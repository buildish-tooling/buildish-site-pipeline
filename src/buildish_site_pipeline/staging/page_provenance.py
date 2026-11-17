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

"""Associate staged files with coordinator-owned inputs before emitting source links."""

from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from ..cli.errors import StageIntegrityError
from ..models.emitted.staged_front_matter import PageSourceProvenance
from ..models.enums import ContextAction, RecordKind
from ..models.validation.provenance import validate_source_target_path
from ..planning.types import SelectedVersionContext
from ..source_roots import ResolvedSourceBinding
from .ownership import OwnedUnit, OwnedUnitKind, source_root_for_context
from .publication_paths import stage_root_for_public_path
from .types import EffectiveBuildPlan
from .worker_protocol import StagedPageContributionWire


@dataclass(frozen=True, slots=True)
class PageSourceInput:
    """One coordinator-owned source/output association, independent of worker labels."""

    binding: ResolvedSourceBinding
    source_root: Path
    stage_root: Path
    context: SelectedVersionContext | None = None

    @property
    def artifact_key(self) -> str | None:
        return self.context.artifact_key if self.context is not None else None


@dataclass(frozen=True, slots=True)
class UnitPageSources:
    """Provenance candidates for one current owned unit."""

    unit: OwnedUnit
    artifact_keys: frozenset[str]
    inputs: tuple[PageSourceInput, ...]


def build_page_source_index(
    build_plan: EffectiveBuildPlan, units: tuple[OwnedUnit, ...]
) -> dict[str, UnitPageSources]:
    """Build once per finalization; never use retained provenance as authority."""
    components = {component.slug: component for component in build_plan.site.components}
    index: dict[str, UnitPageSources] = {}
    for unit in units:
        if unit.unit_id in index:
            raise StageIntegrityError(f"Duplicate provenance unit: {unit.unit_id}")
        inputs: list[PageSourceInput] = []
        artifact_keys: frozenset[str] = frozenset()
        if unit.kind is OwnedUnitKind.COMPONENT:
            component = components.get(unit.component_slug or "")
            if component is None:
                raise StageIntegrityError(
                    f"Unknown provenance component: {unit.component_slug}"
                )
            artifact_keys = frozenset(artifact.key for artifact in component.artifacts)
            for owned_context in unit.contexts:
                context = owned_context.context
                source_root = source_root_for_context(context.docs_root, context)
                if source_root is not None:
                    inputs.append(
                        PageSourceInput(
                            binding=context.source_binding,
                            source_root=source_root,
                            stage_root=owned_context.content_stage_root,
                            context=context,
                        )
                    )
            if (
                component.pages_root is not None
                and component.content_source is not None
            ):
                inputs.append(
                    PageSourceInput(
                        binding=component.content_source,
                        source_root=component.pages_root,
                        stage_root=stage_root_for_public_path(
                            "content", component.publication.component_path
                        ),
                    )
                )
        index[unit.unit_id] = UnitPageSources(unit, artifact_keys, tuple(inputs))
    return index


def page_source_provenance(
    *,
    build_plan: EffectiveBuildPlan,
    sources: UnitPageSources,
    contribution: StagedPageContributionWire,
) -> PageSourceProvenance | None:
    """Recompute a target only after matching the exact source and destination file."""
    if sources.unit.kind is not OwnedUnitKind.COMPONENT:
        return None
    if contribution.component_slug != sources.unit.component_slug:
        raise StageIntegrityError("Page component does not match its owned unit")
    if (
        contribution.artifact_key is not None
        and contribution.artifact_key not in sources.artifact_keys
    ):
        raise StageIntegrityError(
            "Page references an unknown artifact in its owned unit"
        )
    destination = Path(contribution.stage_relative_path)
    candidates = [
        item
        for item in sources.inputs
        if item.artifact_key == contribution.artifact_key
        and destination.is_relative_to(item.stage_root)
    ]
    if not candidates:
        raise StageIntegrityError(
            "Page destination has no matching owned source context"
        )
    # Generated notices have no authored source, even if a fragment supplies one.
    if any(
        item.context is not None and item.context.action is ContextAction.NOTICE
        for item in candidates
    ):
        return None
    if contribution.source_path is None:
        return None
    raw_source = Path(contribution.source_path)
    if ".." in raw_source.parts or "\\" in contribution.source_path:
        return None
    source = (
        raw_source
        if raw_source.is_absolute()
        else build_plan.workspace_root / raw_source
    )
    matched: list[tuple[PageSourceInput, str]] = []
    contained = False
    for item in candidates:
        suffix = _contained_suffix(source, item.source_root)
        binding_suffix = _contained_suffix(source, item.binding.local_dir)
        if suffix is None or binding_suffix is None:
            continue
        contained = True
        if suffix == destination.relative_to(item.stage_root).as_posix():
            matched.append((item, suffix))
    if not matched:
        if contained:
            raise StageIntegrityError(
                "Page source filename does not match its owned destination"
            )
        return None
    depth = max(len(item.stage_root.parts) for item, _ in matched)
    deepest = [
        (item, suffix)
        for item, suffix in matched
        if len(item.stage_root.parts) == depth
    ]
    if len(deepest) != 1:
        raise StageIntegrityError("Ambiguous page source context for owned destination")
    item, suffix = deepest[0]
    if item.binding.key not in build_plan.site.sources:
        return None
    context = item.context
    mapping = (
        context.provider_record.docs_source
        if context is not None and context.provider_record is not None
        else None
    )
    if mapping is not None:
        target_path = str(PurePosixPath(mapping.root) / suffix)
        try:
            validate_source_target_path(target_path)
        except ValueError:
            return None
        return PageSourceProvenance(
            key=item.binding.key,
            path=target_path,
            repository=mapping.repository,
            view_ref=mapping.ref,
        )
    if context is not None and context.kind is not RecordKind.DEVELOPMENT:
        return None
    path = _contained_suffix(source, item.binding.local_dir)
    if path is None:
        return None
    ref = item.binding.default_branch
    edit_ref = ref
    if context is not None and context.artifact_key is not None:
        ref = context.ref
        edit_ref = (
            ref
            if ref
            and (ref.startswith("refs/heads/") or ref == item.binding.default_branch)
            else None
        )
    if item.binding.repository is None:
        ref = edit_ref = None
    return PageSourceProvenance(
        key=item.binding.key,
        path=path,
        repository=item.binding.repository,
        view_ref=ref,
        edit_ref=edit_ref,
    )


def _contained_suffix(source: Path, root: Path) -> str | None:
    """Check resolved containment while retaining the exact lexical filename."""
    normalized_root = root.resolve(strict=False)
    if not source.resolve(strict=False).is_relative_to(normalized_root):
        return None
    try:
        suffix = source.relative_to(normalized_root).as_posix()
        return validate_source_target_path(suffix)
    except ValueError:
        return None
