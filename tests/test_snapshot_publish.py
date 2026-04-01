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

"""Tests for snapshot publishing helpers."""

from __future__ import annotations

from contextlib import redirect_stdout
import datetime as dt
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import apache_buildish_site_pipeline.snapshot_publish as snapshot_publish

from tests.test_support import write_files


def _seed_snapshot_repo(repo_root: Path) -> None:
    write_files(
        repo_root,
        {
            "pyproject.toml": (
                "[project]\n"
                'name = "apache-buildish-site-pipeline"\n'
                'version = "0.1.0"\n'
            ),
            "README.md": "# Demo\n",
            "apache_buildish_site_pipeline/__init__.py": "__all__ = []\n",
        },
    )


class SnapshotPublishTest(unittest.TestCase):
    def _assert_main_out_dir(self, out_dir_arg: str, expected_out_dir: Path) -> None:
        stdout = io.StringIO()
        expected_repo_root = Path(snapshot_publish.__file__).resolve().parents[1]
        built_wheel = (expected_out_dir / "demo.whl").resolve()

        with patch(
            "apache_buildish_site_pipeline.snapshot_publish.build_snapshot_wheel",
            return_value=built_wheel,
        ) as build_mock, redirect_stdout(stdout):
            exit_code = snapshot_publish.main(["--out-dir", out_dir_arg])

        self.assertEqual(0, exit_code)
        build_mock.assert_called_once_with(expected_repo_root, expected_out_dir)
        self.assertIn("Built local snapshot wheel", stdout.getvalue())

    def test_format_snapshot_version_includes_git_revision(self) -> None:
        version = snapshot_publish.format_snapshot_version(
            "0.1.0",
            built_at=dt.datetime(2026, 4, 1, 12, 34, 56, tzinfo=dt.UTC),
            git_revision="ABC123def4567890",
        )

        self.assertEqual("0.1.0.dev20260401123456+gabc123def456", version)

    def test_format_snapshot_version_requires_timezone_aware_timestamp(self) -> None:
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            snapshot_publish.format_snapshot_version(
                "0.1.0",
                built_at=dt.datetime(2026, 4, 1, 12, 34, 56),
                git_revision="abc123",
            )

    def test_format_snapshot_version_uses_nogit_when_revision_normalizes_empty(self) -> None:
        version = snapshot_publish.format_snapshot_version(
            "0.1.0",
            built_at=dt.datetime(2026, 4, 1, 12, 34, 56, tzinfo=dt.UTC),
            git_revision="!!!",
        )

        self.assertEqual("0.1.0.dev20260401123456+nogit", version)

    def test_normalize_git_revision_returns_none_for_missing_input(self) -> None:
        self.assertIsNone(snapshot_publish._normalize_git_revision(None))

    def test_replace_project_version_rewrites_first_assignment(self) -> None:
        updated = snapshot_publish.replace_project_version(
            "[project]\nversion = \"0.1.0\"\nname = \"demo\"\n",
            "0.1.0.dev20260401123456+gabc123def456",
        )

        self.assertIn(
            'version = "0.1.0.dev20260401123456+gabc123def456"',
            updated,
        )

    def test_replace_project_version_requires_exactly_one_assignment(self) -> None:
        with self.assertRaisesRegex(ValueError, "exactly one"):
            snapshot_publish.replace_project_version("[project]\nname = \"demo\"\n", "0.2.0")

    def test_current_git_revision_returns_none_when_git_command_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "apache_buildish_site_pipeline.snapshot_publish._required_executable",
                return_value="git",
            ), patch(
                "apache_buildish_site_pipeline.snapshot_publish.subprocess.run",
                return_value=subprocess.CompletedProcess(["git"], 1, stdout="", stderr="boom"),
            ):
                revision = snapshot_publish._current_git_revision(Path(temp_dir))

        self.assertIsNone(revision)

    def test_current_git_revision_strips_successful_git_stdout(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "apache_buildish_site_pipeline.snapshot_publish._required_executable",
                return_value="git",
            ), patch(
                "apache_buildish_site_pipeline.snapshot_publish.subprocess.run",
                return_value=subprocess.CompletedProcess(
                    ["git"], 0, stdout="abc123def456\n", stderr=""
                ),
            ):
                revision = snapshot_publish._current_git_revision(Path(temp_dir))

        self.assertEqual("abc123def456", revision)

    def test_required_executable_raises_when_binary_is_missing(self) -> None:
        with patch("apache_buildish_site_pipeline.snapshot_publish.shutil.which", return_value=None):
            with self.assertRaisesRegex(FileNotFoundError, "uv"):
                snapshot_publish._required_executable("uv")

    def test_required_executable_returns_resolved_binary_path(self) -> None:
        with patch(
            "apache_buildish_site_pipeline.snapshot_publish.shutil.which",
            return_value="/usr/bin/uv",
        ):
            self.assertEqual("/usr/bin/uv", snapshot_publish._required_executable("uv"))

    def test_build_snapshot_wheel_writes_manifest_for_created_wheel(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            out_dir = Path(temp_dir) / "dist"
            _seed_snapshot_repo(repo_root)
            snapshot_version = "0.1.0.dev20260401123456+gabc123def456"
            wheel_name = f"apache_buildish_site_pipeline-{snapshot_version}-py3-none-any.whl"

            def _fake_run(command: list[str], *, cwd: Path, check: bool) -> subprocess.CompletedProcess[str]:
                self.assertEqual(["uv", "build", "--wheel", "--out-dir", str(out_dir)], command)
                self.assertTrue(check)
                self.assertTrue((cwd / "pyproject.toml").is_file())
                (out_dir / wheel_name).write_text("wheel\n", encoding="utf-8")
                return subprocess.CompletedProcess(command, 0)

            with patch(
                "apache_buildish_site_pipeline.snapshot_publish._required_executable",
                return_value="uv",
            ), patch(
                "apache_buildish_site_pipeline.snapshot_publish._current_git_revision",
                return_value="abc123def456",
            ), patch(
                "apache_buildish_site_pipeline.snapshot_publish.format_snapshot_version",
                return_value=snapshot_version,
            ), patch(
                "apache_buildish_site_pipeline.snapshot_publish.subprocess.run",
                side_effect=_fake_run,
            ):
                wheel_path = snapshot_publish.build_snapshot_wheel(repo_root, out_dir)

            self.assertEqual((out_dir / wheel_name).resolve(), wheel_path)
            manifest = json.loads((out_dir / "latest.json").read_text(encoding="utf-8"))
            self.assertEqual(snapshot_version, manifest["version"])
            self.assertEqual(wheel_name, manifest["wheel"])
            self.assertEqual(str(wheel_path), manifest["wheelPath"])
            self.assertEqual(
                f"apache-buildish-site-pipeline @ {wheel_path.as_uri()}",
                manifest["dependencySpec"],
            )

    def test_build_snapshot_wheel_rejects_when_no_new_wheel_is_created(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir) / "repo"
            out_dir = Path(temp_dir) / "dist"
            _seed_snapshot_repo(repo_root)

            with patch(
                "apache_buildish_site_pipeline.snapshot_publish._required_executable",
                return_value="uv",
            ), patch(
                "apache_buildish_site_pipeline.snapshot_publish._current_git_revision",
                return_value="abc123def456",
            ), patch(
                "apache_buildish_site_pipeline.snapshot_publish.format_snapshot_version",
                return_value="0.1.0.dev20260401123456+gabc123def456",
            ), patch(
                "apache_buildish_site_pipeline.snapshot_publish.subprocess.run",
                return_value=subprocess.CompletedProcess(["uv"], 0),
            ):
                with self.assertRaisesRegex(RuntimeError, "exactly one new wheel"):
                    snapshot_publish.build_snapshot_wheel(repo_root, out_dir)

    def test_main_resolves_relative_out_dir_beneath_repo_root(self) -> None:
        expected_repo_root = Path(snapshot_publish.__file__).resolve().parents[1]
        self._assert_main_out_dir(
            "dist/snapshots",
            (expected_repo_root / "dist" / "snapshots").resolve(),
        )

    def test_main_preserves_absolute_out_dir(self) -> None:
        expected_repo_root = Path(snapshot_publish.__file__).resolve().parents[1]
        absolute_out_dir = (expected_repo_root / "dist" / "snapshots").resolve()
        self._assert_main_out_dir(str(absolute_out_dir), absolute_out_dir)