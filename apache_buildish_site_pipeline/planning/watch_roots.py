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

"""Watch-eligibility and watch-root derivation."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from apache_buildish_site_pipeline.models.enums import MaterializationInputKind, PlanningTarget
from apache_buildish_site_pipeline.models.enums import DiagnosticSeverity
from apache_buildish_site_pipeline.models.planning_stage_contract import PipelineDiagnosticEntry

from .types import MaterializationStatusReason, ResolvedLocalInput, WatchInputPlan

_MAX_WATCH_ROOTS = 32


def derive_watch_plan(
    *,
    target: PlanningTarget,
    workspace_root: Path,
    local_inputs: tuple[ResolvedLocalInput, ...],
    stage_root: Path | None = None,
    work_root: Path | None = None,
    report_output: Path | None = None,
) -> tuple[tuple[ResolvedLocalInput, ...], WatchInputPlan | None]:
    """Annotate inputs with watch eligibility and derive safe watch roots."""

    normalized_workspace_root = workspace_root.resolve(strict=False)
    protected_paths = tuple(
        path.resolve(strict=False)
        for path in (stage_root, work_root, report_output)
        if path is not None
    )
    updated_inputs = []
    root_candidates: list[Path] = []
    diagnostics: list[PipelineDiagnosticEntry] = []
    for local_input in local_inputs:
        watch_eligible = _is_watch_eligible(local_input, normalized_workspace_root)
        updated_inputs.append(replace(local_input, watch_eligible=watch_eligible if target is PlanningTarget.WATCH else watch_eligible))
        if target is not PlanningTarget.WATCH or not watch_eligible or not local_input.expected_local_path.exists():
            continue
        candidate_root = local_input.expected_local_path.resolve(strict=False)
        if any(_conflicts_with_protected_path(candidate_root, protected_path) for protected_path in protected_paths):
            diagnostics.append(
                PipelineDiagnosticEntry(
                    severity=DiagnosticSeverity.WARNING,
                    code="watch-root-conflict",
                    message=f"Excluded watch root {candidate_root} because it conflicts with an output path",
                    component_slug=local_input.identity.component_slug,
                    artifact_key=local_input.identity.artifact_key,
                    details={"reason": MaterializationStatusReason.WATCH_ROOT_CONFLICT},
                )
            )
            continue
        root_candidates.append(candidate_root)

    distinct_roots = tuple(sorted(set(root_candidates)))
    if len(distinct_roots) > _MAX_WATCH_ROOTS:
        raise ValueError("Planning derived more than the 32 watch-root ceiling")
    watch_plan = WatchInputPlan(roots=distinct_roots, diagnostics=tuple(diagnostics)) if target is PlanningTarget.WATCH else None
    return tuple(updated_inputs), watch_plan


def _is_watch_eligible(local_input: ResolvedLocalInput, workspace_root: Path) -> bool:
    if local_input.identity.input_kind in {MaterializationInputKind.RELEASED, MaterializationInputKind.CANDIDATE}:
        return False
    return local_input.expected_local_path.resolve(strict=False).is_relative_to(workspace_root)


def _conflicts_with_protected_path(candidate_root: Path, protected_path: Path) -> bool:
    return candidate_root == protected_path or candidate_root.is_relative_to(protected_path) or protected_path.is_relative_to(candidate_root)