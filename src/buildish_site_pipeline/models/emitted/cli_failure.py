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

"""Versioned machine-readable CLI failure contract."""

from __future__ import annotations

from enum import StrEnum
from typing import ClassVar, Literal

from pydantic import Field

from buildish_site_pipeline.docs.documentation import (
    ContractDocumentation,
    PipelineDerivedModel,
    SchemaExample,
    SchemaExportSpecification,
)
from buildish_site_pipeline.docs.schema_examples import cli_failure_example_document
from buildish_site_pipeline.models.scalars import NonEmptyString, NonNegativeInteger


class CliErrorCategory(StrEnum):
    """Stable high-level failure categories for CLI automation."""

    INVOCATION = "invocation"
    INPUT = "input"
    PLANNING = "planning"
    INTERNAL = "internal"


class CliDiagnosticIssue(PipelineDerivedModel):
    """One bounded, actionable detail attached to a CLI failure."""

    location: NonEmptyString = Field(
        description="Bounded source or field location for the issue.",
        examples=["components[0].slug"],
    )
    code: NonEmptyString = Field(
        description="Stable machine-readable issue code.",
        examples=["required"],
    )
    message: NonEmptyString = Field(
        description="Concise human-readable explanation of the issue.",
        examples=["Field required"],
    )
    actual_bytes: NonNegativeInteger | None = Field(
        default=None,
        description="Observed input size when the issue reports a size limit.",
    )
    limit_bytes: NonNegativeInteger | None = Field(
        default=None,
        description="Configured maximum input size when the issue reports a size limit.",
    )

    def to_json_payload(self) -> dict[str, object]:
        """Serialize this issue using the stable camel-case CLI contract."""

        return self.model_dump(mode="json", by_alias=True, exclude_none=True)


class CliDiagnostic(PipelineDerivedModel):
    """Structured operator-facing failure without internal exception details."""

    category: CliErrorCategory = Field(
        description="High-level failure category suitable for automation branching."
    )
    code: NonEmptyString = Field(
        description="Stable machine-readable CLI failure code.",
        examples=["input-validation-failed"],
    )
    message: NonEmptyString = Field(
        description="Concise human-readable summary of the failure."
    )
    source: NonEmptyString | None = Field(
        default=None,
        description="Sanitized input name associated with the failure, when available.",
        examples=["site/catalog.yaml"],
    )
    issues: tuple[CliDiagnosticIssue, ...] = Field(
        default=(),
        description="Bounded actionable issue details retained for this failure.",
    )
    omitted_issue_count: NonNegativeInteger = Field(
        default=0,
        description="Number of additional issues omitted to keep the failure bounded.",
    )

    def to_json_payload(self) -> dict[str, object]:
        """Serialize the stable machine-readable diagnostic fields."""

        return self.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
            exclude_defaults=True,
        )

    def render_text(self) -> str:
        """Render a concise human diagnostic while retaining the first issue."""

        source_suffix = f" [{self.source}]" if self.source is not None else ""
        issue_suffix = ""
        if self.issues:
            first_issue = self.issues[0]
            issue_suffix = (
                f": {first_issue.location}: {first_issue.message}"
                if first_issue.location != "$"
                else f": {first_issue.message}"
            )
            remaining = len(self.issues) - 1 + self.omitted_issue_count
            if remaining:
                plural_suffix = "s" if remaining != 1 else ""
                issue_suffix += f" (+{remaining} more issue{plural_suffix})"
        return f"{self.code}{source_suffix}: {self.message}{issue_suffix}"


class CliFailureReportV1(PipelineDerivedModel):
    """Stable JSON envelope emitted when no command report can be produced."""

    contract_documentation: ClassVar[ContractDocumentation] = ContractDocumentation(
        category="emitted",
        ownership="pipeline-derived",
        summary="Versioned CLI failure envelope emitted in place of a requested JSON command report.",
    )
    schema_export: ClassVar[SchemaExportSpecification] = SchemaExportSpecification(
        filename="cli-failure-report-v1.schema.json",
        title="Site Pipeline CLI Failure Report v1",
        examples=(
            SchemaExample(
                summary="Authored input validation failure with one actionable issue.",
                value_builder=cli_failure_example_document,
            ),
        ),
    )

    schema_version: Literal[1] = Field(
        description="Schema version for the CLI failure report."
    )
    kind: Literal["cliFailure"] = Field(
        description="Discriminator separating failures from command-specific reports."
    )
    command: Literal["plan", "check", "build", "watch"] = Field(
        description="Command whose normal JSON report could not be produced."
    )
    exit_code: Literal[1, 2, 3] = Field(
        description="CLI process exit code associated with this failure."
    )
    diagnostic: CliDiagnostic = Field(
        alias="error",
        description="Structured error category, code, message, and bounded issue details.",
    )

    def to_json_payload(self) -> dict[str, object]:
        """Serialize the versioned CLI failure report contract."""

        return self.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
            exclude_defaults=True,
        )
