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

"""Shared stage-run report construction for build and watch commands."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from apache_buildish_site_pipeline.evaluation.summary import build_run_status
from apache_buildish_site_pipeline.evaluation.types import DiagnosticCounts, EvaluationResult
from apache_buildish_site_pipeline.models.enums import DiagnosticSeverity, StageCommand
from apache_buildish_site_pipeline.models.planning_stage_contract import PipelineDiagnosticEntry, StageRunReportV1, StageRunSummary
from apache_buildish_site_pipeline.staging.public_safety import sanitize_public_diagnostics


def build_stage_run_report(
    *,
    command: StageCommand,
    evaluation: EvaluationResult | None,
    succeeded: bool,
    wrote_stage: bool,
    stage_usable: bool,
    stage_root_path: Path | None,
    manifest_path: Path | None,
    diagnostics: tuple[PipelineDiagnosticEntry, ...] | None = None,
    cycle: int | None = None,
    workspace_root: Path | None = None,
    private_roots: tuple[Path, ...] = (),
) -> StageRunReportV1:
    """Build a typed stage-run report from evaluation data and final stage state."""

    effective_diagnostics = tuple(diagnostics if diagnostics is not None else (evaluation.diagnostics if evaluation is not None else ()))
    report_workspace_root = workspace_root or _report_workspace_root(evaluation)
    if report_workspace_root is not None:
        effective_diagnostics = sanitize_public_diagnostics(
            effective_diagnostics,
            workspace_root=report_workspace_root,
            private_roots=private_roots,
        )
    counts = _count_diagnostics(effective_diagnostics)
    return StageRunReportV1(
        schema_version=1,
        generated_at=datetime.now(UTC),
        command=command,
        summary=StageRunSummary(
            status=build_run_status(counts),
            succeeded=succeeded,
            wrote_stage=wrote_stage,
            stage_usable=stage_usable,
            error_count=counts.error_count,
            warning_count=counts.warning_count,
            info_count=counts.info_count,
        ),
        stage_root_path=str(stage_root_path) if stage_root_path is not None else None,
        manifest_path=str(manifest_path) if manifest_path is not None else None,
        cycle=cycle,
        diagnostics=list(effective_diagnostics),
    )


def _count_diagnostics(diagnostics: tuple[PipelineDiagnosticEntry, ...]) -> DiagnosticCounts:
    return DiagnosticCounts(
        error_count=sum(1 for entry in diagnostics if entry.severity is DiagnosticSeverity.ERROR),
        warning_count=sum(1 for entry in diagnostics if entry.severity is DiagnosticSeverity.WARNING),
        info_count=sum(1 for entry in diagnostics if entry.severity is DiagnosticSeverity.INFO),
    )


def _report_workspace_root(evaluation: EvaluationResult | None) -> Path | None:
    if evaluation is None:
        return None
    if evaluation.build_plan is not None:
        return evaluation.build_plan.workspace_root
    return evaluation.planning.site.workspace_root