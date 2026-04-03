# Copyright 2026 The Apache Software Foundation

"""Summary helpers for check/build/watch evaluation outcomes."""

from __future__ import annotations

from apache_buildish_site_pipeline.models.enums import CheckFailureThreshold, RunStatus
from apache_buildish_site_pipeline.models.planning_stage_contract import CheckSummary

from .types import DiagnosticCounts


def build_run_status(counts: DiagnosticCounts) -> RunStatus:
    """Compute run status from diagnostic counts."""

    if counts.error_count > 0:
        return RunStatus.ERRORS
    if counts.warning_count > 0:
        return RunStatus.WARNINGS
    return RunStatus.CLEAN


def build_check_summary(
    *,
    counts: DiagnosticCounts,
    fail_on_severity: CheckFailureThreshold,
) -> CheckSummary:
    """Build the stable check summary model."""

    status = build_run_status(counts)
    passed = counts.error_count == 0 and (
        fail_on_severity is CheckFailureThreshold.ERROR or counts.warning_count == 0
    )
    return CheckSummary(
        status=status,
        passed=passed,
        fail_on_severity=fail_on_severity,
        error_count=counts.error_count,
        warning_count=counts.warning_count,
        info_count=counts.info_count,
    )