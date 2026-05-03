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

"""Public staged aggregate file root models."""

from __future__ import annotations

from typing import ClassVar

from pydantic import Field

from ...docs.documentation import (
    ContractDocumentation,
    PipelineDerivedModel as SitePipelineBaseModel,
    SchemaExportSpecification,
)
from ..base import SitePipelineRootModel
from .aggregates import (
    ArtifactsDataEntry,
    CandidateAggregateEntry,
    CompatibilityAggregateEntry,
    ComponentsDataEntry,
    ContentIndexEntry,
    MountAggregateEntry,
    ProvidersDataEntry,
    RedirectAggregateEntry,
    RefAggregateEntry,
    ReleaseAggregateEntry,
    RouteAggregateEntry,
    TranslationSetAggregateEntry,
)
from .planning_stage_contract import PipelineDiagnosticEntry


def _aggregate_file_documentation(*, summary: str, file_path: str) -> ContractDocumentation:
    return ContractDocumentation(
        category="emitted",
        ownership="pipeline-derived",
        summary=summary,
        file_path=file_path,
    )


class ComponentsDataFileV1(SitePipelineBaseModel):
    """Public staged aggregate file at ``data/components.json``."""

    contract_documentation: ClassVar[ContractDocumentation] = _aggregate_file_documentation(
        summary="Published component inventory with resolved routes, origins, and artifact summaries.",
        file_path="data/components.json",
    )
    schema_export: ClassVar[SchemaExportSpecification] = SchemaExportSpecification(
        filename="components-data-v1.schema.json",
        title="Site Pipeline data/components.json v1",
        reference_roots=(ComponentsDataEntry,),
    )

    items: list[ComponentsDataEntry] = Field(
        description="Component aggregate entries emitted into `data/components.json`."
    )


class ArtifactsDataFileV1(SitePipelineBaseModel):
    """Public staged aggregate file at ``data/artifacts.json``."""

    contract_documentation: ClassVar[ContractDocumentation] = _aggregate_file_documentation(
        summary="Published artifact inventory with version discovery rules, lifecycle hints, and latest-version summaries.",
        file_path="data/artifacts.json",
    )
    schema_export: ClassVar[SchemaExportSpecification] = SchemaExportSpecification(
        filename="artifacts-data-v1.schema.json",
        title="Site Pipeline data/artifacts.json v1",
        reference_roots=(ArtifactsDataEntry,),
    )

    items: list[ArtifactsDataEntry] = Field(
        description="Artifact aggregate entries emitted into `data/artifacts.json`."
    )


class RoutesDataFileV1(SitePipelineBaseModel):
    """Public staged aggregate file at ``data/routes.json``."""

    contract_documentation: ClassVar[ContractDocumentation] = _aggregate_file_documentation(
        summary="Flat inventory of published routes with resolved URLs, labels, and ownership metadata.",
        file_path="data/routes.json",
    )
    schema_export: ClassVar[SchemaExportSpecification] = SchemaExportSpecification(
        filename="routes-data-v1.schema.json",
        title="Site Pipeline data/routes.json v1",
        reference_roots=(RouteAggregateEntry,),
    )

    items: list[RouteAggregateEntry] = Field(
        description="Route aggregate entries emitted into `data/routes.json`."
    )


class RedirectsDataFileV1(SitePipelineBaseModel):
    """Public staged aggregate file at ``data/redirects.json``."""

    contract_documentation: ClassVar[ContractDocumentation] = _aggregate_file_documentation(
        summary="Flat inventory of published redirects and their resolved destination URLs.",
        file_path="data/redirects.json",
    )
    schema_export: ClassVar[SchemaExportSpecification] = SchemaExportSpecification(
        filename="redirects-data-v1.schema.json",
        title="Site Pipeline data/redirects.json v1",
        reference_roots=(RedirectAggregateEntry,),
    )

    items: list[RedirectAggregateEntry] = Field(
        description="Redirect aggregate entries emitted into `data/redirects.json`."
    )


class ProvidersDataFileV1(SitePipelineBaseModel):
    """Public staged aggregate file at ``data/providers.json``."""

    contract_documentation: ClassVar[ContractDocumentation] = _aggregate_file_documentation(
        summary="Loaded provider inventory with display names, base URLs, and fetch timestamps.",
        file_path="data/providers.json",
    )
    schema_export: ClassVar[SchemaExportSpecification] = SchemaExportSpecification(
        filename="providers-data-v1.schema.json",
        title="Site Pipeline data/providers.json v1",
        reference_roots=(ProvidersDataEntry,),
    )

    items: list[ProvidersDataEntry] = Field(
        description="Provider summary entries emitted into `data/providers.json`."
    )


class ReleasesDataFileV1(SitePipelineBaseModel):
    """Public staged aggregate file at ``data/releases.json``."""

    contract_documentation: ClassVar[ContractDocumentation] = _aggregate_file_documentation(
        summary="Published released-version inventory with lifecycle, support, and asset metadata.",
        file_path="data/releases.json",
    )
    schema_export: ClassVar[SchemaExportSpecification] = SchemaExportSpecification(
        filename="releases-data-v1.schema.json",
        title="Site Pipeline data/releases.json v1",
        reference_roots=(ReleaseAggregateEntry,),
    )

    items: list[ReleaseAggregateEntry] = Field(
        description="Released-version aggregate entries emitted into `data/releases.json`."
    )


