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

"""Internal CLI invocation and result contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, StrEnum
from pathlib import Path

from apache_buildish_site_pipeline.models.enums import CheckFailureThreshold, PlanningTarget
from apache_buildish_site_pipeline.models.planning_stage_contract import (
    CheckReportV1,
    ResolvedMaterializationReportV1,
    StageRunReportV1,
)


class ReportFormat(StrEnum):
    """Supported operator-facing report encodings."""

    TEXT = "text"
    JSON = "json"


class ApplicationExitCode(IntEnum):
    """Process exit codes defined by the CLI contract."""

    SUCCESS = 0
    DOMAIN_FAILURE = 1
    INVOCATION_ERROR = 2
    INTERNAL_FAILURE = 3


@dataclass(frozen=True, slots=True)
class RepositoryLayout:
    """Resolved filesystem layout for one command invocation."""

    cwd: Path
    workspace_root: Path
    catalog_path: Path
    site_root: Path
    stage_root: Path
    work_root: Path

    @property
    def repo_root(self) -> Path:
        """Backward-compatible alias for the authored workspace root."""

        return self.workspace_root


@dataclass(frozen=True, slots=True)
class ReportRequest:
    """Normalized report emission request."""

    report_format: ReportFormat
    schema_version: int | None
    output_path: Path | None

    @property
    def writes_to_stdout(self) -> bool:
        return self.output_path is None


@dataclass(frozen=True, slots=True)
class PlanInvocation:
    """Parsed `plan` command invocation."""

    layout: RepositoryLayout
    planning_target: PlanningTarget
    report_request: ReportRequest


@dataclass(frozen=True, slots=True)
class CheckInvocation:
    """Parsed `check` command invocation."""

    layout: RepositoryLayout
    fail_on_severity: CheckFailureThreshold
    report_request: ReportRequest


@dataclass(frozen=True, slots=True)
class BuildInvocation:
    """Parsed `build` command invocation."""

    layout: RepositoryLayout
    report_request: ReportRequest


@dataclass(frozen=True, slots=True)
class WatchInvocation:
    """Parsed `watch` command invocation."""

    layout: RepositoryLayout
    fail_on_severity: CheckFailureThreshold
    report_request: ReportRequest


CommandInvocation = PlanInvocation | CheckInvocation | BuildInvocation | WatchInvocation
ReportModel = ResolvedMaterializationReportV1 | CheckReportV1 | StageRunReportV1


@dataclass(frozen=True, slots=True)
class CommandResult:
    """Executed command result before final report emission."""

    exit_code: ApplicationExitCode
    report: ReportModel
    text_output: str