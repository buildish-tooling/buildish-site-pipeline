# Copyright 2026 The Apache Software Foundation
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

"""Read-only page scan validations for selected content roots."""

from __future__ import annotations

from pathlib import Path

from apache_buildish_site_pipeline.models.enums import (
    DiagnosticSeverity,
    MaterializationInputKind,
    MaterializationStatus,
)
from apache_buildish_site_pipeline.page_support import is_supported_page_path
from apache_buildish_site_pipeline.models.loading import LoadingError, load_yaml_mapping
from apache_buildish_site_pipeline.models.authored.page_metadata import (
    PageTranslationMetadata,
)
from apache_buildish_site_pipeline.planning.types import (
    LocalInputIdentity,
    PlanningEvaluation,
    ResolvedLocalInput,
)

from . import diagnostic_codes
from .collector import DiagnosticCollector
from .types import PageScanResult, ScannedPage

_PAGE_INPUT_KINDS = {
    MaterializationInputKind.SITE_PAGES,
    MaterializationInputKind.DEVELOPMENT,
    MaterializationInputKind.LINE_HEAD,
    MaterializationInputKind.RELEASED,
    MaterializationInputKind.CANDIDATE,
    MaterializationInputKind.NAMED_REF,
}


def validate_page_scan(
    planning: PlanningEvaluation, collector: DiagnosticCollector
) -> PageScanResult:
    """Scan selected page inputs for malformed front matter and rooted-path escapes."""

    pages: list[ScannedPage] = []
    for local_input in planning.local_inputs:
        if local_input.readiness.status is not MaterializationStatus.PRESENT:
            continue
        if local_input.identity.input_kind not in _PAGE_INPUT_KINDS:
            continue
        pages.extend(_scan_local_input(local_input=local_input, collector=collector))
    return PageScanResult(pages=tuple(pages))


def _scan_local_input(
    *, local_input: ResolvedLocalInput, collector: DiagnosticCollector
) -> list[ScannedPage]:
    root = local_input.expected_local_path
    root_real = root.resolve(strict=False)
    input_id = _format_input_id(local_input.identity)
    pages: list[ScannedPage] = []
    seen_dirs: set[Path] = set()
    stack = [root]

    while stack:
        directory = stack.pop()
        directory_real = directory.resolve(strict=False)
        if directory_real in seen_dirs:
            continue
        seen_dirs.add(directory_real)
        try:
            entries = sorted(directory.iterdir(), key=lambda entry: entry.name)
        except OSError as exc:
            collector.add(
                severity=DiagnosticSeverity.ERROR,
                code=diagnostic_codes.PAGE_READ_FAILED,
                message=f"Could not scan page input {input_id}",
                component_slug=local_input.identity.component_slug,
                artifact_key=local_input.identity.artifact_key,
                details={"inputId": input_id, "reason": str(exc)},
            )
            continue
        for entry in entries:
            entry_real = entry.resolve(strict=False)
            relative_path = entry.relative_to(root).as_posix()
            if not entry_real.is_relative_to(root_real):
                collector.add(
                    severity=DiagnosticSeverity.ERROR,
                    code=diagnostic_codes.PAGE_PATH_OUTSIDE_ROOT,
                    message=(
                        f"Scanned page path {relative_path} for {input_id} resolves outside the declared source root"
                    ),
                    component_slug=local_input.identity.component_slug,
                    artifact_key=local_input.identity.artifact_key,
                    details={"inputId": input_id, "path": relative_path},
                )
                continue
            if entry.is_dir():
                stack.append(entry)
                continue
            if not is_supported_page_path(entry):
                continue
            pages.append(
                _scan_page_file(
                    entry=entry,
                    local_input=local_input,
                    input_id=input_id,
                    collector=collector,
                ),
            )
    return pages


def _scan_page_file(
    *,
    entry: Path,
    local_input: ResolvedLocalInput,
    input_id: str,
    collector: DiagnosticCollector,
) -> ScannedPage:
    relative_path = entry.relative_to(local_input.expected_local_path).as_posix()
    translation_key: str | None = None
    try:
        text = entry.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        collector.add(
            severity=DiagnosticSeverity.ERROR,
            code=diagnostic_codes.PAGE_READ_FAILED,
            message=f"Could not read page content {relative_path} for {input_id}",
            component_slug=local_input.identity.component_slug,
            artifact_key=local_input.identity.artifact_key,
            details={"inputId": input_id, "path": relative_path, "reason": str(exc)},
        )
        return _page_record(
            local_input=local_input, input_id=input_id, relative_path=relative_path
        )
    front_matter = _extract_front_matter(
        text=text,
        relative_path=relative_path,
        local_input=local_input,
        input_id=input_id,
        collector=collector,
    )
    if front_matter is not None:
        if "pipeline" in front_matter:
            collector.add(
                severity=DiagnosticSeverity.ERROR,
                code=diagnostic_codes.PAGE_RESERVED_NAMESPACE,
                message=f"Page front matter for {relative_path} in {input_id} uses the reserved pipeline namespace",
                component_slug=local_input.identity.component_slug,
                artifact_key=local_input.identity.artifact_key,
                details={
                    "inputId": input_id,
                    "path": relative_path,
                    "field": "pipeline",
                },
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
                    message=f"Page front matter for {relative_path} in {input_id} is invalid",
                    component_slug=local_input.identity.component_slug,
                    artifact_key=local_input.identity.artifact_key,
                    details={
                        "inputId": input_id,
                        "path": relative_path,
                        "reason": str(exc),
                    },
                )
            else:
                translation_key = translation.translation_key
    return _page_record(
        local_input=local_input,
        input_id=input_id,
        relative_path=relative_path,
        translation_key=translation_key,
    )


def _extract_front_matter(
    *,
    text: str,
    relative_path: str,
    local_input: ResolvedLocalInput,
    input_id: str,
    collector: DiagnosticCollector,
) -> dict[str, object] | None:
    if not text.startswith("---\n"):
        return None
    end_marker = text.find("\n---\n", 4)
    if end_marker == -1:
        end_marker = text.find("\n...\n", 4)
    if end_marker == -1:
        collector.add(
            severity=DiagnosticSeverity.ERROR,
            code=diagnostic_codes.PAGE_FRONT_MATTER_INVALID,
            message=f"Page front matter for {relative_path} in {input_id} is not terminated",
            component_slug=local_input.identity.component_slug,
            artifact_key=local_input.identity.artifact_key,
            details={"inputId": input_id, "path": relative_path},
        )
        return None
    raw_front_matter = text[4:end_marker]
    if raw_front_matter.strip() == "":
        return {}
    try:
        return dict(load_yaml_mapping(raw_front_matter))
    except LoadingError as exc:
        collector.add(
            severity=DiagnosticSeverity.ERROR,
            code=diagnostic_codes.PAGE_FRONT_MATTER_INVALID,
            message=f"Page front matter for {relative_path} in {input_id} is malformed",
            component_slug=local_input.identity.component_slug,
            artifact_key=local_input.identity.artifact_key,
            details={"inputId": input_id, "path": relative_path, "reason": str(exc)},
        )
        return None


def _page_record(
    *,
    local_input: ResolvedLocalInput,
    input_id: str,
    relative_path: str,
    translation_key: str | None = None,
) -> ScannedPage:
    return ScannedPage(
        input_id=input_id,
        component_slug=local_input.identity.component_slug,
        artifact_key=local_input.identity.artifact_key,
        relative_path=relative_path,
        translation_key=translation_key,
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
