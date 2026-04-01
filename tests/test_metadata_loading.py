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

"""Tests for component metadata loading and filesystem helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from apache_buildish_site_pipeline.filesystem import load_component_metadata
from apache_buildish_site_pipeline.filesystem import repo_root_from

from tests.test_support import dump_yaml


class ComponentMetadataLoadingTest(unittest.TestCase):
    def test_load_component_metadata_returns_typed_models(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "mammoth-cache"
            dump_yaml(
                repo_root / "site" / "component.yaml",
                {
                    "schemaVersion": 1,
                    "component": {"displayName": "Mammoth Cache"},
                    "content": {"pagesRoot": "site/pages", "docsRoot": "site/docs"},
                    "versioning": {"developmentLabel": "Preview"},
                    "navigation": {"section": "components"},
                },
            )

            metadata, metadata_path = load_component_metadata(
                repo_root, "site/component.yaml", "mammoth-cache"
            )

            self.assertEqual(repo_root / "site" / "component.yaml", metadata_path)
            self.assertEqual("Mammoth Cache", metadata.component.display_name)
            self.assertEqual("site/pages", metadata.content.pages_root)
            self.assertEqual("Preview", metadata.versioning.development_label)
            self.assertEqual("components", metadata.navigation.section)

    def test_load_component_metadata_accepts_legacy_unreleased_label(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "mammoth-cache"
            dump_yaml(
                repo_root / "site" / "component.yaml",
                {"schemaVersion": 1, "versioning": {"unreleasedLabel": "Unreleased"}},
            )

            metadata, _ = load_component_metadata(
                repo_root, "site/component.yaml", "mammoth-cache"
            )

            self.assertEqual("Unreleased", metadata.versioning.development_label)

    def test_load_component_metadata_rejects_invalid_tag_pattern(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "mammoth-cache"
            dump_yaml(
                repo_root / "site" / "component.yaml",
                {"schemaVersion": 1, "versioning": {"tagPattern": "["}},
            )

            with self.assertRaisesRegex(ValueError, "Invalid YAML"):
                load_component_metadata(repo_root, "site/component.yaml", "mammoth-cache")

    def test_load_component_metadata_rejects_invalid_release_line_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "mammoth-cache"
            dump_yaml(
                repo_root / "site" / "component.yaml",
                {
                    "schemaVersion": 1,
                    "lifecycle": {
                        "releaseLines": [
                            {
                                "line": "v1",
                                "latest": "v1.2.3",
                                "status": "maintained",
                                "aliases": "stable",
                            }
                        ]
                    },
                },
            )

            with self.assertRaisesRegex(ValueError, "Invalid YAML"):
                load_component_metadata(repo_root, "site/component.yaml", "mammoth-cache")

    def test_load_component_metadata_rejects_null_nested_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "mammoth-cache"
            dump_yaml(
                repo_root / "site" / "component.yaml",
                {
                    "schemaVersion": 1,
                    "component": None,
                    "content": None,
                    "versioning": None,
                    "lifecycle": None,
                    "navigation": None,
                },
            )

            with self.assertRaisesRegex(ValueError, "Invalid YAML"):
                load_component_metadata(repo_root, "site/component.yaml", "mammoth-cache")


class FilesystemHelpersTest(unittest.TestCase):
    def test_repo_root_from_accepts_string_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "consumer"
            repo_root.mkdir()

            self.assertEqual(repo_root.resolve(), repo_root_from(str(repo_root)))