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

"""Unit tests for CLI argument parsing and dispatch."""

from __future__ import annotations

from contextlib import redirect_stdout
import io
import unittest
from unittest.mock import patch

from apache_buildish_site_pipeline import cli


WORKSPACE_REPO = "/workspace/repo"


class CliTest(unittest.TestCase):
    def _run_main_with_stdout(self, args: list[str]) -> tuple[int, str]:
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            exit_code = cli.main(args)

        return exit_code, stdout.getvalue()

    def test_parse_args_accepts_preview_command(self) -> None:
        args = cli.parse_args(["preview", "--port", "9000"])

        self.assertEqual("preview", args.command)
        self.assertEqual(9000, args.port)

    def test_parse_args_defaults_to_build_when_no_subcommand_is_given(self) -> None:
        args = cli.parse_args([])

        self.assertEqual("build", args.command)
        self.assertEqual(8000, args.port)
        self.assertGreater(args.debounce_ms, 0)

    def test_parse_args_accepts_missing_components_policy(self) -> None:
        args = cli.parse_args(["watch", "--missing-components", "fail"])

        self.assertEqual("watch", args.command)
        self.assertEqual("fail", args.missing_components)

    def test_main_build_command_prints_component_count(self) -> None:
        with patch(
            "apache_buildish_site_pipeline.cli.build",
            return_value=[object(), object()],
        ) as build_mock:
            exit_code, output = self._run_main_with_stdout(
                [
                    "build",
                    "--repo-root",
                    WORKSPACE_REPO,
                    "--catalog",
                    "site/catalogs/components.yaml",
                    "--site-title",
                    "Local Site",
                ]
            )

        self.assertEqual(0, exit_code)
        build_mock.assert_called_once_with(
            repo_root=WORKSPACE_REPO,
            config_path=None,
            catalog_path="site/catalogs/components.yaml",
            authored_site_content_path=None,
            stage_path=None,
            preview_path=None,
            site_title="Local Site",
            project_status=None,
            missing_components=None,
        )
        self.assertIn("Built 2 component(s)", output)

    def test_main_preview_command_passes_missing_components_policy(self) -> None:
        with patch("apache_buildish_site_pipeline.cli.preview") as preview_mock:
            exit_code = cli.main(
                [
                    "preview",
                    "--repo-root",
                    WORKSPACE_REPO,
                    "--missing-components",
                    "fail",
                ]
            )

        self.assertEqual(0, exit_code)
        preview_mock.assert_called_once_with(
            repo_root=WORKSPACE_REPO,
            port=8000,
            config_path=None,
            catalog_path=None,
            authored_site_content_path=None,
            stage_path=None,
            preview_path=None,
            site_title=None,
            project_status=None,
            missing_components="fail",
        )

    def test_main_clean_command_uses_workspace_overrides(self) -> None:
        with patch("apache_buildish_site_pipeline.cli.clean") as clean_mock:
            exit_code, output = self._run_main_with_stdout(
                [
                    "clean",
                    "--repo-root",
                    WORKSPACE_REPO,
                    "--config",
                    "site/site-pipeline.yaml",
                    "--authored-site-content",
                    "docs-src",
                    "--stage-path",
                    "build/stage",
                    "--preview-path",
                    "build/preview",
                ]
            )

        self.assertEqual(0, exit_code)
        clean_mock.assert_called_once_with(
            repo_root=WORKSPACE_REPO,
            config_path="site/site-pipeline.yaml",
            authored_site_content_path="docs-src",
            stage_path="build/stage",
            preview_path="build/preview",
        )
        self.assertIn("Removed generated outputs", output)

    def test_main_watch_command_passes_shared_options_and_policy(self) -> None:
        with patch("apache_buildish_site_pipeline.cli.watch_and_build") as watch_mock:
            exit_code = cli.main(
                [
                    "watch",
                    "--repo-root",
                    WORKSPACE_REPO,
                    "--catalog",
                    "site/catalogs/components.yaml",
                    "--debounce-ms",
                    "250",
                    "--site-title",
                    "Workspace Site",
                    "--project-status",
                    "graduated",
                    "--missing-components",
                    "fail",
                ]
            )

        self.assertEqual(0, exit_code)
        watch_mock.assert_called_once_with(
            repo_root=WORKSPACE_REPO,
            debounce_ms=250,
            config_path=None,
            catalog_path="site/catalogs/components.yaml",
            authored_site_content_path=None,
            stage_path=None,
            preview_path=None,
            site_title="Workspace Site",
            project_status="graduated",
            missing_components="fail",
        )