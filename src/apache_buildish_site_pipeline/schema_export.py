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

"""Generate checked-in JSON Schema files for public input and output contracts.

The exported schemas are derived from the same Pydantic models that validate or
emit the pipeline's public file contracts. Model docstrings and
``Field(description=...)`` metadata therefore become schema help text, keeping
Python model metadata as the single source of truth.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

from pydantic import Field, TypeAdapter, create_model

from apache_buildish_site_pipeline.models.aggregates import (
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
from apache_buildish_site_pipeline.models.catalog import CatalogDocumentV1
from apache_buildish_site_pipeline.models.component_repository import (
    ComponentRepositoryDocumentV1,
)
from apache_buildish_site_pipeline.models.planning_stage_contract import (
    CheckReportV1,
    PipelineDiagnosticEntry,
    ResolvedMaterializationReportV1,
    StageManifestV1,
    StageRunReportV1,
)
from apache_buildish_site_pipeline.models.provider_snapshot import ProviderSnapshotV1
from apache_buildish_site_pipeline.models.staged_front_matter import (
    PipelineFrontMatterNamespace,
)
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


@dataclass(frozen=True)
class SchemaExport:
    """One checked-in JSON Schema export for a public file contract."""

    filename: str
    title: str
    schema_builder: SchemaBuilder
    description: str | None = None


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


_SCHEMA_EXPORTS = (
    SchemaExport(
        filename="site-pipeline-catalog-v1.schema.json",
        title="Site Pipeline Catalog v1",
        schema_builder=_model_schema(CatalogDocumentV1),
    ),
    SchemaExport(
        filename="site-pipeline-component-v1.schema.json",
        title="Site Pipeline Component Metadata v1",
        schema_builder=_model_schema(ComponentRepositoryDocumentV1),
    ),
    SchemaExport(
        filename="site-pipeline-provider-snapshot-v1.schema.json",
        title="Site Pipeline Provider Snapshot v1",
        schema_builder=_model_schema(ProviderSnapshotV1),
    ),
    SchemaExport(
        filename="site-pipeline-materialization-report-v1.schema.json",
        title="Site Pipeline Materialization Report v1",
        schema_builder=_model_schema(ResolvedMaterializationReportV1),
    ),
    SchemaExport(
        filename="site-pipeline-check-report-v1.schema.json",
        title="Site Pipeline Check Report v1",
        schema_builder=_model_schema(CheckReportV1),
    ),
    SchemaExport(
        filename="site-pipeline-stage-run-report-v1.schema.json",
        title="Site Pipeline Stage Run Report v1",
        schema_builder=_model_schema(StageRunReportV1),
    ),
    SchemaExport(
        filename="site-pipeline-stage-manifest-v1.schema.json",
        title="Site Pipeline Stage Manifest v1",
        schema_builder=_model_schema(StageManifestV1),
    ),
    SchemaExport(
        filename="site-pipeline-front-matter-namespace-v1.schema.json",
        title="Site Pipeline Front Matter Namespace v1",
        schema_builder=_model_schema(PipelineFrontMatterNamespace),
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
    ),
    SchemaExport(
        filename="site-pipeline-diagnostics-data-v1.schema.json",
        title="Site Pipeline data/diagnostics.json v1",
        description="Public staged diagnostics file at ``data/diagnostics.json``.",
        schema_builder=_list_schema(list[PipelineDiagnosticEntry]),
    ),
    SchemaExport(
        filename="site-pipeline-unit-contributions-v1.schema.json",
        title="Site Pipeline data/_pipeline/unit-contributions.json v1",
        schema_builder=_model_schema(PersistedUnitContributionsV1),
    ),
    SchemaExport(
        filename="site-pipeline-output-ownership-v1.schema.json",
        title="Site Pipeline data/_pipeline/output-ownership.json v1",
        schema_builder=_model_schema(OutputOwnershipMapV1),
    ),
    SchemaExport(
        filename="site-pipeline-aggregate-dependencies-v1.schema.json",
        title="Site Pipeline data/_pipeline/aggregate-dependencies.json v1",
        schema_builder=_model_schema(AggregateDependencyMapV1),
    ),
)


def schema_exports() -> tuple[SchemaExport, ...]:
    """Return the checked-in schema exports for public file contracts."""

    return _SCHEMA_EXPORTS


def authored_schema_exports() -> tuple[SchemaExport, ...]:
    """Return the authored-input schema exports kept for local YAML authoring."""

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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m apache_buildish_site_pipeline.schema_export"
    )
    parser.add_argument(
        "--output-dir",
        default="schemas",
        help="Directory that should receive the generated JSON Schema files.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Generate the checked-in JSON Schema files for public file contracts."""

    args = _build_parser().parse_args(argv)
    for output_path in write_schema_files(Path(args.output_dir)):
        sys.stdout.write(output_path.as_posix())  # noqa: TID251
        sys.stdout.write("\n")  # noqa: TID251
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
