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

"""Build worker-facing staging wires so the coordinator stays orchestration-focused."""

from __future__ import annotations

from pathlib import Path
from typing import assert_never

from apache_buildish_site_pipeline.models.enums import RecordKind
from apache_buildish_site_pipeline.planning.types import (
    ResolvedComponentConfig,
    SelectedVersionContext,
)

from .front_matter import build_component_front_matter, build_version_context
from .ownership import OwnedContextInput, OwnedUnit, OwnedUnitKind
from .publication_paths import public_path_for_context, stage_root_for_public_path
from .worker_protocol import (
    ComponentContextWire,
    LocalizationWire,
    PagePublicationWire,
    WorkerSpecWire,
    WorkerStageMetaWire,
)
from .types import WorkRootLayout
from .workdirs import RunWorkspace


def build_worker_spec_for_unit(
    *,
    unit: OwnedUnit,
    workspace_root: Path,
    site_components: tuple[ResolvedComponentConfig, ...],
    run_workspace: RunWorkspace,
) -> WorkerSpecWire:
    """Translate one owned unit into the exact worker wire payload it needs."""

    unit_workspace = run_workspace.workspace_for_unit(unit)
    stage_meta = WorkerStageMetaWire(
        content_roots=tuple(str(root) for root in unit_workspace.content_roots),
        static_roots=tuple(str(root) for root in unit_workspace.static_roots),
    )
    if unit.kind is OwnedUnitKind.SITE_PAGES:
        return WorkerSpecWire(
            unit_id=unit.unit_id,
            unit_kind=unit.kind.value,
            owner_id=unit.owner_id,
            workspace_root=str(workspace_root),
            unit_root=str(unit_workspace.unit_root),
            fragment_path=str(unit_workspace.fragment_path),
            site_pages_source=str(unit.site_pages_source),
            stage_meta=stage_meta,
        )
    if unit.kind is OwnedUnitKind.SITE_ASSETS:
        return WorkerSpecWire(
            unit_id=unit.unit_id,
            unit_kind=unit.kind.value,
            owner_id=unit.owner_id,
            workspace_root=str(workspace_root),
            unit_root=str(unit_workspace.unit_root),
            fragment_path=str(unit_workspace.fragment_path),
            site_assets_source=str(unit.site_assets_source),
            stage_meta=stage_meta,
        )
    if unit.kind is OwnedUnitKind.VENDOR_ASSETS:
        return WorkerSpecWire(
            unit_id=unit.unit_id,
            unit_kind=unit.kind.value,
            owner_id=unit.owner_id,
            workspace_root=str(workspace_root),
            unit_root=str(unit_workspace.unit_root),
            fragment_path=str(unit_workspace.fragment_path),
            vendor_assets=tuple(
                {"key": asset.key, "source_path": str(asset.source_path)}
                for asset in unit.vendor_assets
            ),
            stage_meta=stage_meta,
        )

    component = next(
        component for component in site_components if component.slug == unit.component_slug
    )
    component_front_matter = build_component_front_matter(
        component,
        tuple(context.context for context in unit.contexts),
    ).model_dump(mode="json", by_alias=True, exclude_none=True)
    return WorkerSpecWire(
        unit_id=unit.unit_id,
        unit_kind=unit.kind.value,
        owner_id=unit.owner_id,
        workspace_root=str(workspace_root),
        unit_root=str(unit_workspace.unit_root),
        fragment_path=str(unit_workspace.fragment_path),
        component_slug=component.slug,
        component_pages_source=str(unit.component_pages_source)
        if unit.component_pages_source is not None
        else None,
        component_pages_stage_root=str(
            run_workspace.layout.next_stage_root
            / stage_root_for_public_path("content", component.publication.component_path)
        ),
        component_assets_source=str(unit.component_assets_source)
        if unit.component_assets_source is not None
        else None,
        component_assets_stage_root=str(
            run_workspace.layout.next_stage_root
            / stage_root_for_public_path("static", component.publication.assets_path)
        ),
        component_front_matter=component_front_matter,
        component_publication=PagePublicationWire(
            path=component.publication.component_path,
            url=component.publication.component_url,
            component_path=component.publication.component_path,
            component_url=component.publication.component_url,
            origin_key=component.publication.origin.key,
        ),
        localization=_localization_wire(component),
        contexts=tuple(
            build_context_wire(
                component=component,
                owned_context=context,
                layout=run_workspace.layout,
            )
            for context in unit.contexts
        ),
        stage_meta=stage_meta,
    )


def build_context_wire(
    *,
    component: ResolvedComponentConfig,
    owned_context: OwnedContextInput,
    layout: WorkRootLayout,
) -> ComponentContextWire:
    """Translate one version context into the worker-facing publication wire."""

    context = owned_context.context
    publication = component.publication
    public_path = public_path_for_context(publication=publication, context=context)
    public_url = f"{publication.origin.base_url.rstrip('/')}{public_path}"
    version_context = build_version_context(component, context).model_dump(
        mode="json", by_alias=True, exclude_none=True
    )
    version_context["provider"] = {
        "key": context.provider_record.provider
        if context.provider_record is not None
        else None,
        "externalId": context.provider_record.external_id
        if context.provider_record is not None
        else None,
        "externalUrl": context.provider_record.external_url
        if context.provider_record is not None
        else None,
    }
    page_kind, section = _page_descriptor_for_kind(context.kind)
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


def _localization_wire(component: ResolvedComponentConfig) -> LocalizationWire:
    return LocalizationWire(
        default_locale=component.localization.default_locale,
        supported_locales=tuple(component.localization.supported_locales or ()),
        route_mode=component.localization.route_mode,
    )


def _page_descriptor_for_kind(kind: RecordKind) -> tuple[str, str]:
    if kind is RecordKind.DEVELOPMENT:
        return "development-page", "development"
    if kind is RecordKind.RELEASED:
        return "release-page", "release"
    if kind is RecordKind.CANDIDATE:
        return "candidate-page", "candidate"
    if kind is RecordKind.LINE_HEAD:
        return "line-head-page", "line-head"
    if kind is RecordKind.NAMED_REF:
        return "ref-page", "ref"
    assert_never(kind)


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