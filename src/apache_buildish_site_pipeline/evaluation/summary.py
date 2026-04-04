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