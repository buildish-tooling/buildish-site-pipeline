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

"""Tests for generated JSON Schema exports."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from apache_buildish_site_pipeline.schema_export import schema_exports, write_schema_files


class SchemaExportTests(unittest.TestCase):
    """Verify the checked-in schema export workflow."""

    def test_generated_schema_uses_model_metadata_and_canonical_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            write_schema_files(Path(tempdir))
            catalog_schema = json.loads((Path(tempdir) / "site-pipeline-catalog-v1.schema.json").read_text(encoding="utf-8"))
            component_schema = json.loads((Path(tempdir) / "site-pipeline-component-v1.schema.json").read_text(encoding="utf-8"))
            manifest_schema = json.loads((Path(tempdir) / "site-pipeline-stage-manifest-v1.schema.json").read_text(encoding="utf-8"))
            components_data_schema = json.loads((Path(tempdir) / "site-pipeline-components-data-v1.schema.json").read_text(encoding="utf-8"))
            diagnostics_schema = json.loads((Path(tempdir) / "site-pipeline-diagnostics-data-v1.schema.json").read_text(encoding="utf-8"))

        self.assertEqual(catalog_schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(
            catalog_schema["$id"],
            "https://buildish.apache.org/components/site-pipeline/schemas/site-pipeline-catalog-v1.schema.json",
        )
        self.assertIn("Do not edit by hand", catalog_schema["$comment"])
        self.assertEqual(catalog_schema["description"], "Consumer-authored component catalog document.")
        self.assertEqual(catalog_schema["properties"]["schemaVersion"]["description"], "Schema version for the catalog format.")
        self.assertEqual(
            catalog_schema["$defs"]["ComponentCatalogEntry"]["properties"]["weight"]["description"],
            "Optional ordering hint for component listings, menus, and other consumer-rendered component collections.",
        )
        self.assertEqual(component_schema["description"], "Component-owned metadata from ``site/component.yaml``.")
        self.assertEqual(component_schema["properties"]["component"]["description"], "Stable identity for the component repository.")
        self.assertEqual(manifest_schema["title"], "Site Pipeline Stage Manifest v1")
        self.assertEqual(components_data_schema["description"], "Public staged aggregate file at ``data/components.json``.")
        self.assertEqual(components_data_schema["properties"]["items"]["type"], "array")
        self.assertEqual(diagnostics_schema["description"], "Public staged diagnostics file at ``data/diagnostics.json``.")
        self.assertEqual(diagnostics_schema["type"], "array")

    def test_export_inventory_covers_inputs_and_outputs(self) -> None:
        export_names = {export.filename for export in schema_exports()}

        self.assertIn("site-pipeline-provider-snapshot-v1.schema.json", export_names)
        self.assertIn("site-pipeline-stage-manifest-v1.schema.json", export_names)
        self.assertIn("site-pipeline-components-data-v1.schema.json", export_names)
        self.assertIn("site-pipeline-unit-contributions-v1.schema.json", export_names)
        self.assertIn("site-pipeline-front-matter-namespace-v1.schema.json", export_names)
        self.assertGreaterEqual(len(export_names), 20)

    def test_checked_in_schema_files_match_generated_output(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            generated_dir = Path(tempdir)
            write_schema_files(generated_dir)
            checked_in_dir = Path(__file__).resolve().parents[2] / "schemas"

            self.assertEqual(
                sorted(path.name for path in checked_in_dir.glob("*.json")),
                sorted(export.filename for export in schema_exports()),
            )

            for name in [export.filename for export in schema_exports()]:
                self.assertEqual(
                    json.loads((checked_in_dir / name).read_text(encoding="utf-8")),
                    json.loads((generated_dir / name).read_text(encoding="utf-8")),
                )


if __name__ == "__main__":
    unittest.main()