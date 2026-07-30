# Copyright 2026 The Buildish Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Shared page inventory builder and low-level authored-page validations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from buildish_site_pipeline.models.authored.page_metadata import (
    PageTranslationMetadata,
)
from buildish_site_pipeline.models.enums import (
    DiagnosticSeverity,
    MaterializationInputKind,
    MaterializationStatus,
)
from buildish_site_pipeline.models.loading import LoadingError, load_yaml_mapping
from buildish_site_pipeline.page_support import is_supported_page_path
from buildish_site_pipeline.planning.types import (
    LocalInputIdentity,
    PlanningEvaluation,
    ResolvedLocalInput,
    ResolvedLocalizationPolicy,
    SelectedVersionContext,
)
from buildish_site_pipeline.staging.front_matter import detect_locale
from buildish_site_pipeline.staging.publication_paths import public_path_for_context

from . import diagnostic_codes
from .collector import DiagnosticCollector
from .link_references import extract_link_references
from .types import InventoryPage, PageInventory

_PAGE_INPUT_KINDS = {
    MaterializationInputKind.SITE_PAGES,
    MaterializationInputKind.DEVELOPMENT,
    MaterializationInputKind.LINE_HEAD,
    MaterializationInputKind.RELEASED,
    MaterializationInputKind.CANDIDATE,
    MaterializationInputKind.NAMED_REF,
}


@dataclass(frozen=True, slots=True)
class _PageRootContext:
    root: Path
    input_id: str
    component_slug: str | None
    artifact_key: str | None
    base_public_path: str
    localization: ResolvedLocalizationPolicy | None


def validate_page_scan(
    planning: PlanningEvaluation, collector: DiagnosticCollector
) -> PageInventory:
    """Build the shared page inventory and emit basic authored-page diagnostics."""

    pages: list[InventoryPage] = []
    for context in _page_root_contexts(planning):
        pages.extend(_scan_page_root(context=context, collector=collector))
    return PageInventory(pages=tuple(pages))


def _page_root_contexts(planning: PlanningEvaluation) -> tuple[_PageRootContext, ...]:
    site = getattr(planning, "site", None)
    components = getattr(site, "components", ()) if site is not None else ()
    components_by_slug = {component.slug: component for component in components}
    contexts: list[_PageRootContext] = []
    for local_input in planning.local_inputs:
        if local_input.readiness.status is not MaterializationStatus.PRESENT:
            continue
        if local_input.identity.input_kind not in _PAGE_INPUT_KINDS:
            continue
        if local_input.identity.input_kind is MaterializationInputKind.SITE_PAGES:
            contexts.append(
                _PageRootContext(
                    root=local_input.expected_local_path,
                    input_id=_format_input_id(local_input.identity),
                    component_slug=None,
                    artifact_key=None,
                    base_public_path="/",
                    localization=None,
                )
            )
            continue
        selected_context = _selected_context_for_input(planning, local_input)
        component = components_by_slug.get(local_input.identity.component_slug)
        if selected_context is None:
            contexts.append(
                _PageRootContext(
                    root=local_input.expected_local_path,
                    input_id=_format_input_id(local_input.identity),
                    component_slug=local_input.identity.component_slug,
                    artifact_key=local_input.identity.artifact_key,
                    base_public_path=(
                        component.publication.component_path if component is not None else "/"
                    ),
                    localization=(component.localization if component is not None else None),
                )
            )
            continue
        contexts.append(
            _PageRootContext(
                root=local_input.expected_local_path,
                input_id=_format_input_id(local_input.identity),
                component_slug=selected_context.component_slug,
                artifact_key=selected_context.artifact_key,
                base_public_path=public_path_for_context(
                    components_by_slug[selected_context.component_slug].publication,
                    selected_context,
                ),
                localization=components_by_slug[selected_context.component_slug].localization,
            )
        )

    for component in components:
        if component.pages_root is None:
            continue
        contexts.append(
            _PageRootContext(
                root=component.pages_root,
                input_id=f"componentPages:{component.slug}",
                component_slug=component.slug,
                artifact_key=None,
                base_public_path=component.publication.component_path,
                localization=component.localization,
            )
        )
    return tuple(contexts)


