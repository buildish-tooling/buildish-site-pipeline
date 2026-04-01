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

"""Planning, evaluation-report, and staged-output contract models."""

from __future__ import annotations

from typing import ClassVar, Literal, Self

from pydantic import Field, field_validator, model_validator

from ...docs.documentation import (
    ContractDocumentation,
    PipelineDerivedModel as SitePipelineBaseModel,
    SchemaExample,
    SchemaExportSpecification,
)
from ...docs.schema_examples import (
    check_report_example_document,
    materialization_report_example_document,
    stage_manifest_example_document,
    stage_run_report_example_document,
)
from ..enums import (
    CheckFailureThreshold,
    DiagnosticSeverity,
    MaterializationInputKind,
    MaterializationStatus,
    PlanningTarget,
    RunStatus,
    StageCommand,
)
from ..scalars import (
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
    """One local checkout or fetched input that the planner expects to exist."""

    source_key: NonEmptyString | None = Field(
        default=None,
        description="Named source binding that produced this materialization requirement.",
        examples=["apache-spark"],
    )
    input_kind: MaterializationInputKind = Field(
        description="Kind of materialized input, such as a component checkout, artifact checkout, or provider-derived fetch target.",
    )
    component_slug: NonEmptyString | None = Field(
        default=None,
        description="Component slug for the materialized input when the requirement is tied to a specific component.",
        examples=["spark"],
    )
    artifact_key: NonEmptyString | None = Field(
        default=None,
        description="Artifact key for the materialized input when the requirement is tied to one independently versioned artifact.",
        examples=["runtime"],
    )
    release_line: NonEmptyString | None = Field(
        default=None,
        description="Release-line key when the required local input is scoped to one maintenance line.",
        examples=["4.0"],
    )
    version: NonEmptyString | None = Field(
        default=None,
        description="Exact version when the required local input is scoped to one released version.",
        examples=["4.0.0"],
    )
    ref: NonEmptyString | None = Field(
        default=None,
        description="Exact source-control ref when the planner resolved this input from a branch or named ref.",
        examples=["refs/heads/main"],
    )
    tag: NonEmptyString | None = Field(
        default=None,
        description="Exact tag name when the planner resolved this input from a tagged release.",
        examples=["v4.0.0"],
    )
    commit_sha: NonEmptyString | None = Field(
        default=None,
        description="Resolved commit SHA for the required input when one was discovered.",
        examples=["6f0fd1f7b2c4a6d8e9f00123456789abcdef0123"],
    )
    expected_local_path: LocalPathString = Field(
        description="Local filesystem path where the planner expects this input to be present or materialized.",
        examples=[".buildish/materialized/apache-spark/main"],
    )
    status: MaterializationStatus = Field(
        description="Current materialization status, such as already present, missing, or needing refresh.",
    )
    provenance: NonEmptyString | None = Field(
        default=None,
        description="Short explanation of how the planner derived this materialization requirement.",
    )
    watch_eligible: bool | None = Field(
        default=None,
        description="Whether watch mode can safely monitor this input for incremental restaging.",
    )
    reason: NonEmptyString | None = Field(
        default=None,
        description="Human-readable explanation of why this input is required or why its current status matters.",
    )


class ReducedDiagnosticDetailsSummary(SitePipelineBaseModel):
    """Compact placeholder used when full diagnostic details were too large to keep."""

    omitted: Literal[True] = Field(
        description="Always `true`, signalling that the original diagnostic details were intentionally omitted."
    )
    reason: Literal["sizeLimitExceeded"] = Field(
        description="Reason why the original diagnostic details were replaced by this bounded summary."
    )
    actual_bytes: PositiveInteger = Field(
        description="Actual serialized size of the original diagnostic details payload in bytes.",
        examples=[524288],
    )
    limit_bytes: PositiveInteger = Field(
        description="Configured byte limit that the original diagnostic details exceeded.",
        examples=[65536],
    )
    summary: NonEmptyString | None = Field(
        default=None,
        description="Short human-readable summary of the omitted details payload.",
    )
    fingerprint: NonEmptyString | None = Field(
        default=None,
        description="Stable fingerprint that lets tooling correlate repeated oversized payloads without storing the full payload.",
    )

    @model_validator(mode="after")
    def ensure_actual_size_exceeds_limit(self) -> Self:
        if self.actual_bytes <= self.limit_bytes:
            raise ValueError(
                "Reduced diagnostic details must record actualBytes > limitBytes"
            )
        return self


class PipelineDiagnosticEntry(SitePipelineBaseModel):
    """Structured diagnostic emitted during planning, checking, or staging."""

    severity: DiagnosticSeverity = Field(
        description="Diagnostic severity level that callers can use for gating and presentation."
    )
    code: NonEmptyString = Field(
        description="Stable machine-readable diagnostic code.",
        examples=["catalog.invalidRedirectTarget"],
    )
    message: NonEmptyString = Field(
        description="Primary human-readable diagnostic message.",
        examples=["Redirect target route:/spark/missing/ could not be resolved."],
    )
    component_slug: NonEmptyString | None = Field(
        default=None,
        description="Component slug associated with the diagnostic when a specific component is directly affected.",
        examples=["spark"],
    )
    artifact_key: NonEmptyString | None = Field(
        default=None,
        description="Artifact key associated with the diagnostic when a specific artifact is directly affected.",
        examples=["runtime"],
    )
    target_id: NonEmptyString | None = Field(
        default=None,
        description="Additional target identifier, such as a path, ref, or release key, that helps callers locate the problem precisely.",
        examples=["/spark/docs/current/"],
    )
    details: ReducedDiagnosticDetailsSummary | ExtensionsObject | None = Field(
        default=None,
        description="Structured detail payload for the diagnostic, or a bounded summary when the original detail payload was too large.",
    )

    @field_validator("details")
    @classmethod
    def preserve_validated_extension_object(
        cls,
        details: ReducedDiagnosticDetailsSummary | ExtensionsObject | None,
    ) -> ReducedDiagnosticDetailsSummary | ExtensionsObject | None:
        return details


class ResolvedMaterializationReportV1(SitePipelineBaseModel):
    """Machine-readable planning report for required local inputs."""

    contract_documentation: ClassVar[ContractDocumentation] = ContractDocumentation(
        category="emitted",
        ownership="pipeline-derived",
        summary="Planning inventory of required local inputs and their current materialization status.",
    )
    schema_export: ClassVar[SchemaExportSpecification] = SchemaExportSpecification(
        filename="materialization-report-v1.schema.json",
        title="Site Pipeline Materialization Report v1",
        examples=(
            SchemaExample(
                summary="Planning report with one required release checkout.",
                value_builder=materialization_report_example_document,
            ),
        ),
    )

    schema_version: Literal[1] = Field(
        description="Schema version for the materialization planning report."
    )
    generated_at: TimestampString = Field(
        description="Timestamp when this planning report was generated."
    )
    target: PlanningTarget = Field(
        description="Planning target that this report was generated for, such as build or watch preparation."
    )
    entries: list[ResolvedMaterializationEntry] = Field(
        description="Required local inputs together with their expected locations and current materialization status."
    )
    diagnostics: list[PipelineDiagnosticEntry] = Field(
        default_factory=list,
        description="Structured diagnostics emitted while resolving required local inputs for this planning target.",
    )

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
    """Outcome counts and pass/fail decision for one `check` run."""

    status: RunStatus = Field(
        description="Overall diagnostic status for the run after counts were evaluated."
    )
    passed: bool = Field(
        description="Whether the check run satisfied the configured failure threshold and should be treated as passing."
    )
    fail_on_severity: CheckFailureThreshold = Field(
        description="Configured severity threshold that decides whether warnings already fail the run or only errors do."
    )
    error_count: NonNegativeInteger = Field(
        description="Number of error diagnostics emitted during the run."
    )
    warning_count: NonNegativeInteger = Field(
        description="Number of warning diagnostics emitted during the run."
    )
    info_count: NonNegativeInteger = Field(
        description="Number of informational diagnostics emitted during the run."
    )

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

    contract_documentation: ClassVar[ContractDocumentation] = ContractDocumentation(
        category="emitted",
        ownership="pipeline-derived",
        summary="Validation result for one `site-pipeline check` invocation.",
    )
    schema_export: ClassVar[SchemaExportSpecification] = SchemaExportSpecification(
        filename="check-report-v1.schema.json",
        title="Site Pipeline Check Report v1",
        examples=(
            SchemaExample(
                summary="Validation report with one warning that does not fail the run.",
                value_builder=check_report_example_document,
            ),
        ),
    )

    schema_version: Literal[1] = Field(description="Schema version for the check report.")
    generated_at: TimestampString = Field(
        description="Timestamp when the check report was generated."
    )
    command: Literal["check"] = Field(
        description="Command name that produced this report; always `check` for this contract."
    )
    summary: CheckSummary = Field(
        description="Outcome summary with pass/fail state and diagnostic counts for the run."
    )
    diagnostics: list[PipelineDiagnosticEntry] = Field(
        description="Structured diagnostics emitted during the check run."
    )


class StageRunSummary(SitePipelineBaseModel):
    """Outcome counts and usability flags for one stage-producing run or watch cycle."""

    status: RunStatus = Field(
        description="Overall diagnostic status for the run after counts were evaluated."
    )
    succeeded: bool = Field(
        description="Whether the run finished with a usable stage and should be treated as successful."
    )
    wrote_stage: bool = Field(
        description="Whether the run actually wrote or refreshed stage output on disk."
    )
    stage_usable: bool = Field(
        description="Whether downstream tooling may safely use the stage after this run finished."
    )
    error_count: NonNegativeInteger = Field(
        description="Number of error diagnostics emitted during the run."
    )
    warning_count: NonNegativeInteger = Field(
        description="Number of warning diagnostics emitted during the run."
    )
    info_count: NonNegativeInteger = Field(
        description="Number of informational diagnostics emitted during the run."
    )

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

    contract_documentation: ClassVar[ContractDocumentation] = ContractDocumentation(
        category="emitted",
        ownership="pipeline-derived",
        summary="Execution result for one `build` run or completed watch cycle.",
    )
    schema_export: ClassVar[SchemaExportSpecification] = SchemaExportSpecification(
        filename="stage-run-report-v1.schema.json",
        title="Site Pipeline Stage Run Report v1",
        examples=(
            SchemaExample(
                summary="Successful build report with a usable stage manifest.",
                value_builder=stage_run_report_example_document,
            ),
        ),
    )

    schema_version: Literal[1] = Field(description="Schema version for the stage run report.")
    generated_at: TimestampString = Field(
        description="Timestamp when the stage run report was generated."
    )
    command: StageCommand = Field(
        description="Stage-producing command that produced this report, such as `build` or `watch`."
    )
    summary: StageRunSummary = Field(
        description="Outcome summary with success state, stage usability, and diagnostic counts for the run."
    )
    stage_root_path: LocalPathString | None = Field(
        default=None,
        description="Local path to the root of the stage tree, if the run produced one."
    )
    manifest_path: LocalPathString | None = Field(
        default=None,
        description="Local path to the generated stage manifest when the stage is usable."
    )
    cycle: NonNegativeInteger | None = Field(
        default=None,
        description="Completed watch-cycle number for watch reports; omitted for one-shot build reports.",
        examples=[3],
    )
    diagnostics: list[PipelineDiagnosticEntry] = Field(
        description="Structured diagnostics emitted during the stage-producing run."
    )

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
    """Named top-level directories inside a stage tree."""

    content: StageRelativePath = Field(
        description="Stage-relative directory that contains rendered pages and content files.",
        examples=["content"],
    )
    static: StageRelativePath = Field(
        description="Stage-relative directory that contains copied static assets.",
        examples=["static"],
    )
    data: StageRelativePath = Field(
        description="Stage-relative directory that contains aggregate metadata files.",
        examples=["data"],
    )

    @model_validator(mode="after")
    def ensure_distinct_roots(self) -> Self:
        if len({self.content, self.static, self.data}) != 3:
            raise ValueError("Stage roots must be distinct relative directories")
        return self


class StageDataFiles(SitePipelineBaseModel):
    """Stage-relative paths of aggregate metadata files currently present in one stage tree."""

    components: StageRelativePath = Field(
        description="Stage-relative path of the published component aggregate file.",
        examples=["data/components.json"],
    )
    artifacts: StageRelativePath = Field(
        description="Stage-relative path of the published artifact aggregate file.",
        examples=["data/artifacts.json"],
    )
    routes: StageRelativePath = Field(
        description="Stage-relative path of the published route aggregate file.",
        examples=["data/routes.json"],
    )
    redirects: StageRelativePath = Field(
        description="Stage-relative path of the published redirect aggregate file.",
        examples=["data/redirects.json"],
    )
    releases: StageRelativePath | None = Field(
        default=None,
        description="Stage-relative path of the published release aggregate file when release metadata is present.",
        examples=["data/releases.json"],
    )
    candidates: StageRelativePath | None = Field(
        default=None,
        description="Stage-relative path of the published candidate aggregate file when release-candidate metadata is present.",
        examples=["data/candidates.json"],
    )
    refs: StageRelativePath | None = Field(
        default=None,
        description="Stage-relative path of the published ref aggregate file when development, line-head, or named-ref metadata is present.",
        examples=["data/refs.json"],
    )
    translations: StageRelativePath | None = Field(
        default=None,
        description="Stage-relative path of the published translation aggregate file when localized page groups are present.",
        examples=["data/translations.json"],
    )
    compatibility: StageRelativePath | None = Field(
        default=None,
        description="Stage-relative path of the published compatibility aggregate file when compatibility assertions are present.",
        examples=["data/compatibility.json"],
    )
    mounts: StageRelativePath | None = Field(
        default=None,
        description="Stage-relative path of the published mount aggregate file when mounted subtrees are present.",
        examples=["data/mounts.json"],
    )
    providers: StageRelativePath | None = Field(
        default=None,
        description="Stage-relative path of the provider aggregate file when provider metadata is present in the stage.",
        examples=["data/providers.json"],
    )
    content_index: StageRelativePath | None = Field(
        default=None,
        description="Stage-relative path of the content-index aggregate file when the stage includes a generated page index.",
        examples=["data/content-index.json"],
    )
    diagnostics: StageRelativePath | None = Field(
        default=None,
        description="Stage-relative path of the diagnostics aggregate file when diagnostics were published into the stage.",
        examples=["data/diagnostics.json"],
    )
    unit_contributions: StageRelativePath | None = Field(
        default=None,
        description="Stage-relative path of the persisted unit-contribution manifest file when it is present.",
        examples=["data/unit-contributions.json"],
    )
    output_ownership: StageRelativePath | None = Field(
        default=None,
        description="Stage-relative path of the output-ownership map when incremental rebuild metadata is present.",
        examples=["data/output-ownership.json"],
    )
    aggregate_dependencies: StageRelativePath | None = Field(
        default=None,
        description="Stage-relative path of the aggregate-dependency map when incremental rebuild metadata is present.",
        examples=["data/aggregate-dependencies.json"],
    )


class StageManifestV1(SitePipelineBaseModel):
    """Authoritative entry-point document for a staged output tree."""

    contract_documentation: ClassVar[ContractDocumentation] = ContractDocumentation(
        category="emitted",
        ownership="pipeline-derived",
        summary="Entry point for a stage tree, including roots, formats, and aggregate file locations.",
        file_path="manifest.json",
    )
    schema_export: ClassVar[SchemaExportSpecification] = SchemaExportSpecification(
        filename="stage-manifest-v1.schema.json",
        title="Site Pipeline Stage Manifest v1",
        examples=(
            SchemaExample(
                summary="Stage manifest that points at content, static, and aggregate roots.",
                value_builder=stage_manifest_example_document,
            ),
        ),
    )

    schema_version: Literal[1] = Field(description="Schema version for the stage manifest.")
    stage_layout_version: SchemaVersion = Field(
        description="Version of the stage directory layout contract that this manifest follows."
    )
    generated_at: TimestampString = Field(
        description="Timestamp when the manifest was generated."
    )
    command: StageCommand = Field(
        description="Stage-producing command that created the stage tree represented by this manifest."
    )
    front_matter_format: Literal["yaml"] = Field(
        description="Front matter serialization format used for staged content files."
    )
    aggregate_format: Literal["json"] = Field(
        description="Serialization format used for aggregate metadata files in the stage data directory."
    )
    roots: StageRoots = Field(
        description="Top-level stage directories used for content, static assets, and aggregate data."
    )
    data_files: StageDataFiles = Field(
        description="Stage-relative paths of aggregate metadata files currently present in the stage."
    )

    @model_validator(mode="after")
    def ensure_data_files_live_beneath_the_data_root(self) -> Self:
        data_root_prefix = f"{self.roots.data}/"
        for path_value in self.data_files.model_dump().values():
            if path_value is None:
                continue
            if not str(path_value).startswith(data_root_prefix):
                raise ValueError("All stage data files must live beneath roots.data")
        return self
