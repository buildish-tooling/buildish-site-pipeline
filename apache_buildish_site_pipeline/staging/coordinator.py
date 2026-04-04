# Copyright 2026 The Apache Software Foundation

"""Serial first-wave staging coordinator with owned-unit boundaries."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from apache_buildish_site_pipeline.cli_errors import RetainedStageError
from apache_buildish_site_pipeline.models import ProviderSnapshotV1
from apache_buildish_site_pipeline.models.enums import RecordKind
from apache_buildish_site_pipeline.models.planning_stage_contract import PipelineDiagnosticEntry, StageCommand, StageManifestV1
from apache_buildish_site_pipeline.planning.types import ResolvedComponentConfig, SelectedVersionContext

from .front_matter import build_component_front_matter, build_version_context
from .manifest_builder import build_stage_manifest
from .ownership import OwnedContextInput, OwnedUnit, OwnedUnitKind, build_owned_units
from .publication import StagePublicationResult, finalize_stage_publication, validate_visible_stage_target_path
from .publication_paths import public_path_for_context
from .types import BuildRequest, BuildRunOutcome, EffectiveBuildPlan, StageDestination, WorkRootLayout
from .units import run_component_unit, run_site_assets_unit, run_site_pages_unit, run_vendor_assets_unit
from .worker_protocol import (
    ComponentContextWire,
    LocalizationWire,
    PagePublicationWire,
    WorkerResultWire,
    WorkerSpecWire,
    WorkerStageMetaWire,
)
from .workdirs import create_work_root_layout, prepare_next_stage_root, remove_work_root


def run_build(request: BuildRequest) -> BuildRunOutcome:
    """Materialize one private next-stage tree from one effective build plan."""

    stage_root = prepare_next_stage_root(request.destination.stage_root)
    layout = create_work_root_layout(next_stage_root=stage_root)
    try:
        worker_results = _run_owned_units(request=request, layout=layout)
        manifest = build_stage_manifest(
            layout=layout,
            command=request.command,
            build_plan=request.build_plan,
            diagnostics=request.diagnostics,
            provider_snapshot=request.provider_snapshot,
            worker_results=worker_results,
        )
        return BuildRunOutcome(
            command=request.command,
            layout=layout,
            manifest=manifest,
            worker_count=request.operator_policy.normalized_pool_size(),
        )
    except Exception:
        remove_work_root(layout)
        raise


def materialize_stage_tree(
    *,
    build_plan: EffectiveBuildPlan,
    diagnostics: tuple[PipelineDiagnosticEntry, ...],
    provider_snapshot: ProviderSnapshotV1,
    stage_root: Path,
    command: StageCommand = StageCommand.BUILD,
) -> StageManifestV1:
    """Materialize one private stage tree directly into the provided stage root."""

    outcome = run_build(
        BuildRequest(
            command=command,
            build_plan=build_plan,
            diagnostics=diagnostics,
            provider_snapshot=provider_snapshot,
            destination=StageDestination(stage_root=stage_root),
        ),
    )
    cleanup_after_publication(outcome)
    return outcome.manifest


def publish_stage(
    *,
    build_plan: EffectiveBuildPlan,
    diagnostics: tuple[PipelineDiagnosticEntry, ...],
    provider_snapshot: ProviderSnapshotV1,
    stage_root: Path,
    assembly_root: Path | None = None,
    allow_replace_existing: bool = False,
    command: StageCommand = StageCommand.BUILD,
) -> StagePublicationResult:
    """Build one stage tree privately and then publish it atomically."""

    validate_visible_stage_target_path(stage_root)
    normalized_stage_root = stage_root.resolve(strict=False)
    parent_path = normalized_stage_root.parent
    parent_path.mkdir(parents=True, exist_ok=True)
    temp_root = (
        assembly_root.resolve(strict=False)
        if assembly_root is not None
        else Path(tempfile.mkdtemp(prefix=".stage-build.", dir=parent_path))
    )
    try:
        outcome = run_build(
            BuildRequest(
                command=command,
                build_plan=build_plan,
                diagnostics=diagnostics,
                provider_snapshot=provider_snapshot,
                destination=StageDestination(stage_root=temp_root),
            ),
        )
        publication = finalize_stage_publication(
            candidate_stage_root=outcome.layout.next_stage_root,
            stage_root=normalized_stage_root,
            allow_replace_existing=allow_replace_existing,
        )
        cleanup_after_publication(outcome)
        return publication
    except Exception as error:
        if assembly_root is not None:
            raise RetainedStageError(f"Retained failed stage assembly root for inspection: {temp_root}") from error
        shutil.rmtree(temp_root, ignore_errors=True)
        raise


def _run_owned_units(*, request: BuildRequest, layout: WorkRootLayout) -> tuple[WorkerResultWire, ...]:
    units = build_owned_units(request.build_plan)
    results: list[WorkerResultWire] = []
    for unit in units:
        spec = _worker_spec_for_unit(unit=unit, request=request, layout=layout)
        if unit.kind is OwnedUnitKind.SITE_PAGES:
            results.append(run_site_pages_unit(spec))
        elif unit.kind is OwnedUnitKind.SITE_ASSETS:
            results.append(run_site_assets_unit(spec))
        elif unit.kind is OwnedUnitKind.VENDOR_ASSETS:
            results.append(run_vendor_assets_unit(spec))
        else:
            results.append(run_component_unit(spec))
    return tuple(results)


def _worker_spec_for_unit(*, unit: OwnedUnit, request: BuildRequest, layout: WorkRootLayout) -> WorkerSpecWire:
    stage_meta = WorkerStageMetaWire(
        content_roots=tuple(str(layout.next_stage_root / root) for root in unit.content_stage_roots),
        static_roots=tuple(str(layout.next_stage_root / root) for root in unit.static_stage_roots),
    )
    fragment_path = str(layout.fragments_root / f"{unit.unit_id.replace(':', '_')}.json")
    if unit.kind is OwnedUnitKind.SITE_PAGES:
        return WorkerSpecWire(
            unit_id=unit.unit_id,
            unit_kind=unit.kind.value,
            owner_id=unit.owner_id,
            workspace_root=str(request.build_plan.workspace_root),
            fragment_path=fragment_path,
            site_pages_source=str(unit.site_pages_source),
            stage_meta=stage_meta,
        )
    if unit.kind is OwnedUnitKind.SITE_ASSETS:
        return WorkerSpecWire(
            unit_id=unit.unit_id,
            unit_kind=unit.kind.value,
            owner_id=unit.owner_id,
            workspace_root=str(request.build_plan.workspace_root),
            fragment_path=fragment_path,
            site_assets_source=str(unit.site_assets_source),
            stage_meta=stage_meta,
        )
    if unit.kind is OwnedUnitKind.VENDOR_ASSETS:
        return WorkerSpecWire(
            unit_id=unit.unit_id,
            unit_kind=unit.kind.value,
            owner_id=unit.owner_id,
            workspace_root=str(request.build_plan.workspace_root),
            fragment_path=fragment_path,
            vendor_assets=tuple(
                {"key": asset.key, "source_path": str(asset.source_path)}
                for asset in unit.vendor_assets
            ),
            stage_meta=stage_meta,
        )

    component = next(component for component in request.build_plan.site.components if component.slug == unit.component_slug)
    component_front_matter = build_component_front_matter(
        component,
        tuple(context.context for context in unit.contexts),
    ).model_dump(mode="json", by_alias=True, exclude_none=True)
    localization = None
    if component.localization is not None:
        localization = LocalizationWire(
            default_locale=component.localization.default_locale,
            supported_locales=tuple(component.localization.supported_locales or ()),
            route_mode=component.localization.route_mode.value if component.localization.route_mode is not None else None,
        )
    component_publication = PagePublicationWire(
        path=component.publication.component_path,
        url=component.publication.component_url,
        component_path=component.publication.component_path,
        component_url=component.publication.component_url,
        origin_key=component.publication.origin.key,
    )
    return WorkerSpecWire(
        unit_id=unit.unit_id,
        unit_kind=unit.kind.value,
        owner_id=unit.owner_id,
        workspace_root=str(request.build_plan.workspace_root),
        fragment_path=fragment_path,
        component_slug=component.slug,
        component_pages_source=str(unit.component_pages_source) if unit.component_pages_source is not None else None,
        component_pages_stage_root=str(layout.next_stage_root / "content" / "components" / component.slug / "pages"),
        component_assets_source=str(unit.component_assets_source) if unit.component_assets_source is not None else None,
        component_assets_stage_root=str(layout.next_stage_root / "static" / "components" / component.slug / "assets"),
        component_front_matter=component_front_matter,
        component_publication=component_publication,
        localization=localization,
        contexts=tuple(_context_wire(component=component, owned_context=context, layout=layout) for context in unit.contexts),
        stage_meta=stage_meta,
    )


def _context_wire(
    *,
    component: ResolvedComponentConfig,
    owned_context: OwnedContextInput,
    layout: WorkRootLayout,
) -> ComponentContextWire:
    context = owned_context.context
    publication = component.publication
    public_path = public_path_for_context(publication=publication, context=context)
    public_url = f"{publication.origin.base_url.rstrip('/')}{public_path}"
    version_context = build_version_context(component, context).model_dump(mode="json", by_alias=True, exclude_none=True)
    version_context["provider"] = {
        "key": context.provider_record.provider if context.provider_record is not None else None,
        "externalId": context.provider_record.external_id if context.provider_record is not None else None,
        "externalUrl": context.provider_record.external_url if context.provider_record is not None else None,
    }
    page_kind = "docs-page"
    section = "docs"
    if context.kind is RecordKind.DEVELOPMENT:
        page_kind = "development-page"
        section = "development"
    elif context.kind is RecordKind.RELEASED:
        page_kind = "release-page"
        section = "release"
    elif context.kind is RecordKind.CANDIDATE:
        page_kind = "candidate-page"
        section = "candidate"
    elif context.kind is RecordKind.LINE_HEAD:
        page_kind = "line-head-page"
        section = "line-head"
    elif context.kind is RecordKind.NAMED_REF:
        page_kind = "ref-page"
        section = "ref"
    docs_root = _source_root_for_context(context.docs_root, context)
    assets_root = _source_root_for_context(context.assets_root, context)
    return ComponentContextWire(
        context_id=owned_context.context_id,
        artifact_key=context.artifact_key,
        source_docs_root=str(docs_root) if docs_root is not None else None,
        source_assets_root=str(assets_root) if assets_root is not None else None,
        content_stage_root=str(layout.next_stage_root / owned_context.content_stage_root),
        static_stage_root=str(layout.next_stage_root / owned_context.static_stage_root),
        publication=PagePublicationWire(
            path=public_path,
            url=public_url,
            component_path=component.publication.component_path,
            component_url=component.publication.component_url,
            origin_key=component.publication.origin.key,
        ),
        version_context=version_context,
        page_kind=page_kind,
        section=section,
        record_kind=context.kind.value,
        version_ref=context.ref,
        version=context.version,
    )


def _source_root_for_context(root: Path | None, context: SelectedVersionContext) -> Path | None:
    if root is None:
        return None
    if context.kind is RecordKind.RELEASED and context.version is not None:
        return root / "releases" / context.version
    if context.kind is RecordKind.CANDIDATE and context.version is not None:
        return root / "candidates" / context.version
    if context.kind is RecordKind.LINE_HEAD and context.release_line is not None:
        return root / "maintenance" / context.release_line
    if context.kind is RecordKind.NAMED_REF and context.named_ref_key is not None:
        return root / "refs" / context.named_ref_key
    return root


def cleanup_after_publication(outcome: BuildRunOutcome) -> None:
    """Remove private work roots once callers no longer need them."""

    remove_work_root(outcome.layout)