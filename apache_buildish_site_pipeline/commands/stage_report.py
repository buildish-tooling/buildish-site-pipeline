# Copyright 2026 The Apache Software Foundation

"""Shared stage-run report construction for build and watch commands."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from apache_buildish_site_pipeline.evaluation.summary import build_run_status
from apache_buildish_site_pipeline.evaluation.types import DiagnosticCounts, EvaluationResult
from apache_buildish_site_pipeline.models.enums import DiagnosticSeverity, StageCommand
from apache_buildish_site_pipeline.models.planning_stage_contract import PipelineDiagnosticEntry, StageRunReportV1, StageRunSummary


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
) -> StageRunReportV1:
    """Build a typed stage-run report from evaluation data and final stage state."""

    effective_diagnostics = tuple(diagnostics if diagnostics is not None else (evaluation.diagnostics if evaluation is not None else ()))
    counts = _count_diagnostics(effective_diagnostics)
    return StageRunReportV1(
        schema_version=1,
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
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