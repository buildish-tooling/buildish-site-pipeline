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

"""Planning, evaluation-report, and staged-output contract models."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import Field, field_validator, model_validator

from .base import SitePipelineBaseModel
from .enums import (
    CheckFailureThreshold,
    DiagnosticSeverity,
    MaterializationInputKind,
    MaterializationStatus,
    PlanningTarget,
    RunStatus,
    StageCommand,
)
from .scalars import (
    ExtensionsObject,
    LocalPathString,
    NonEmptyString,
    NonNegativeInteger,
    PositiveInteger,
    SchemaVersion,
    StageRelativePath,
    TimestampString,
)


class ResolvedMaterializationEntry(SitePipelineBaseModel):
    """One required local input discovered by planning."""

    source_key: NonEmptyString | None = None
    input_kind: MaterializationInputKind
    component_slug: NonEmptyString | None = None
    artifact_key: NonEmptyString | None = None
    release_line: NonEmptyString | None = None
    version: NonEmptyString | None = None
    ref: NonEmptyString | None = None
    tag: NonEmptyString | None = None
    commit_sha: NonEmptyString | None = None
    expected_local_path: LocalPathString
    status: MaterializationStatus
    provenance: NonEmptyString | None = None
    watch_eligible: bool | None = None
    reason: NonEmptyString | None = None


class ReducedDiagnosticDetailsSummary(SitePipelineBaseModel):
    """Bounded replacement object for oversized diagnostic details."""

    omitted: Literal[True]
    reason: Literal["sizeLimitExceeded"]
    actual_bytes: PositiveInteger
    limit_bytes: PositiveInteger
    summary: NonEmptyString | None = None
    fingerprint: NonEmptyString | None = None

    @model_validator(mode="after")
    def ensure_actual_size_exceeds_limit(self) -> Self:
        if self.actual_bytes <= self.limit_bytes:
            raise ValueError(
                "Reduced diagnostic details must record actualBytes > limitBytes"
            )
        return self


class PipelineDiagnosticEntry(SitePipelineBaseModel):
    """Structured pipeline diagnostic entry."""

    severity: DiagnosticSeverity
    code: NonEmptyString
    message: NonEmptyString
    component_slug: NonEmptyString | None = None
    artifact_key: NonEmptyString | None = None
    target_id: NonEmptyString | None = None
    details: ReducedDiagnosticDetailsSummary | ExtensionsObject | None = None

    @field_validator("details")
    @classmethod
    def preserve_validated_extension_object(
        cls,
        details: ReducedDiagnosticDetailsSummary | ExtensionsObject | None,
    ) -> ReducedDiagnosticDetailsSummary | ExtensionsObject | None:
        return details


class ResolvedMaterializationReportV1(SitePipelineBaseModel):
    """Machine-readable planning report for required local inputs."""

    schema_version: Literal[1]
    generated_at: TimestampString
    target: PlanningTarget
    entries: list[ResolvedMaterializationEntry]
    diagnostics: list[PipelineDiagnosticEntry] = Field(default_factory=list)

    @model_validator(mode="after")
    def ensure_watch_entries_are_explicit(self) -> Self:
        if self.target is PlanningTarget.WATCH and any(
            entry.watch_eligible is None for entry in self.entries
        ):
            raise ValueError(
                "Watch planning reports must include watchEligible on every entry"
            )
        return self


class CheckSummary(SitePipelineBaseModel):
    """Outcome summary for one ``check`` run."""

    status: RunStatus
    passed: bool
    fail_on_severity: CheckFailureThreshold
    error_count: NonNegativeInteger
    warning_count: NonNegativeInteger
    info_count: NonNegativeInteger

    @model_validator(mode="after")
    def ensure_normative_count_and_pass_rules(self) -> Self:
        if self.status is RunStatus.CLEAN and (
            self.error_count != 0 or self.warning_count != 0
        ):
            raise ValueError("status=clean requires zero errors and zero warnings")
        if self.status is RunStatus.WARNINGS and (
            self.error_count != 0 or self.warning_count == 0
        ):
            raise ValueError(
                "status=warnings requires zero errors and at least one warning"
            )
        if self.status is RunStatus.ERRORS and self.error_count == 0:
            raise ValueError("status=errors requires at least one error")

        expected_passed = self.error_count == 0 and (
            self.fail_on_severity is CheckFailureThreshold.ERROR
            or self.warning_count == 0
        )
        if self.passed is not expected_passed:
            raise ValueError(
                "passed must match the failOnSeverity threshold and diagnostic counts"
            )
        return self


class CheckReportV1(SitePipelineBaseModel):
    """Machine-readable result of ``site-pipeline check``."""

    schema_version: Literal[1]
    generated_at: TimestampString
    command: Literal["check"]
    summary: CheckSummary
    diagnostics: list[PipelineDiagnosticEntry]


class StageRunSummary(SitePipelineBaseModel):
    """Outcome summary for one stage-producing run or watch cycle."""

    status: RunStatus
    succeeded: bool
    wrote_stage: bool
    stage_usable: bool
    error_count: NonNegativeInteger
    warning_count: NonNegativeInteger
    info_count: NonNegativeInteger

    @model_validator(mode="after")
    def ensure_normative_stage_summary_rules(self) -> Self:
        if self.status is RunStatus.CLEAN and (
            self.error_count != 0 or self.warning_count != 0
        ):
            raise ValueError("status=clean requires zero errors and zero warnings")
        if self.status is RunStatus.WARNINGS and (
            self.error_count != 0 or self.warning_count == 0
        ):
            raise ValueError(
                "status=warnings requires zero errors and at least one warning"
            )
        if self.status is RunStatus.ERRORS and self.error_count == 0:
            raise ValueError("status=errors requires at least one error")
        if self.wrote_stage and not self.stage_usable:
            raise ValueError("wroteStage=true requires stageUsable=true")
        if self.succeeded and (not self.wrote_stage or not self.stage_usable):
            raise ValueError(
                "succeeded=true requires wroteStage=true and stageUsable=true"
            )
        return self


class StageRunReportV1(SitePipelineBaseModel):
    """Machine-readable result of ``build`` or one completed watch cycle."""

    schema_version: Literal[1]
    generated_at: TimestampString
    command: StageCommand
    summary: StageRunSummary
    stage_root_path: LocalPathString | None = None
    manifest_path: LocalPathString | None = None
    cycle: NonNegativeInteger | None = None
    diagnostics: list[PipelineDiagnosticEntry]

    @model_validator(mode="after")
    def ensure_stage_report_contract(self) -> Self:
        if self.command is StageCommand.BUILD and self.cycle is not None:
            raise ValueError("build reports must omit cycle")
        if self.command is StageCommand.WATCH and self.cycle is None:
            raise ValueError("watch reports must include cycle")
        if self.summary.succeeded and self.manifest_path is None:
            raise ValueError("successful stage runs must include manifestPath")
        if self.manifest_path is not None and self.stage_root_path is None:
            raise ValueError("manifestPath requires stageRootPath")
        if not self.summary.stage_usable and self.manifest_path is not None:
            raise ValueError("stageUsable=false must omit manifestPath")
        return self


class StageRoots(SitePipelineBaseModel):
    """Top-level directory roots within a stage tree."""

    content: StageRelativePath
    static: StageRelativePath
    data: StageRelativePath

    @model_validator(mode="after")
    def ensure_distinct_roots(self) -> Self:
        if len({self.content, self.static, self.data}) != 3:
            raise ValueError("Stage roots must be distinct relative directories")
        return self


class StageDataFiles(SitePipelineBaseModel):
    """Inventory of aggregate metadata files present in a stage tree."""

    components: StageRelativePath
    artifacts: StageRelativePath
    routes: StageRelativePath
    redirects: StageRelativePath
    releases: StageRelativePath | None = None
    candidates: StageRelativePath | None = None
    refs: StageRelativePath | None = None
    translations: StageRelativePath | None = None
    compatibility: StageRelativePath | None = None
    mounts: StageRelativePath | None = None
    providers: StageRelativePath | None = None
    content_index: StageRelativePath | None = None
    diagnostics: StageRelativePath | None = None
    unit_contributions: StageRelativePath | None = None
    output_ownership: StageRelativePath | None = None
    aggregate_dependencies: StageRelativePath | None = None


class StageManifestV1(SitePipelineBaseModel):
    """Authoritative entry-point document for a staged output tree."""

    schema_version: Literal[1]
    stage_layout_version: SchemaVersion
    generated_at: TimestampString
    command: StageCommand
    front_matter_format: Literal["yaml"]
    aggregate_format: Literal["json"]
    roots: StageRoots
    data_files: StageDataFiles

    @model_validator(mode="after")
    def ensure_data_files_live_beneath_the_data_root(self) -> Self:
        data_root_prefix = f"{self.roots.data}/"
        for path_value in self.data_files.model_dump().values():
            if path_value is None:
                continue
            if not str(path_value).startswith(data_root_prefix):
                raise ValueError("All stage data files must live beneath roots.data")
        return self
