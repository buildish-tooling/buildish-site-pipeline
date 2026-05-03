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

"""Persisted stage metadata that makes watch-mode incremental rebuilds deterministic."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Literal, cast

from pydantic import Field

from ..docs.documentation import (
    ContractDocumentation,
    PipelineDerivedModel as SitePipelineBaseModel,
    SchemaExample,
    SchemaExportSpecification,
)
from ..docs.schema_examples import (
    aggregate_dependencies_example_document,
    output_ownership_example_document,
    unit_contributions_example_document,
)
from ..models.emitted.planning_stage_contract import (
    StageDataFiles,
    StageManifestV1,
    StageRelativePath,
)
from ..path_trust import path_resolves_through_symlink
from .ownership import OwnedUnit
from .worker_protocol import UnitContributionManifestWire

COORDINATOR_OWNER_ID = "coordinator"


class PersistedUnitContributionsV1(SitePipelineBaseModel):
    """Stable per-unit page contribution manifests retained in the visible stage."""

    contract_documentation: ClassVar[ContractDocumentation] = ContractDocumentation(
        category="emitted",
        ownership="pipeline-derived",
        summary="Per-unit page contribution manifests retained in the visible stage.",
        file_path="data/_pipeline/unit-contributions.json",
    )
    schema_export: ClassVar[SchemaExportSpecification] = SchemaExportSpecification(
        filename="unit-contributions-v1.schema.json",
        title="Site Pipeline data/_pipeline/unit-contributions.json v1",
        examples=(
            SchemaExample(
                summary="Retained per-unit contribution map with one staged page.",
                value_builder=unit_contributions_example_document,
            ),
        ),
    )

    schema_version: Literal[1] = Field(
        default=1,
        description="Schema version for the persisted unit-contribution manifest file.",
    )
    units: tuple[UnitContributionManifestWire, ...] = Field(
        default=(),
        description="Worker contribution manifests retained for every staged unit that currently owns visible output.",
    )


class OutputOwnershipClaimV1(SitePipelineBaseModel):
    """One exact published file or directory root together with its logical owner."""

    owner_id: str = Field(
        description="Logical owner identifier for the output, such as a unit owner id or the coordinator.",
        examples=["coordinator"],
    )
    unit_id: str | None = Field(
        default=None,
        description="Unit identifier when the owning output belongs to one concrete staging unit.",
        examples=["component:spark:runtime"],
    )
    path_kind: Literal["directory", "file"] = Field(
        description="Whether the owned stage-relative path refers to one exact file or one directory root."
    )
    stage_relative_path: StageRelativePath = Field(
        description="Owned path inside the visible stage.",
        examples=["content/spark"],
    )


class OutputOwnershipMapV1(SitePipelineBaseModel):
    """Published ownership inventory used to prune retained stages safely."""

    contract_documentation: ClassVar[ContractDocumentation] = ContractDocumentation(
        category="emitted",
        ownership="pipeline-derived",
        summary="Ownership map for staged files and directories retained across rebuilds.",
        file_path="data/_pipeline/output-ownership.json",
    )
    schema_export: ClassVar[SchemaExportSpecification] = SchemaExportSpecification(
        filename="output-ownership-v1.schema.json",
        title="Site Pipeline data/_pipeline/output-ownership.json v1",
        examples=(
            SchemaExample(
                summary="Ownership claims for one unit directory and one coordinator aggregate file.",
                value_builder=output_ownership_example_document,
            ),
        ),
    )

    schema_version: Literal[1] = Field(
        default=1,
        description="Schema version for the output-ownership map.",
    )
    claims: tuple[OutputOwnershipClaimV1, ...] = Field(
        default=(),
        description="Ownership claims for every retained stage file or directory root.",
    )


class AggregateDependencyEntryV1(SitePipelineBaseModel):
    """One coordinator-owned aggregate and the units that may change its payload."""

    stage_relative_path: StageRelativePath = Field(
        description="Coordinator-owned aggregate file inside the visible stage.",
        examples=["data/components.json"],
    )
    dependent_unit_ids: tuple[str, ...] = Field(
        default=(),
        description="Unit identifiers whose output can invalidate or change this aggregate file.",
    )


class AggregateDependencyMapV1(SitePipelineBaseModel):
    """Shared-output dependency map for the current first-wave coordinator outputs."""

    contract_documentation: ClassVar[ContractDocumentation] = ContractDocumentation(
        category="emitted",
        ownership="pipeline-derived",
        summary="Coordinator aggregate files and the units that can invalidate them.",
        file_path="data/_pipeline/aggregate-dependencies.json",
    )
    schema_export: ClassVar[SchemaExportSpecification] = SchemaExportSpecification(
        filename="aggregate-dependencies-v1.schema.json",
        title="Site Pipeline data/_pipeline/aggregate-dependencies.json v1",
        examples=(
            SchemaExample(
                summary="Aggregate dependency map that marks which units can invalidate one shared file.",
                value_builder=aggregate_dependencies_example_document,
            ),
        ),
    )

    schema_version: Literal[1] = Field(
        default=1,
        description="Schema version for the aggregate-dependency map.",
    )
    entries: tuple[AggregateDependencyEntryV1, ...] = Field(
        default=(),
        description="Coordinator-owned aggregate files together with the units that may change them.",
    )


@dataclass(frozen=True, slots=True)
class RetainedStageIncrementalState:
    """Incremental metadata loaded from the last trusted visible stage."""

    unit_contributions: PersistedUnitContributionsV1
    output_ownership: OutputOwnershipMapV1
    aggregate_dependencies: AggregateDependencyMapV1


def build_output_ownership_map(
    *, units: tuple[OwnedUnit, ...], data_files: StageDataFiles
) -> OutputOwnershipMapV1:
    """Describe every published first-wave output root and shared aggregate exactly once."""

    claims = [
        OutputOwnershipClaimV1(
            owner_id=unit.owner_id,
            unit_id=unit.unit_id,
            path_kind="directory",
            stage_relative_path=str(stage_relative_path),
        )
        for unit in units
        for stage_relative_path in (*unit.content_stage_roots, *unit.static_stage_roots)
    ]
    claims.extend(
        OutputOwnershipClaimV1(
            owner_id=COORDINATOR_OWNER_ID,
            path_kind="file",
            stage_relative_path=str(stage_relative_path),
        )
        for stage_relative_path in _coordinator_owned_stage_paths(data_files)
    )
    claims.sort(
        key=lambda claim: (
            str(claim.stage_relative_path),
            claim.path_kind,
            claim.owner_id,
            claim.unit_id or "",
        )
    )
    return OutputOwnershipMapV1(claims=tuple(claims))


def build_aggregate_dependency_map(
    *, units: tuple[OwnedUnit, ...], data_files: StageDataFiles
) -> AggregateDependencyMapV1:
    """Persist a conservative dependency map for coordinator-owned shared outputs."""

    dependent_unit_ids = tuple(sorted(unit.unit_id for unit in units))
    entries = tuple(
        AggregateDependencyEntryV1(
            stage_relative_path=str(stage_relative_path),
            dependent_unit_ids=dependent_unit_ids,
        )
        for stage_relative_path in _shared_aggregate_stage_paths(data_files)
    )
    return AggregateDependencyMapV1(entries=entries)


def load_retained_stage_incremental_state(
    *,
    stage_root: Path,
    manifest: StageManifestV1,
) -> RetainedStageIncrementalState | None:
    """Load retained incremental metadata when the trusted stage exposes it."""

    data_files = manifest.data_files
    required_paths = (
        data_files.unit_contributions,
        data_files.output_ownership,
        data_files.aggregate_dependencies,
    )
    if any(path is None for path in required_paths):
        return None
    unit_contributions_path, output_ownership_path, aggregate_dependencies_path = (
        cast(str, data_files.unit_contributions),
        cast(str, data_files.output_ownership),
        cast(str, data_files.aggregate_dependencies),
    )
    try:
        unit_contributions = PersistedUnitContributionsV1.model_validate_json(
            _resolve_stage_file(
                stage_root=stage_root, stage_relative_path=unit_contributions_path
            ).read_text(encoding="utf-8"),
        )
        output_ownership = OutputOwnershipMapV1.model_validate_json(
            _resolve_stage_file(
                stage_root=stage_root, stage_relative_path=output_ownership_path
            ).read_text(encoding="utf-8"),
        )
        aggregate_dependencies = AggregateDependencyMapV1.model_validate_json(
            _resolve_stage_file(
                stage_root=stage_root, stage_relative_path=aggregate_dependencies_path
            ).read_text(encoding="utf-8"),
        )
    except Exception:
        return None
    return RetainedStageIncrementalState(
        unit_contributions=unit_contributions,
        output_ownership=output_ownership,
        aggregate_dependencies=aggregate_dependencies,
    )


def _resolve_stage_file(*, stage_root: Path, stage_relative_path: str) -> Path:
    raw_candidate = stage_root / Path(stage_relative_path)
    candidate = raw_candidate.resolve(strict=False)
    normalized_stage_root = stage_root.resolve(strict=False)
    if (
        not candidate.is_relative_to(normalized_stage_root)
        or not candidate.is_file()
        or path_resolves_through_symlink(raw_candidate)
    ):
        raise ValueError(f"Invalid retained stage metadata path: {stage_relative_path}")
    return candidate


def _coordinator_owned_stage_paths(
    data_files: StageDataFiles,
) -> tuple[StageRelativePath, ...]:
    return tuple(
        (
            *_shared_aggregate_stage_paths(data_files),
            *tuple(_internal_metadata_stage_paths(data_files)),
            StageRelativePath("manifest.json"),
        )
    )


def _shared_aggregate_stage_paths(
    data_files: StageDataFiles,
) -> tuple[StageRelativePath, ...]:
    aggregate_paths = (
        data_files.components,
        data_files.artifacts,
        data_files.routes,
        data_files.redirects,
        data_files.releases,
        data_files.candidates,
        data_files.refs,
        data_files.translations,
        data_files.compatibility,
        data_files.mounts,
        data_files.providers,
        data_files.content_index,
        data_files.diagnostics,
    )
    return tuple(path for path in aggregate_paths if path is not None)


def _internal_metadata_stage_paths(
    data_files: StageDataFiles,
) -> tuple[StageRelativePath, ...]:
    internal_paths = (
        data_files.unit_contributions,
        data_files.output_ownership,
        data_files.aggregate_dependencies,
    )
    return tuple(path for path in internal_paths if path is not None)
