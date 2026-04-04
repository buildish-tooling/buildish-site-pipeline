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

"""Generate checked-in JSON Schema files for authored YAML documents.

The exported schemas are derived from the same Pydantic models that validate
``site/components.yaml`` and ``site/component.yaml``. Model docstrings and
``Field(description=...)`` metadata therefore become IDE hover text and schema
help, keeping Python model metadata as the single source of truth.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from apache_buildish_site_pipeline.models.base import SitePipelineBaseModel
from apache_buildish_site_pipeline.models.catalog import CatalogDocumentV1
from apache_buildish_site_pipeline.models.component_repository import ComponentRepositoryDocumentV1

_JSON_SCHEMA_DRAFT_202012 = "https://json-schema.org/draft/2020-12/schema"


@dataclass(frozen=True)
class AuthoredSchemaExport:
    """One checked-in authored-document schema export."""

    filename: str
    title: str
    model: type[SitePipelineBaseModel]


_AUTHORED_SCHEMA_EXPORTS = (
    AuthoredSchemaExport(
        filename="site-pipeline-catalog-v1.schema.json",
        title="Site Pipeline Catalog v1",
        model=CatalogDocumentV1,
    ),
    AuthoredSchemaExport(
        filename="site-pipeline-component-v1.schema.json",
        title="Site Pipeline Component Metadata v1",
        model=ComponentRepositoryDocumentV1,
    ),
)


def authored_schema_exports() -> tuple[AuthoredSchemaExport, ...]:
    """Return the authored YAML schema exports that should be checked in."""

    return _AUTHORED_SCHEMA_EXPORTS


def build_schema_document(export: AuthoredSchemaExport) -> dict[str, Any]:
    """Build one JSON Schema document for an authored YAML model."""

    schema = export.model.model_json_schema(by_alias=True)
    schema["$schema"] = _JSON_SCHEMA_DRAFT_202012
    schema["title"] = export.title
    return schema


def write_authored_schema_files(output_dir: Path) -> tuple[Path, ...]:
    """Write the checked-in authored YAML schema files to ``output_dir``."""

    output_dir.mkdir(parents=True, exist_ok=True)
    written_paths: list[Path] = []
    for export in authored_schema_exports():
        output_path = output_dir / export.filename
        output_path.write_text(json.dumps(build_schema_document(export), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written_paths.append(output_path)
    return tuple(written_paths)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m apache_buildish_site_pipeline.schema_export")
    parser.add_argument("--output-dir", default="schemas", help="Directory that should receive the generated JSON Schema files.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Generate the checked-in authored-document JSON Schema files."""

    args = _build_parser().parse_args(argv)
    for output_path in write_authored_schema_files(Path(args.output_dir)):
        print(output_path.as_posix())
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())