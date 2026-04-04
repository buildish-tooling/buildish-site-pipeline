# Copyright 2026 The Apache Software Foundation

"""Shared contextual evaluation package."""

from __future__ import annotations

from datetime import UTC, datetime

from apache_buildish_site_pipeline.models.planning_stage_contract import CheckReportV1

from .execution import run_evaluation
from .types import EvaluationMode, EvaluationRequest, EvaluationResult


def build_check_report(result: EvaluationResult) -> CheckReportV1:
    """Project an evaluation result into the public check report model."""

    return CheckReportV1(
        schema_version=1,
        generated_at=datetime.now(UTC),
        command="check",
        summary=result.check_summary,
        diagnostics=list(result.diagnostics),
    )


__all__ = [
    "EvaluationMode",
    "EvaluationRequest",
    "EvaluationResult",
    "build_check_report",
    "run_evaluation",
]