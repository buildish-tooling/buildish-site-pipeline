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

"""Planning and input-resolution package."""

from __future__ import annotations

from pathlib import Path

from buildish_site_pipeline.models.authored.site_catalog import (
    SiteCatalogDocumentV1,
)
from buildish_site_pipeline.models.authored.component_metadata import (
    ComponentMetadataDocumentV1,
)
from buildish_site_pipeline.models.enums import PlanningTarget
from buildish_site_pipeline.models.emitted.planning_stage_contract import (
    PipelineDiagnosticEntry,
)
from buildish_site_pipeline.models.provider.provider_snapshot import (
    ProviderSnapshotDocumentV1,
)

from .build_plan import build_effective_build_plan
from .effective_config import resolve_site_config
from .input_inventory import derive_local_inputs
from .provider_index import build_provider_snapshot_index
from .readiness import classify_input_readiness
from .report_builder import build_resolved_materialization_report
from .selection import select_version_contexts
from .types import PlanningEvaluation
from .watch_roots import derive_watch_plan


def evaluate_planning(
    *,
    target: PlanningTarget,
    catalog: SiteCatalogDocumentV1,
    provider_snapshot: ProviderSnapshotDocumentV1,
    workspace_root: Path,
    component_documents: dict[str, ComponentMetadataDocumentV1] | None = None,
    stage_root: Path | None = None,
    work_root: Path | None = None,
    report_output: Path | None = None,
) -> PlanningEvaluation:
    """Run the full planning pass and return the immutable in-memory result."""

    site = resolve_site_config(
        catalog=catalog,
        workspace_root=workspace_root,
        component_documents=component_documents,
    )
    provider_index = build_provider_snapshot_index(
        provider_snapshot=provider_snapshot, site=site
    )
    selected_versions = select_version_contexts(
        site=site, provider_index=provider_index
    )
    local_inputs = derive_local_inputs(site=site, selected_versions=selected_versions)
    ready_inputs = classify_input_readiness(local_inputs)
    watched_inputs, watch_plan = derive_watch_plan(
        target=target,
        workspace_root=workspace_root,
        local_inputs=ready_inputs,
        stage_root=stage_root,
        work_root=work_root,
        report_output=report_output,
    )
    diagnostics: tuple[PipelineDiagnosticEntry, ...] = ()
    build_plan_result = build_effective_build_plan(
        target=target,
        site=site,
        selected_versions=selected_versions,
        local_inputs=watched_inputs,
        watch_plan=watch_plan,
    )
    return PlanningEvaluation(
        target=target,
        site=site,
        provider_index=provider_index,
        selected_versions=selected_versions,
        local_inputs=watched_inputs,
        watch_plan=watch_plan,
        build_plan_result=build_plan_result,
        diagnostics=diagnostics,
    )


__all__ = [
    "PlanningEvaluation",
    "build_resolved_materialization_report",
    "evaluate_planning",
]