def _scan_page_root(
    *, context: _PageRootContext, collector: DiagnosticCollector
) -> list[InventoryPage]:
    root_real = context.root.resolve(strict=False)
    pages: list[InventoryPage] = []
    seen_dirs: set[Path] = set()
    stack = [context.root]

    while stack:
        directory = stack.pop()
        directory_real = directory.resolve(strict=False)
        if directory_real in seen_dirs:
            continue
        seen_dirs.add(directory_real)
        try:
            entries = sorted(directory.iterdir(), key=lambda entry: entry.name)
        except OSError as exc:
            _add_scan_failure(context=context, collector=collector, reason=str(exc))
            continue
        for entry in entries:
            entry_real = entry.resolve(strict=False)
            relative_path = entry.relative_to(context.root).as_posix()
            if not entry_real.is_relative_to(root_real):
                collector.add(
                    severity=DiagnosticSeverity.ERROR,
                    code=diagnostic_codes.PAGE_PATH_OUTSIDE_ROOT,
                    message=(
                        f"Scanned page path {relative_path} for {context.input_id} resolves outside the declared source root"
                    ),
                    component_slug=context.component_slug,
                    artifact_key=context.artifact_key,
                    details={"inputId": context.input_id, "path": relative_path},
                )
                continue
            if entry.is_dir():
                stack.append(entry)
                continue
            if not is_supported_page_path(entry):
                continue
            pages.append(_scan_page_file(entry=entry, context=context, collector=collector))
    return pages


def _scan_page_file(
    *, entry: Path, context: _PageRootContext, collector: DiagnosticCollector
) -> InventoryPage:
    relative_path = entry.relative_to(context.root).as_posix()
    translation_key: str | None = None
    try:
        text = entry.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        collector.add(
            severity=DiagnosticSeverity.ERROR,
            code=diagnostic_codes.PAGE_READ_FAILED,
            message=f"Could not read page content {relative_path} for {context.input_id}",
            component_slug=context.component_slug,
            artifact_key=context.artifact_key,
            details={"inputId": context.input_id, "path": relative_path, "reason": str(exc)},
        )
        return _page_record(
            context=context,
            entry=entry,
            relative_path=relative_path,
            translation_key=None,
            extracted_links=(),
        )

    front_matter, body_text, source_line_offset = _extract_front_matter(
        text=text,
        relative_path=relative_path,
        context=context,
        collector=collector,
    )
    if front_matter is not None:
        if "pipeline" in front_matter:
            collector.add(
                severity=DiagnosticSeverity.ERROR,
                code=diagnostic_codes.PAGE_RESERVED_NAMESPACE,
                message=f"Page front matter for {relative_path} in {context.input_id} uses the reserved pipeline namespace",
                component_slug=context.component_slug,
                artifact_key=context.artifact_key,
                details={"inputId": context.input_id, "path": relative_path, "field": "pipeline"},
            )
        if "translationKey" in front_matter:
            try:
                translation = PageTranslationMetadata.model_validate(
                    {"translationKey": front_matter["translationKey"]},
                    by_alias=True,
                    by_name=False,
                )
            except Exception as exc:  # pragma: no cover
                collector.add(
                    severity=DiagnosticSeverity.ERROR,
                    code=diagnostic_codes.PAGE_FRONT_MATTER_INVALID,
                    message=f"Page front matter for {relative_path} in {context.input_id} is invalid",
                    component_slug=context.component_slug,
                    artifact_key=context.artifact_key,
                    details={"inputId": context.input_id, "path": relative_path, "reason": str(exc)},
                )
            else:
                translation_key = translation.translation_key
    extracted_links = (
        extract_link_references(
            source_path=entry,
            text=body_text,
            source_line_offset=source_line_offset,
        )
        if body_text is not None
        else ()
    )
    return _page_record(
        context=context,
        entry=entry,
        relative_path=relative_path,
        translation_key=translation_key,
        extracted_links=extracted_links,
    )


