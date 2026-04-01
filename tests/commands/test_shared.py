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

"""Direct coverage for workspace-loading command helpers."""

from __future__ import annotations

import unittest

from buildish_site_pipeline.cli.errors import InputDiagnosticError
from buildish_site_pipeline.commands.shared import load_workspace_inputs

from tests.support.workspace import _workspace


def _set_default_metadata_file(workspace_root, metadata_file: str) -> None:
    catalog_path = workspace_root / "site/catalog.yaml"
    catalog = catalog_path.read_text(encoding="utf-8")
    catalog = catalog.replace(
        "defaults:\n",
        f"defaults:\n  metadataFile: {metadata_file}\n",
        1,
    )
    catalog_path.write_text(catalog, encoding="utf-8")


class SharedWorkspaceLoadingTests(unittest.TestCase):
    def test_missing_catalog_document_raises_input_diagnostic(self) -> None:
        with _workspace() as workspace_root:
            (workspace_root / "site/catalog.yaml").unlink()

            with self.assertRaises(InputDiagnosticError) as raised:
                load_workspace_inputs(workspace_root=workspace_root)

        self.assertEqual(raised.exception.diagnostic.code, "input-not-found")
        self.assertIn("Catalog document does not exist", str(raised.exception))

    def test_missing_provider_snapshot_returns_empty_default_snapshot(self) -> None:
        with _workspace() as workspace_root:
            (workspace_root / "site/provider-snapshot.json").unlink()

            loaded = load_workspace_inputs(workspace_root=workspace_root)

        self.assertIsNone(loaded.provider_snapshot_path)
        self.assertEqual(loaded.provider_snapshot.providers, [])
        self.assertEqual(loaded.provider_snapshot.records, [])

    def test_multiple_default_provider_snapshots_are_rejected(self) -> None:
        with _workspace() as workspace_root:
            (workspace_root / "site/provider-snapshot.yaml").write_text(
                "schemaVersion: 1\nproviders: []\nrecords: []\n",
                encoding="utf-8",
            )

            with self.assertRaises(InputDiagnosticError) as raised:
                load_workspace_inputs(workspace_root=workspace_root)

        self.assertIn("multiple default provider snapshot files", str(raised.exception))

    def test_component_metadata_loads_from_resolved_named_source_binding(self) -> None:
        with _workspace() as workspace_root:
            _set_default_metadata_file(workspace_root, "site/component.yaml")
            metadata_path = workspace_root / "components/runtime/site/component.yaml"
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            metadata_path.write_text(
                "schemaVersion: 1\ncomponent:\n  slug: spark\n",
                encoding="utf-8",
            )

            loaded = load_workspace_inputs(workspace_root=workspace_root)

        self.assertIn("spark", loaded.component_documents)
        self.assertEqual(loaded.component_documents["spark"].component.slug, "spark")

    def test_component_metadata_path_must_stay_within_repository_root(self) -> None:
        with _workspace() as workspace_root:
            _set_default_metadata_file(workspace_root, "component.yaml")
            outside_metadata = workspace_root / "component.yaml"
            outside_metadata.write_text("schemaVersion: 1\n", encoding="utf-8")
            (workspace_root / "components/runtime/component.yaml").symlink_to(
                outside_metadata
            )

            with self.assertRaises(InputDiagnosticError) as raised:
                load_workspace_inputs(workspace_root=workspace_root)

        self.assertIn("escapes declared root", str(raised.exception))

    def test_component_metadata_file_requires_supported_document_format(self) -> None:
        with _workspace() as workspace_root:
            _set_default_metadata_file(workspace_root, "component.txt")
            (workspace_root / "components/runtime/component.txt").write_text(
                "schemaVersion: 1\n",
                encoding="utf-8",
            )

            with self.assertRaises(InputDiagnosticError) as raised:
                load_workspace_inputs(workspace_root=workspace_root)

        self.assertEqual(
            raised.exception.diagnostic.code,
            "input-format-unsupported",
        )
        self.assertIn(".json, .yaml, or .yml", str(raised.exception))
