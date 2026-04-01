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

"""Tests for config resolution and config-driven build behavior."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import apache_buildish_site_pipeline as site_pipeline
from apache_buildish_site_pipeline.config import resolve_pipeline_config

from tests.test_support import catalog_defaults
from tests.test_support import catalog_payload
from tests.test_support import dump_yaml
from tests.test_support import text_block
from tests.test_support import write_files


class BuildWorkspaceConfigTest(unittest.TestCase):
    def test_build_reads_workspace_paths_from_config_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            repo_root = workspace / "consumer"
            dump_yaml(
                repo_root / "site" / "site-pipeline.yaml",
                {
                    "schemaVersion": 1,
                    "workspace": {
                        "authoredSiteContentPath": "docs-src",
                        "stagePath": "build/site-stage",
                        "previewPath": "build/site-preview",
                    },
                },
            )
            dump_yaml(
                repo_root / "site" / "components.yaml",
                catalog_payload(
                    {"slug": "mammoth-cache", "localDir": "mammoth-cache"},
                    defaults=catalog_defaults(),
                ),
            )
            write_files(
                repo_root,
                {
                    "docs-src/_index.md": text_block(
                        """
                        # Root

                        Consumer overview.
                        """
                    )
                },
            )
            write_files(
                workspace / "mammoth-cache",
                {
                    "site/pages/_index.md": text_block("""
                    # Overview

                    Landing page.
                    """),
                    "site/docs/_index.md": text_block("""
                    # Docs

                    Hello.
                    """),
                },
            )
            dump_yaml(
                workspace / "mammoth-cache" / "site" / "component.yaml",
                {"schemaVersion": 1, "component": {"displayName": "Mammoth Cache"}},
            )

            results = site_pipeline.build(repo_root)

            self.assertEqual("/components/mammoth-cache/", results[0].raw_component_index_path)
            self.assertEqual(
                "/components/mammoth-cache/development/",
                results[0].raw_development_index_path,
            )
            self.assertTrue((repo_root / "build" / "site-stage" / "manifest.yaml").is_file())
            self.assertTrue((repo_root / "build" / "site-preview" / "index.html").is_file())


class ResolvePipelineConfigTest(unittest.TestCase):
    def test_prefers_explicit_workspace_paths_over_config_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "consumer"
            (repo_root / "site" / "catalogs").mkdir(parents=True)
            dump_yaml(
                repo_root / "site" / "site-pipeline.yaml",
                {
                    "schemaVersion": 1,
                    "workspace": {
                        "catalogPath": "site/catalogs/from-config.yaml",
                        "authoredSiteContentPath": "site/content-from-config",
                        "stagePath": "build/stage-from-config",
                        "previewPath": "build/preview-from-config",
                    },
                },
            )
            dump_yaml(
                repo_root / "site" / "catalogs" / "from-config.yaml",
                catalog_payload(),
            )
            dump_yaml(
                repo_root / "site" / "catalogs" / "from-cli.yaml",
                catalog_payload(),
            )

            resolved = resolve_pipeline_config(
                repo_root,
                catalog_path="site/catalogs/from-cli.yaml",
                authored_site_content_path="site/content-from-cli",
                stage_path="build/stage-from-cli",
                preview_path="build/preview-from-cli",
            )

            self.assertEqual(
                (repo_root / "site" / "catalogs" / "from-cli.yaml").resolve(),
                resolved.catalog_path,
            )
            self.assertEqual(
                (repo_root / "site" / "content-from-cli").resolve(),
                resolved.authored_site_content_path,
            )
            self.assertEqual(
                (repo_root / "build" / "stage-from-cli").resolve(),
                resolved.stage_path,
            )
            self.assertEqual(
                (repo_root / "build" / "preview-from-cli").resolve(),
                resolved.preview_path,
            )

    def test_uses_site_settings_from_config_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "consumer"
            (repo_root / "site" / "catalogs").mkdir(parents=True)
            dump_yaml(
                repo_root / "site" / "site-pipeline.yaml",
                {
                    "schemaVersion": 1,
                    "workspace": {"catalogPath": "site/catalogs/components.yaml"},
                    "site": {
                        "siteTitle": "Example Buildish",
                        "projectStatus": "retired",
                    },
                },
            )
            dump_yaml(
                repo_root / "site" / "catalogs" / "components.yaml",
                catalog_payload(),
            )

            resolved = resolve_pipeline_config(repo_root)

            self.assertEqual("Example Buildish", resolved.site_title)
            self.assertEqual("retired", resolved.project_status)

    def test_reads_missing_components_policy_from_config_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "consumer"
            (repo_root / "site").mkdir(parents=True)
            dump_yaml(
                repo_root / "site" / "site-pipeline.yaml",
                {
                    "schemaVersion": 1,
                    "site": {"missingComponents": "fail"},
                },
            )
            dump_yaml(repo_root / "site" / "components.yaml", catalog_payload())

            resolved = resolve_pipeline_config(repo_root)

            self.assertEqual("fail", resolved.missing_components)

    def test_prefers_cli_missing_components_policy_over_config_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "consumer"
            (repo_root / "site").mkdir(parents=True)
            dump_yaml(
                repo_root / "site" / "site-pipeline.yaml",
                {
                    "schemaVersion": 1,
                    "site": {"missingComponents": "fail"},
                },
            )
            dump_yaml(repo_root / "site" / "components.yaml", catalog_payload())

            resolved = resolve_pipeline_config(repo_root, missing_components="skip")

            self.assertEqual("skip", resolved.missing_components)