def _extract_front_matter(
    *, text: str, relative_path: str, context: _PageRootContext, collector: DiagnosticCollector
) -> tuple[dict[str, object] | None, str | None, int]:
    if not text.startswith("---\n"):
        return None, text, 0
    end_marker = text.find("\n---\n", 4)
    if end_marker == -1:
        end_marker = text.find("\n...\n", 4)
    if end_marker == -1:
        collector.add(
            severity=DiagnosticSeverity.ERROR,
            code=diagnostic_codes.PAGE_FRONT_MATTER_INVALID,
            message=f"Page front matter for {relative_path} in {context.input_id} is not terminated",
            component_slug=context.component_slug,
            artifact_key=context.artifact_key,
            details={"inputId": context.input_id, "path": relative_path},
        )
        return None, None, 0
    raw_front_matter = text[4:end_marker]
    body_text = text[end_marker + 5 :]
    source_line_offset = text[: end_marker + 5].count("\n")
    if raw_front_matter.strip() == "":
        return {}, body_text, source_line_offset
    try:
        return dict(load_yaml_mapping(raw_front_matter)), body_text, source_line_offset
    except LoadingError as exc:
        collector.add(
            severity=DiagnosticSeverity.ERROR,
            code=diagnostic_codes.PAGE_FRONT_MATTER_INVALID,
            message=f"Page front matter for {relative_path} in {context.input_id} is malformed",
            component_slug=context.component_slug,
            artifact_key=context.artifact_key,
            details={"inputId": context.input_id, "path": relative_path, "reason": str(exc)},
        )
        return None, body_text, source_line_offset


def _page_record(
    *,
    context: _PageRootContext,
    entry: Path,
    relative_path: str,
    translation_key: str | None,
    extracted_links,
) -> InventoryPage:
    _, _, routed_relative_path = detect_locale(Path(relative_path), context.localization)
    return InventoryPage(
        input_id=context.input_id,
        component_slug=context.component_slug,
        artifact_key=context.artifact_key,
        relative_path=relative_path,
        routed_relative_path=routed_relative_path.as_posix(),
        source_path=entry,
        base_public_path=context.base_public_path,
        translation_key=translation_key,
        extracted_links=tuple(extracted_links),
    )


def _selected_context_for_input(
    planning: PlanningEvaluation, local_input: ResolvedLocalInput
) -> SelectedVersionContext | None:
    identity = local_input.identity
    selected_versions = getattr(planning, "selected_versions", None)
    contexts = getattr(selected_versions, "contexts", ()) if selected_versions else ()
    for context in contexts:
        if _matches_input_context(identity, context):
            return context
    return None


def _matches_input_context(
    identity: LocalInputIdentity, context: SelectedVersionContext
) -> bool:
    return (
        identity.input_kind is context.input_kind
        and identity.component_slug == context.component_slug
        and identity.artifact_key == context.artifact_key
        and identity.release_line == context.release_line
        and identity.version == context.version
        and identity.ref == context.ref
        and identity.tag == context.tag
        and identity.commit_sha == context.commit_sha
    )


def _add_scan_failure(
    *, context: _PageRootContext, collector: DiagnosticCollector, reason: str
) -> None:
    collector.add(
        severity=DiagnosticSeverity.ERROR,
        code=diagnostic_codes.PAGE_READ_FAILED,
        message=f"Could not scan page input {context.input_id}",
        component_slug=context.component_slug,
        artifact_key=context.artifact_key,
        details={"inputId": context.input_id, "reason": reason},
    )


def _format_input_id(identity: LocalInputIdentity) -> str:
    parts = [identity.input_kind.value]
    if identity.component_slug is not None:
        parts.append(identity.component_slug)
    if identity.artifact_key is not None:
        parts.append(identity.artifact_key)
    if identity.release_line is not None:
        parts.append(identity.release_line)
    if identity.version is not None:
        parts.append(identity.version)
    if identity.ref is not None:
        parts.append(identity.ref)
    return ":".join(parts)