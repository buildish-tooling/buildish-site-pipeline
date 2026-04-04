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

"""Focused tests for watch-loop coordination helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from apache_buildish_site_pipeline.commands.watch import (
    _coalesce_dirty_paths,
    _derive_watch_roots,
    _is_pipeline_owned_path,
    _load_trusted_stage,
)


class WatchInternalTests(unittest.TestCase):
    def test_load_trusted_stage_accepts_normal_visible_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            stage_root = workspace_root / "site/.stage"
            stage_root.mkdir(parents=True, exist_ok=True)
            _write_stage_manifest(stage_root)

            trusted_stage = _load_trusted_stage(stage_root)

        self.assertIsNotNone(trusted_stage)
        if trusted_stage is None:
            self.fail("expected trusted stage metadata")
        self.assertEqual(trusted_stage.stage_root, stage_root.resolve(strict=False))

    def test_load_trusted_stage_rejects_stage_root_with_symlinked_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            real_site_root = workspace_root / "real-site"
            stage_root = real_site_root / ".stage"
            stage_root.mkdir(parents=True, exist_ok=True)
            _write_stage_manifest(stage_root)
            (workspace_root / "site").symlink_to(real_site_root, target_is_directory=True)

            trusted_stage = _load_trusted_stage(workspace_root / "site/.stage")

        self.assertIsNone(trusted_stage)

    def test_load_trusted_stage_rejects_symlinked_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            stage_root = workspace_root / "site/.stage"
            stage_root.mkdir(parents=True, exist_ok=True)
            real_manifest = workspace_root / "manifest.json"
            _write_stage_manifest(real_manifest.parent, manifest_path=real_manifest)
            (stage_root / "manifest.json").symlink_to(real_manifest)

            trusted_stage = _load_trusted_stage(stage_root)

        self.assertIsNone(trusted_stage)

    def test_load_trusted_stage_rejects_nested_symlink_in_stage_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            stage_root = workspace_root / "site/.stage"
            stage_root.mkdir(parents=True, exist_ok=True)
            _write_stage_manifest(stage_root)
            content_root = stage_root / "content"
            content_root.mkdir(parents=True, exist_ok=True)
            real_page = workspace_root / "index.md"
            real_page.write_text("# hello\n", encoding="utf-8")
            (content_root / "index.md").symlink_to(real_page)

            trusted_stage = _load_trusted_stage(stage_root)

        self.assertIsNone(trusted_stage)

    def test_load_trusted_stage_rejects_unreadable_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            stage_root = workspace_root / "site/.stage"
            manifest_path = stage_root / "manifest.json"
            stage_root.mkdir(parents=True, exist_ok=True)
            _write_stage_manifest(stage_root)

            original_read_text = Path.read_text

            def _read_text(path: Path, *args, **kwargs):
                if path == manifest_path:
                    raise PermissionError("blocked")
                return original_read_text(path, *args, **kwargs)

            with mock.patch("pathlib.Path.read_text", autospec=True, side_effect=_read_text):
                trusted_stage = _load_trusted_stage(stage_root)

        self.assertIsNone(trusted_stage)

    def test_coalesce_dirty_paths_collapses_nested_bursts(self) -> None:
        repo_root = Path("/workspace")
        changed_paths = (
            repo_root / "components/runtime/docs/releases",
            repo_root / "components/runtime/docs/releases/4.0.0/index.md",
            repo_root / "site/components.yaml",
        )

        self.assertEqual(
            _coalesce_dirty_paths(changed_paths),
            (
                repo_root / "site/components.yaml",
                repo_root / "components/runtime/docs/releases",
            ),
        )

    def test_derive_watch_roots_keeps_workspace_root_for_topology_changes(self) -> None:
        repo_root = Path("/workspace")
        planning_roots = (
            repo_root / "components/runtime/docs",
            repo_root / "site/components.yaml",
        )

        self.assertEqual(_derive_watch_roots(repo_root=repo_root, planning_roots=planning_roots), (repo_root,))

    def test_pipeline_owned_path_detection_filters_stage_work_and_report_temps(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            stage_root = workspace_root / "site/.stage"
            work_root = workspace_root / "site/.site-pipeline-work"
            report_output = workspace_root / "watch-report.json"
            authored_path = workspace_root / "components/runtime/docs/index.md"

            self.assertTrue(
                _is_pipeline_owned_path(
                    path=stage_root / "manifest.json",
                    stage_root=stage_root,
                    work_root=work_root,
                    report_output=report_output,
                ),
            )
            self.assertTrue(
                _is_pipeline_owned_path(
                    path=work_root / "watch/cycle-000001/stage/manifest.json",
                    stage_root=stage_root,
                    work_root=work_root,
                    report_output=report_output,
                ),
            )
            self.assertTrue(
                _is_pipeline_owned_path(
                    path=workspace_root / ".watch-report.json.123.tmp",
                    stage_root=stage_root,
                    work_root=work_root,
                    report_output=report_output,
                ),
            )
            self.assertFalse(
                _is_pipeline_owned_path(
                    path=authored_path,
                    stage_root=stage_root,
                    work_root=work_root,
                    report_output=report_output,
                ),
            )


def _write_stage_manifest(stage_root: Path, *, manifest_path: Path | None = None) -> None:
    target_path = manifest_path if manifest_path is not None else stage_root / "manifest.json"
    target_path.write_text(
        '{"schemaVersion":1,"stageLayoutVersion":1,"generatedAt":"2026-04-03T18:00:00Z",'
        '"command":"build","frontMatterFormat":"yaml","aggregateFormat":"json",'
        '"roots":{"content":"content","static":"static","data":"data"},'
        '"dataFiles":{"components":"data/components.json","artifacts":"data/artifacts.json",'
        '"routes":"data/routes.json","redirects":"data/redirects.json"}}\n',
        encoding="utf-8",
    )