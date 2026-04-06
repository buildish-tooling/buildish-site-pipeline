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

"""Generate checked-in JSON Schema files and reference docs for public contracts.

The exported artifacts are derived from the same Pydantic models that validate
or emit the pipeline's public file contracts. Model docstrings,
``Field(description=...)`` metadata, and typed reference-doc annotations
therefore stay as the single source of truth for both machine-readable schemas
and human-readable reference output.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any, Literal

from pydantic import Field, TypeAdapter, create_model

from apache_buildish_site_pipeline.models.documentation import ContractDocumentation, contract_documentation_for
from apache_buildish_site_pipeline.models.enums import DocumentFormat
from apache_buildish_site_pipeline.models.loading import (
    load_component_metadata_document,
    load_provider_snapshot_document,
    load_site_catalog_document,
)
from apache_buildish_site_pipeline.models.emitted.aggregates import (
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
from apache_buildish_site_pipeline.models.base import SitePipelineBaseModel
from apache_buildish_site_pipeline.models.authored.component_metadata import (
    ComponentMetadataDocumentV1,
)
from apache_buildish_site_pipeline.models.authored.site_catalog import SiteCatalogDocumentV1
from apache_buildish_site_pipeline.models.emitted.planning_stage_contract import (
    CheckReportV1,
    PipelineDiagnosticEntry,
    ResolvedMaterializationReportV1,
    StageManifestV1,
    StageRunReportV1,
)
from apache_buildish_site_pipeline.models.emitted.staged_front_matter import (
    PipelineFrontMatterNamespace,
)
from apache_buildish_site_pipeline.models.provider.provider_snapshot import ProviderSnapshotDocumentV1
from apache_buildish_site_pipeline.staging.incremental_metadata import (
    AggregateDependencyMapV1,
    OutputOwnershipMapV1,
    PersistedUnitContributionsV1,
)

_JSON_SCHEMA_DRAFT_202012 = "https://json-schema.org/draft/2020-12/schema"
_PUBLISHED_SCHEMA_BASE_URL = (
    "https://buildish.apache.org/components/site-pipeline/schemas"
)
_GENERATED_COMMENT = "Generated from the Site Pipeline Pydantic models. Do not edit by hand; regenerate with `make schemas`."

SchemaBuilder = Callable[[], dict[str, Any]]
ExampleValueBuilder = Callable[[], object]
ExampleRenderFormat = Literal["json", "yaml"]


@dataclass(frozen=True)
class SchemaExample:
    """One generated example shared by schema files and reference docs."""

    summary: str
    value_builder: ExampleValueBuilder
    render_format: ExampleRenderFormat = "json"


@dataclass(frozen=True)
class SchemaExport:
    """One checked-in JSON Schema export for a public file contract."""

    filename: str
    title: str
    schema_builder: SchemaBuilder
    description: str | None = None
    documentation: ContractDocumentation | None = None
    reference_roots: tuple[type[SitePipelineBaseModel], ...] = ()
    examples: tuple[SchemaExample, ...] = ()


def _model_schema(model: type[SitePipelineBaseModel]) -> SchemaBuilder:
    def build() -> dict[str, Any]:
        return model.model_json_schema(by_alias=True)

    return build


def _items_file_schema(
    *, model_name: str, item_model: type[SitePipelineBaseModel], items_description: str
) -> SchemaBuilder:
    def build() -> dict[str, Any]:
        item_schema = item_model.model_json_schema(by_alias=True)
        defs = item_schema.pop("$defs", None)
        file_model = create_model(
            model_name,
            __base__=SitePipelineBaseModel,
            items=(list[Any], Field(description=items_description)),
        )
        schema = file_model.model_json_schema(by_alias=True)
        schema["properties"]["items"]["items"] = item_schema
        if defs is not None:
            schema["$defs"] = defs
        return schema

    return build


def _list_schema(annotation: Any) -> SchemaBuilder:
    def build() -> dict[str, Any]:
        return TypeAdapter(annotation).json_schema(by_alias=True)

    return build


def _pipeline_file_documentation(*, summary: str, file_path: str) -> ContractDocumentation:
    """Build documentation metadata for a pipeline-emitted file contract."""

    return ContractDocumentation(
        category="emitted",
        ownership="pipeline-derived",
        summary=summary,
        file_path=file_path,
    )


def _serialize_example_value(value: object) -> object:
    """Convert typed example payloads into JSON-serializable data."""

    if isinstance(value, SitePipelineBaseModel):
        return value.model_dump(by_alias=True, exclude_none=True, mode="json")
    if isinstance(value, tuple):
        return [_serialize_example_value(item) for item in value]
    if isinstance(value, list):
        return [_serialize_example_value(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(f"Unsupported schema example payload type: {type(value)!r}")


def _catalog_example_document() -> SiteCatalogDocumentV1:
    """Return a realistic authored catalog example used in generated docs."""

    return load_site_catalog_document(
        (
            "schemaVersion: 1\n"
            "defaults:\n"
            "  docsRoot: docs\n"
            "  publication:\n"
            "    origin: docs\n"
            "site: {}\n"
            "origins:\n"
            "  docs:\n"
            "    baseUrl: https://docs.example.org\n"
            "sources:\n"
            "  runtime:\n"
            "    localDir: components/runtime\n"
            "components:\n"
            "  - slug: spark\n"
            "    weight: 100\n"
            "    content:\n"
            "      source: runtime\n"
            "    publication:\n"
            "      mountPath: /spark/\n"
            "    artifacts:\n"
            "      - key: runtime\n"
            "        source: runtime\n"
            "        versioning:\n"
            "          developmentRef: main\n"
            "          tagPattern: ^v.*$\n"
            "        publicationSelection:\n"
            "          development: true\n"
            "          lineHeads:\n"
            "            mode: allAuthored\n"
            "          releases:\n"
            "            mode: latestPerLine\n"
            "        lifecycle:\n"
            "          releaseLines:\n"
            "            - key: '4.0'\n"
            "              maintenanceRef: maintenance/4.0\n"
            "              latest: '4.0.0'\n"
            "          releases:\n"
            "            - version: '4.0.0'\n"
        ),
        document_format=DocumentFormat.YAML,
        source_name="site/catalog.yaml",
    )


def _component_metadata_example_document() -> ComponentMetadataDocumentV1:
    """Return a realistic component metadata example used in generated docs."""

    return load_component_metadata_document(
        (
            "schemaVersion: 1\n"
            "component:\n"
            "  slug: spark\n"
            "  displayName: Apache Spark\n"
            "content:\n"
            "  pagesRoot: site/pages\n"
            "  docsRoot: docs\n"
            "lifecycle:\n"
            "  latestStable: 4.0.0\n"
            "  supportStatusVocabulary:\n"
            "    active:\n"
            "      displayName: Active\n"
            "      order: 10\n"
        ),
        document_format=DocumentFormat.YAML,
        source_name="site/component.yaml",
    )


def _provider_snapshot_example_document() -> ProviderSnapshotDocumentV1:
    """Return a realistic provider snapshot example used in generated docs."""

    return load_provider_snapshot_document(
        (
            '{"schemaVersion":1,'
            '"providers":[{"key":"github-releases","type":"github","displayName":"GitHub Releases","baseUrl":"https://github.com/apache/spark","fetchedAt":"2026-04-03T18:00:00Z"}],'
            '"records":[{"provider":"github-releases","kind":"released","componentSlug":"spark","artifactKey":"runtime","externalId":"spark-4.0.0","version":"4.0.0","externalUrl":"https://github.com/apache/spark/releases/tag/v4.0.0","publishedAt":"2026-04-03T18:00:00Z","assets":[{"name":"spark-4.0.0-src.tgz","url":"https://downloads.apache.org/spark/spark-4.0.0-src.tgz","checksums":{"sha256":"abc123"}}]}]}'
        ),
        document_format=DocumentFormat.JSON,
        source_name="providers.json",
    )


_SCHEMA_EXPORTS = (
    SchemaExport(
        filename="site-pipeline-catalog-v1.schema.json",
        title="Site Pipeline Catalog v1",
        schema_builder=_model_schema(SiteCatalogDocumentV1),
        documentation=contract_documentation_for(SiteCatalogDocumentV1),
        reference_roots=(SiteCatalogDocumentV1,),
        examples=(
            SchemaExample(
                summary="Catalog with one component, one artifact, and release selection policy.",
                value_builder=_catalog_example_document,
                render_format="yaml",
            ),
        ),
    ),
    SchemaExport(
        filename="site-pipeline-component-v1.schema.json",
        title="Site Pipeline Component Metadata v1",
        schema_builder=_model_schema(ComponentMetadataDocumentV1),
        documentation=contract_documentation_for(ComponentMetadataDocumentV1),
        reference_roots=(ComponentMetadataDocumentV1,),
        examples=(
            SchemaExample(
                summary="Component metadata with identity, content roots, and lifecycle hints.",
                value_builder=_component_metadata_example_document,
                render_format="yaml",
            ),
        ),
    ),
    SchemaExport(
        filename="site-pipeline-provider-snapshot-v1.schema.json",
        title="Site Pipeline Provider Snapshot v1",
        schema_builder=_model_schema(ProviderSnapshotDocumentV1),
        documentation=contract_documentation_for(ProviderSnapshotDocumentV1),
        reference_roots=(ProviderSnapshotDocumentV1,),
        examples=(
            SchemaExample(
                summary="Provider snapshot with one released record and one downloadable asset.",
                value_builder=_provider_snapshot_example_document,
            ),
        ),
    ),
    SchemaExport(
        filename="site-pipeline-materialization-report-v1.schema.json",
        title="Site Pipeline Materialization Report v1",
        schema_builder=_model_schema(ResolvedMaterializationReportV1),
        documentation=contract_documentation_for(ResolvedMaterializationReportV1),
        reference_roots=(ResolvedMaterializationReportV1,),
    ),
    SchemaExport(
        filename="site-pipeline-check-report-v1.schema.json",
        title="Site Pipeline Check Report v1",
        schema_builder=_model_schema(CheckReportV1),
        documentation=contract_documentation_for(CheckReportV1),
        reference_roots=(CheckReportV1,),
    ),
    SchemaExport(
        filename="site-pipeline-stage-run-report-v1.schema.json",
        title="Site Pipeline Stage Run Report v1",
        schema_builder=_model_schema(StageRunReportV1),
        documentation=contract_documentation_for(StageRunReportV1),
        reference_roots=(StageRunReportV1,),
    ),
    SchemaExport(
        filename="site-pipeline-stage-manifest-v1.schema.json",
        title="Site Pipeline Stage Manifest v1",
        schema_builder=_model_schema(StageManifestV1),
        documentation=contract_documentation_for(StageManifestV1),
        reference_roots=(StageManifestV1,),
    ),
    SchemaExport(
        filename="site-pipeline-front-matter-namespace-v1.schema.json",
        title="Site Pipeline Front Matter Namespace v1",
        schema_builder=_model_schema(PipelineFrontMatterNamespace),
        documentation=contract_documentation_for(PipelineFrontMatterNamespace),
        reference_roots=(PipelineFrontMatterNamespace,),
    ),
    SchemaExport(
        filename="site-pipeline-components-data-v1.schema.json",
        title="Site Pipeline data/components.json v1",
        description="Public staged aggregate file at ``data/components.json``.",
        schema_builder=_items_file_schema(
            model_name="ComponentsDataFileV1",
            item_model=ComponentsDataEntry,
            items_description="Component aggregate entries emitted into `data/components.json`.",
        ),
        documentation=_pipeline_file_documentation(
            summary="Pipeline-emitted component aggregate file.",
            file_path="data/components.json",
        ),
        reference_roots=(ComponentsDataEntry,),
    ),
    SchemaExport(
        filename="site-pipeline-artifacts-data-v1.schema.json",
        title="Site Pipeline data/artifacts.json v1",
        description="Public staged aggregate file at ``data/artifacts.json``.",
        schema_builder=_items_file_schema(
            model_name="ArtifactsDataFileV1",
            item_model=ArtifactsDataEntry,
            items_description="Artifact aggregate entries emitted into `data/artifacts.json`.",
        ),
        documentation=_pipeline_file_documentation(
            summary="Pipeline-emitted artifact aggregate file.",
            file_path="data/artifacts.json",
        ),
        reference_roots=(ArtifactsDataEntry,),
    ),
    SchemaExport(
        filename="site-pipeline-routes-data-v1.schema.json",
        title="Site Pipeline data/routes.json v1",
        description="Public staged aggregate file at ``data/routes.json``.",
        schema_builder=_items_file_schema(
            model_name="RoutesDataFileV1",
            item_model=RouteAggregateEntry,
            items_description="Route aggregate entries emitted into `data/routes.json`.",
        ),
        documentation=_pipeline_file_documentation(
            summary="Pipeline-emitted route aggregate file.",
            file_path="data/routes.json",
        ),
        reference_roots=(RouteAggregateEntry,),
    ),
    SchemaExport(
        filename="site-pipeline-redirects-data-v1.schema.json",
        title="Site Pipeline data/redirects.json v1",
        description="Public staged aggregate file at ``data/redirects.json``.",
        schema_builder=_items_file_schema(
            model_name="RedirectsDataFileV1",
            item_model=RedirectAggregateEntry,
            items_description="Redirect aggregate entries emitted into `data/redirects.json`.",
        ),
        documentation=_pipeline_file_documentation(
            summary="Pipeline-emitted redirect aggregate file.",
            file_path="data/redirects.json",
        ),
        reference_roots=(RedirectAggregateEntry,),
    ),
    SchemaExport(
        filename="site-pipeline-providers-data-v1.schema.json",
        title="Site Pipeline data/providers.json v1",
        description="Public staged aggregate file at ``data/providers.json``.",
        schema_builder=_items_file_schema(
            model_name="ProvidersDataFileV1",
            item_model=ProvidersDataEntry,
            items_description="Provider summary entries emitted into `data/providers.json`.",
        ),
        documentation=_pipeline_file_documentation(
            summary="Pipeline-emitted provider summary aggregate file.",
            file_path="data/providers.json",
        ),
        reference_roots=(ProvidersDataEntry,),
    ),
    SchemaExport(
        filename="site-pipeline-releases-data-v1.schema.json",
        title="Site Pipeline data/releases.json v1",
        description="Public staged aggregate file at ``data/releases.json``.",
        schema_builder=_items_file_schema(
            model_name="ReleasesDataFileV1",
            item_model=ReleaseAggregateEntry,
            items_description="Released-version aggregate entries emitted into `data/releases.json`.",
        ),
        documentation=_pipeline_file_documentation(
            summary="Pipeline-emitted release aggregate file.",
            file_path="data/releases.json",
        ),
        reference_roots=(ReleaseAggregateEntry,),
    ),
    SchemaExport(
        filename="site-pipeline-candidates-data-v1.schema.json",
        title="Site Pipeline data/candidates.json v1",
        description="Public staged aggregate file at ``data/candidates.json``.",
        schema_builder=_items_file_schema(
            model_name="CandidatesDataFileV1",
            item_model=CandidateAggregateEntry,
            items_description="Candidate-version aggregate entries emitted into `data/candidates.json`.",
        ),
        documentation=_pipeline_file_documentation(
            summary="Pipeline-emitted candidate aggregate file.",
            file_path="data/candidates.json",
        ),
        reference_roots=(CandidateAggregateEntry,),
    ),
    SchemaExport(
        filename="site-pipeline-refs-data-v1.schema.json",
        title="Site Pipeline data/refs.json v1",
        description="Public staged aggregate file at ``data/refs.json``.",
        schema_builder=_items_file_schema(
            model_name="RefsDataFileV1",
            item_model=RefAggregateEntry,
            items_description="Named-ref aggregate entries emitted into `data/refs.json`.",
        ),
        documentation=_pipeline_file_documentation(
            summary="Pipeline-emitted named-ref aggregate file.",
            file_path="data/refs.json",
        ),
        reference_roots=(RefAggregateEntry,),
    ),
    SchemaExport(
        filename="site-pipeline-translations-data-v1.schema.json",
        title="Site Pipeline data/translations.json v1",
        description="Public staged aggregate file at ``data/translations.json``.",
        schema_builder=_items_file_schema(
            model_name="TranslationsDataFileV1",
            item_model=TranslationSetAggregateEntry,
            items_description="Translation-set aggregate entries emitted into `data/translations.json`.",
        ),
        documentation=_pipeline_file_documentation(
            summary="Pipeline-emitted translation aggregate file.",
            file_path="data/translations.json",
        ),
        reference_roots=(TranslationSetAggregateEntry,),
    ),
    SchemaExport(
        filename="site-pipeline-compatibility-data-v1.schema.json",
        title="Site Pipeline data/compatibility.json v1",
        description="Public staged aggregate file at ``data/compatibility.json``.",
        schema_builder=_items_file_schema(
            model_name="CompatibilityDataFileV1",
            item_model=CompatibilityAggregateEntry,
            items_description="Compatibility aggregate entries emitted into `data/compatibility.json`.",
        ),
        documentation=_pipeline_file_documentation(
            summary="Pipeline-emitted compatibility aggregate file.",
            file_path="data/compatibility.json",
        ),
        reference_roots=(CompatibilityAggregateEntry,),
    ),
    SchemaExport(
        filename="site-pipeline-mounts-data-v1.schema.json",
        title="Site Pipeline data/mounts.json v1",
        description="Public staged aggregate file at ``data/mounts.json``.",
        schema_builder=_items_file_schema(
            model_name="MountsDataFileV1",
            item_model=MountAggregateEntry,
            items_description="Mount aggregate entries emitted into `data/mounts.json`.",
        ),
        documentation=_pipeline_file_documentation(
            summary="Pipeline-emitted mount aggregate file.",
            file_path="data/mounts.json",
        ),
        reference_roots=(MountAggregateEntry,),
    ),
    SchemaExport(
        filename="site-pipeline-content-index-data-v1.schema.json",
        title="Site Pipeline data/content-index.json v1",
        description="Public staged aggregate file at ``data/content-index.json``.",
        schema_builder=_items_file_schema(
            model_name="ContentIndexDataFileV1",
            item_model=ContentIndexEntry,
            items_description="Content-index entries emitted into `data/content-index.json`.",
        ),
        documentation=_pipeline_file_documentation(
            summary="Pipeline-emitted content index file.",
            file_path="data/content-index.json",
        ),
        reference_roots=(ContentIndexEntry,),
    ),
    SchemaExport(
        filename="site-pipeline-diagnostics-data-v1.schema.json",
        title="Site Pipeline data/diagnostics.json v1",
        description="Public staged diagnostics file at ``data/diagnostics.json``.",
        schema_builder=_list_schema(list[PipelineDiagnosticEntry]),
        documentation=_pipeline_file_documentation(
            summary="Pipeline-emitted diagnostics file.",
            file_path="data/diagnostics.json",
        ),
        reference_roots=(PipelineDiagnosticEntry,),
    ),
    SchemaExport(
        filename="site-pipeline-unit-contributions-v1.schema.json",
        title="Site Pipeline data/_pipeline/unit-contributions.json v1",
        schema_builder=_model_schema(PersistedUnitContributionsV1),
        documentation=contract_documentation_for(PersistedUnitContributionsV1),
        reference_roots=(PersistedUnitContributionsV1,),
    ),
    SchemaExport(
        filename="site-pipeline-output-ownership-v1.schema.json",
        title="Site Pipeline data/_pipeline/output-ownership.json v1",
        schema_builder=_model_schema(OutputOwnershipMapV1),
        documentation=contract_documentation_for(OutputOwnershipMapV1),
        reference_roots=(OutputOwnershipMapV1,),
    ),
    SchemaExport(
        filename="site-pipeline-aggregate-dependencies-v1.schema.json",
        title="Site Pipeline data/_pipeline/aggregate-dependencies.json v1",
        schema_builder=_model_schema(AggregateDependencyMapV1),
        documentation=contract_documentation_for(AggregateDependencyMapV1),
        reference_roots=(AggregateDependencyMapV1,),
    ),
)


def schema_exports() -> tuple[SchemaExport, ...]:
    """Return the checked-in schema exports for public file contracts."""

    return _SCHEMA_EXPORTS


def authored_schema_exports() -> tuple[SchemaExport, ...]:
    """Return the authored schema exports kept for local YAML authoring."""

    return tuple(export for export in _SCHEMA_EXPORTS[:2])


def build_schema_document(export: SchemaExport) -> dict[str, Any]:
    """Build one finalized JSON Schema document for a public file contract."""

    schema = export.schema_builder()
    schema["$schema"] = _JSON_SCHEMA_DRAFT_202012
    schema["$id"] = f"{_PUBLISHED_SCHEMA_BASE_URL}/{export.filename}"
    schema["$comment"] = _GENERATED_COMMENT
    schema["title"] = export.title
    if export.description is not None:
        schema["description"] = export.description
    if export.documentation is not None:
        schema["x-buildish-contract"] = export.documentation.as_schema_extension()
    if export.examples:
        schema["examples"] = [
            _serialize_example_value(example.value_builder()) for example in export.examples
        ]
    return schema


def write_schema_files(output_dir: Path) -> tuple[Path, ...]:
    """Write the checked-in JSON Schema files to ``output_dir``."""

    output_dir.mkdir(parents=True, exist_ok=True)
    written_paths: list[Path] = []
    for export in schema_exports():
        output_path = output_dir / export.filename
        output_path.write_text(
            json.dumps(build_schema_document(export), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        written_paths.append(output_path)
    return tuple(written_paths)


def write_authored_schema_files(output_dir: Path) -> tuple[Path, ...]:
    """Backward-compatible alias for the full public schema export set."""

    return write_schema_files(output_dir)


def write_reference_file(output_path: Path) -> Path:
    """Write the generated Markdown schema reference document."""

    from apache_buildish_site_pipeline.reference_export import write_reference_markdown_file

    return write_reference_markdown_file(output_path, schema_exports())


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m apache_buildish_site_pipeline.schema_export"
    )
    parser.add_argument(
        "--output-dir",
        default="schemas",
        help="Directory that should receive the generated JSON Schema files.",
    )
    parser.add_argument(
        "--reference-output",
        default="docs/reference/pipeline-model-schema-reference.md",
        help="Path that should receive the generated Markdown schema reference.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Generate the checked-in JSON Schema files and Markdown reference docs."""

    args = _build_parser().parse_args(argv)
    for output_path in write_schema_files(Path(args.output_dir)):
        sys.stdout.write(output_path.as_posix())  # noqa: TID251
        sys.stdout.write("\n")  # noqa: TID251
    reference_path = write_reference_file(Path(args.reference_output))
    sys.stdout.write(reference_path.as_posix())  # noqa: TID251
    sys.stdout.write("\n")  # noqa: TID251
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
