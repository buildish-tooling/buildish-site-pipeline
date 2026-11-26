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

"""Execution profiles and component snapshot availability contracts."""

from __future__ import annotations

from pydantic import Field
from ...docs.documentation import PipelineDerivedModel
from ..enums import (
    ExecutionProfile,
    SnapshotRequirement,
    MaterializationStatus,
    PublicationState,
    ContextAction,
)
from ..scalars import NonEmptyString, LocalPathString, TimestampString


class SnapshotInput(PipelineDerivedModel):
    """One configured component-owned provider file and its observed availability."""

    component_slug: NonEmptyString | None = Field(
        default=None, description="Owning component, or absent for aggregate inventory."
    )
    source_key: NonEmptyString | None = Field(
        default=None,
        description="Catalog source, or absent for the aggregate file beside the catalog.",
    )
    expected_local_path: LocalPathString = Field(
        description="Expected local snapshot file location."
    )
    requirement: SnapshotRequirement = Field(
        description="Authored availability requirement."
    )
    required: bool = Field(
        description="Whether the active execution profile requires this file."
    )
    status: MaterializationStatus = Field(description="Observed file availability.")
    fetched_at: dict[str, TimestampString] = Field(
        default_factory=dict,
        description="Actual per-provider refresh times in this file.",
    )


class ContextDisposition(PipelineDerivedModel):
    """Publication action for one desired exact release in this invocation."""

    component_slug: NonEmptyString = Field(description="Owning component.")
    artifact_key: NonEmptyString = Field(description="Owning artifact.")
    version: NonEmptyString = Field(description="Desired release version.")
    action: ContextAction = Field(
        description="Effective action for original docs or a withdrawal route."
    )
    publication_state: PublicationState | None = Field(
        default=None, description="Resolved authored/provider publication state."
    )
    reason: NonEmptyString | None = Field(
        default=None, description="Why original docs are not staged."
    )


class ExecutionReportContext(PipelineDerivedModel):
    """Shared execution assessment carried by all command reports."""

    profile: ExecutionProfile = Field(
        default=ExecutionProfile.LOCAL,
        description="Explicit execution profile used by this invocation.",
    )
    snapshot_inputs: list[SnapshotInput] = Field(
        default_factory=list,
        description="Configured component provider inputs and their readiness.",
    )
    context_dispositions: list[ContextDisposition] = Field(
        default_factory=list,
        description="Publication actions for known desired release contexts.",
    )
