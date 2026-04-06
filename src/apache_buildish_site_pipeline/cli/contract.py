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

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from pathlib import Path

from apache_buildish_site_pipeline.models.enums import (
    CheckFailureThreshold,
    PlanningTarget,
    RunStatus,
)
from apache_buildish_site_pipeline.models.emitted.planning_stage_contract import (
    CheckReportV1,
    ResolvedMaterializationReportV1,
    StageRunReportV1,
)


class ReportFormat(StrEnum):
    """Supported operator-facing report encodings."""

    TEXT = "text"
    JSON = "json"


class WatchEventFormat(StrEnum):
    """Supported unstable machine-readable watch event encodings."""

    JSONL = "jsonl"


class WatchEventType(StrEnum):
    """Stable identifiers for the currently supported watch event variants."""

    READY = "ready"
    CYCLE_SUCCEEDED = "cycle-succeeded"
    CYCLE_FAILED = "cycle-failed"


@dataclass(frozen=True, slots=True)
class WatchEvent(ABC):
    """Base machine-readable watch event emitted on the configured sink."""

    cycle: int
    stage_root_path: str | None
    manifest_path: str | None

    @property
    @abstractmethod
    def event_type(self) -> WatchEventType:
        """Return the concrete event discriminator written into the JSONL stream."""

    def to_json_payload(self) -> dict[str, object | None]:
        """Serialize the event into the JSON payload written to the event sink."""

        return {
            "event": self.event_type.value,
            "cycle": self.cycle,
            "stageRootPath": self.stage_root_path,
            "manifestPath": self.manifest_path,
        }


@dataclass(frozen=True, slots=True)
class WatchReadyEvent(WatchEvent):
    """One-time readiness signal once the visible stage is safe to consume."""

    @property
    def event_type(self) -> WatchEventType:
        return WatchEventType.READY

    @classmethod
    def from_report(cls, report: StageRunReportV1) -> WatchReadyEvent:
        if report.cycle is None:
            raise ValueError("watch events require watch reports with a cycle number")
        return cls(
            cycle=report.cycle,
            stage_root_path=report.stage_root_path,
            manifest_path=report.manifest_path,
        )


@dataclass(frozen=True, slots=True)
class WatchCycleEvent(WatchEvent, ABC):
    """Shared payload fields for cycle outcome events."""

    status: RunStatus
    succeeded: bool
    wrote_stage: bool
    stage_usable: bool
    error_count: int
    warning_count: int
    info_count: int

    def to_json_payload(self) -> dict[str, object | None]:
        # Use explicit two-argument ``super`` here because Python 3.13 can raise
        # ``TypeError`` for zero-argument ``super()`` inside slotted dataclass
        # inheritance trees like this watch-event hierarchy.
        payload = super(WatchCycleEvent, self).to_json_payload()
        payload.update(
            {
                "status": self.status.value,
                "succeeded": self.succeeded,
                "wroteStage": self.wrote_stage,
                "stageUsable": self.stage_usable,
                "errorCount": self.error_count,
                "warningCount": self.warning_count,
                "infoCount": self.info_count,
            },
        )
        return payload


@dataclass(frozen=True, slots=True)
class WatchCycleSucceededEvent(WatchCycleEvent):
    """Successful watch cycle payload."""

    @property
    def event_type(self) -> WatchEventType:
        return WatchEventType.CYCLE_SUCCEEDED

    @classmethod
    def from_report(cls, report: StageRunReportV1) -> WatchCycleSucceededEvent:
        if report.cycle is None:
            raise ValueError("watch events require watch reports with a cycle number")
        return cls(
            cycle=report.cycle,
            stage_root_path=report.stage_root_path,
            manifest_path=report.manifest_path,
            status=report.summary.status,
            succeeded=report.summary.succeeded,
            wrote_stage=report.summary.wrote_stage,
            stage_usable=report.summary.stage_usable,
            error_count=report.summary.error_count,
            warning_count=report.summary.warning_count,
            info_count=report.summary.info_count,
        )


@dataclass(frozen=True, slots=True)
class WatchCycleFailedEvent(WatchCycleEvent):
    """Failed watch cycle payload."""

    @property
    def event_type(self) -> WatchEventType:
        return WatchEventType.CYCLE_FAILED

    @classmethod
    def from_report(cls, report: StageRunReportV1) -> WatchCycleFailedEvent:
        if report.cycle is None:
            raise ValueError("watch events require watch reports with a cycle number")
        return cls(
            cycle=report.cycle,
            stage_root_path=report.stage_root_path,
            manifest_path=report.manifest_path,
            status=report.summary.status,
            succeeded=report.summary.succeeded,
            wrote_stage=report.summary.wrote_stage,
            stage_usable=report.summary.stage_usable,
            error_count=report.summary.error_count,
            warning_count=report.summary.warning_count,
            info_count=report.summary.info_count,
        )


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
class WatchEventRequest:
    """Normalized unstable watch-event emission request."""

    event_format: WatchEventFormat
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
    unstable_event_request: WatchEventRequest | None


CommandInvocation = PlanInvocation | CheckInvocation | BuildInvocation | WatchInvocation
ReportModel = ResolvedMaterializationReportV1 | CheckReportV1 | StageRunReportV1


@dataclass(frozen=True, slots=True)
class CommandResult:
    """Executed command result before final report emission."""

    exit_code: ApplicationExitCode
    report: ReportModel
    text_output: str