class CandidatesDataFileV1(SitePipelineBaseModel):
    """Public staged aggregate file at ``data/candidates.json``."""

    contract_documentation: ClassVar[ContractDocumentation] = _aggregate_file_documentation(
        summary="Published release-candidate inventory with vote status and downloadable assets.",
        file_path="data/candidates.json",
    )
    schema_export: ClassVar[SchemaExportSpecification] = SchemaExportSpecification(
        filename="candidates-data-v1.schema.json",
        title="Site Pipeline data/candidates.json v1",
        reference_roots=(CandidateAggregateEntry,),
    )

    items: list[CandidateAggregateEntry] = Field(
        description="Candidate-version aggregate entries emitted into `data/candidates.json`."
    )


class RefsDataFileV1(SitePipelineBaseModel):
    """Public staged aggregate file at ``data/refs.json``."""

    contract_documentation: ClassVar[ContractDocumentation] = _aggregate_file_documentation(
        summary="Published development, line-head, and named-ref inventory for version navigation.",
        file_path="data/refs.json",
    )
    schema_export: ClassVar[SchemaExportSpecification] = SchemaExportSpecification(
        filename="refs-data-v1.schema.json",
        title="Site Pipeline data/refs.json v1",
        reference_roots=(RefAggregateEntry,),
    )

    items: list[RefAggregateEntry] = Field(
        description="Named-ref aggregate entries emitted into `data/refs.json`."
    )


class TranslationsDataFileV1(SitePipelineBaseModel):
    """Public staged aggregate file at ``data/translations.json``."""

    contract_documentation: ClassVar[ContractDocumentation] = _aggregate_file_documentation(
        summary="Translation sibling groups keyed by one shared translation identifier.",
        file_path="data/translations.json",
    )
    schema_export: ClassVar[SchemaExportSpecification] = SchemaExportSpecification(
        filename="translations-data-v1.schema.json",
        title="Site Pipeline data/translations.json v1",
        reference_roots=(TranslationSetAggregateEntry,),
    )

    items: list[TranslationSetAggregateEntry] = Field(
        description="Translation-set aggregate entries emitted into `data/translations.json`."
    )


class CompatibilityDataFileV1(SitePipelineBaseModel):
    """Public staged aggregate file at ``data/compatibility.json``."""

    contract_documentation: ClassVar[ContractDocumentation] = _aggregate_file_documentation(
        summary="Declared compatibility relationships between published identities.",
        file_path="data/compatibility.json",
    )
    schema_export: ClassVar[SchemaExportSpecification] = SchemaExportSpecification(
        filename="compatibility-data-v1.schema.json",
        title="Site Pipeline data/compatibility.json v1",
        reference_roots=(CompatibilityAggregateEntry,),
    )

    items: list[CompatibilityAggregateEntry] = Field(
        description="Compatibility aggregate entries emitted into `data/compatibility.json`."
    )


class MountsDataFileV1(SitePipelineBaseModel):
    """Public staged aggregate file at ``data/mounts.json``."""

    contract_documentation: ClassVar[ContractDocumentation] = _aggregate_file_documentation(
        summary="Mounted content and asset subtrees published under resolved public paths.",
        file_path="data/mounts.json",
    )
    schema_export: ClassVar[SchemaExportSpecification] = SchemaExportSpecification(
        filename="mounts-data-v1.schema.json",
        title="Site Pipeline data/mounts.json v1",
        reference_roots=(MountAggregateEntry,),
    )

    items: list[MountAggregateEntry] = Field(
        description="Mount aggregate entries emitted into `data/mounts.json`."
    )


class ContentIndexDataFileV1(SitePipelineBaseModel):
    """Public staged aggregate file at ``data/content-index.json``."""

    contract_documentation: ClassVar[ContractDocumentation] = _aggregate_file_documentation(
        summary="Search and navigation index for staged pages with titles, ancestry, and version metadata.",
        file_path="data/content-index.json",
    )
    schema_export: ClassVar[SchemaExportSpecification] = SchemaExportSpecification(
        filename="content-index-data-v1.schema.json",
        title="Site Pipeline data/content-index.json v1",
        reference_roots=(ContentIndexEntry,),
    )

    items: list[ContentIndexEntry] = Field(
        description="Content-index entries emitted into `data/content-index.json`."
    )


class DiagnosticsDataFileV1(SitePipelineRootModel[list[PipelineDiagnosticEntry]]):
    """Public staged diagnostics file at ``data/diagnostics.json``."""

    contract_documentation: ClassVar[ContractDocumentation] = _aggregate_file_documentation(
        summary="Structured diagnostics emitted during planning, checking, or staging.",
        file_path="data/diagnostics.json",
    )
    schema_export: ClassVar[SchemaExportSpecification] = SchemaExportSpecification(
        filename="diagnostics-data-v1.schema.json",
        title="Site Pipeline data/diagnostics.json v1",
        reference_roots=(PipelineDiagnosticEntry,),
    )
