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

"""Direct coverage for visible-stage publication helpers."""

from __future__ import annotations

import io
import json
import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from buildish_site_pipeline.cli.errors import StageIntegrityError
from buildish_site_pipeline.cli.errors import RetainedStageError
from buildish_site_pipeline.cli import _run
from buildish_site_pipeline.staging.publication import (
    _collect_stage_tree_entries,
    _fsync_directory,
    _fsync_file,
    _replace_stage_root,
    _validate_candidate_stage_root,
    _validate_initial_stage_root,
    _validate_publication_filesystems,
    _validate_replaceable_stage_root,
    finalize_stage_publication,
    validate_materialized_stage_tree,
    validate_visible_stage_target_path,
)
from tests.support.workspace import _cwd, _workspace


class PublicationHelperTests(unittest.TestCase):
    def test_finalize_stage_publication_replaces_empty_placeholder_directory(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            candidate_root = self._stage_tree(root / "candidate")
            (candidate_root / "content/index.html").parent.mkdir(parents=True)
            (candidate_root / "content/index.html").write_text("ok\n", encoding="utf-8")
            stage_root = root / "public"
            stage_root.mkdir()

            published = finalize_stage_publication(
                candidate_stage_root=candidate_root,
                stage_root=stage_root,
            )

            self.assertEqual(published.stage_root, stage_root)
            self.assertTrue((stage_root / "manifest.json").is_file())
            self.assertTrue((stage_root / "content/index.html").is_file())
            self.assertFalse(candidate_root.exists())

    def test_validate_visible_stage_target_path_rejects_symlink_stage_root(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "real-stage"
            target.mkdir()
            stage_root = root / "public"
            stage_root.symlink_to(target, target_is_directory=True)

            with self.assertRaises(StageIntegrityError):
                validate_visible_stage_target_path(stage_root)

    def test_validate_materialized_stage_tree_wraps_os_errors(self) -> None:
        with patch("buildish_site_pipeline.staging.publication.os.walk") as walk:
            walk.side_effect = OSError("boom")

            with self.assertRaises(StageIntegrityError) as raised:
                validate_materialized_stage_tree(Path("/stage"))

        self.assertIn("Could not validate stage tree integrity", str(raised.exception))

    def test_validate_initial_stage_root_rejects_symlink(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "target"
            target.mkdir()
            stage_root = root / "public"
            stage_root.symlink_to(target, target_is_directory=True)

            with self.assertRaises(StageIntegrityError):
                _validate_initial_stage_root(stage_root)

    def test_validate_initial_stage_root_rejects_non_directory(self) -> None:
        with TemporaryDirectory() as temp_dir:
            stage_root = Path(temp_dir) / "public"
            stage_root.write_text("nope\n", encoding="utf-8")

            with self.assertRaises(StageIntegrityError):
                _validate_initial_stage_root(stage_root)

    def test_validate_initial_stage_root_rejects_non_empty_directory(self) -> None:
        with TemporaryDirectory() as temp_dir:
            stage_root = Path(temp_dir) / "public"
            stage_root.mkdir()
            (stage_root / "existing.txt").write_text("occupied\n", encoding="utf-8")

            with self.assertRaises(StageIntegrityError):
                _validate_initial_stage_root(stage_root)

    def test_validate_replaceable_stage_root_accepts_absent_stage_root(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            _validate_replaceable_stage_root(
                stage_root=root / "missing",
                candidate_stage_root=self._stage_tree(root / "candidate"),
            )

    def test_validate_replaceable_stage_root_rejects_non_directory_and_untrusted_tree(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            file_root = root / "file-stage"
            file_root.write_text("nope\n", encoding="utf-8")
            with self.assertRaises(StageIntegrityError):
                _validate_replaceable_stage_root(
                    stage_root=file_root,
                    candidate_stage_root=self._stage_tree(root / "candidate-a"),
                )

            stage_root = root / "public"
            stage_root.mkdir()
            with self.assertRaises(StageIntegrityError):
                _validate_replaceable_stage_root(
                    stage_root=stage_root,
                    candidate_stage_root=self._stage_tree(root / "candidate-b"),
                )

    def test_validate_replaceable_stage_root_rejects_symlink(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "real-stage"
            target.mkdir()
            stage_root = root / "public"
            stage_root.symlink_to(target, target_is_directory=True)

            with self.assertRaises(StageIntegrityError):
                _validate_replaceable_stage_root(
                    stage_root=stage_root,
                    candidate_stage_root=self._stage_tree(root / "candidate"),
                )

    def test_validate_replaceable_stage_root_allows_deleting_unit_owned_paths(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(argv=["build"], stdout=stdout, stderr=stderr)
            self.assertEqual(exit_code, 0)
            self.assertEqual(stderr.getvalue(), "")
            stage_root = workspace_root / "site/.stage"
            candidate_root = workspace_root / "candidate-stage"
            shutil.copytree(stage_root, candidate_root)
            shutil.rmtree(candidate_root / "content/spark")

            _validate_replaceable_stage_root(
                stage_root=stage_root,
                candidate_stage_root=candidate_root,
            )

    def test_validate_replaceable_stage_root_rejects_deleting_coordinator_owned_files(
        self,
    ) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(argv=["build"], stdout=stdout, stderr=stderr)
            self.assertEqual(exit_code, 0)
            self.assertEqual(stderr.getvalue(), "")
            stage_root = workspace_root / "site/.stage"
            candidate_root = workspace_root / "candidate-stage"
            shutil.copytree(stage_root, candidate_root)
            (candidate_root / "data/routes.json").unlink()

            with self.assertRaisesRegex(
                StageIntegrityError,
                "Visible stage replacement would delete paths with ambiguous ownership",
            ):
                _validate_replaceable_stage_root(
                    stage_root=stage_root,
                    candidate_stage_root=candidate_root,
                )

    def test_validate_candidate_stage_root_rejects_bad_directory_and_missing_manifest(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            file_root = root / "candidate-file"
            file_root.write_text("nope\n", encoding="utf-8")
            with self.assertRaises(StageIntegrityError):
                _validate_candidate_stage_root(file_root)

            candidate_root = root / "candidate-dir"
            candidate_root.mkdir()
            with self.assertRaises(StageIntegrityError):
                _validate_candidate_stage_root(candidate_root)

    def test_collect_stage_tree_entries_wraps_os_errors(self) -> None:
        with patch("buildish_site_pipeline.staging.publication.os.walk") as walk:
            walk.side_effect = OSError("boom")

            with self.assertRaises(StageIntegrityError) as raised:
                _collect_stage_tree_entries(Path("/stage"))

        self.assertIn("Could not inspect stage tree entries", str(raised.exception))

    def test_validate_publication_filesystems_rejects_missing_parent(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            candidate_root = self._stage_tree(root / "candidate")

            with self.assertRaises(StageIntegrityError):
                _validate_publication_filesystems(
                    candidate_stage_root=candidate_root,
                    stage_root=root / "missing-parent" / "public",
                )

    def test_validate_publication_filesystems_rejects_existing_stage_on_other_device(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            candidate_root = self._stage_tree(root / "candidate")
            stage_root = self._stage_tree(root / "public")
            stage_parent = stage_root.parent

            with patch(
                "buildish_site_pipeline.staging.publication._stat_device_id",
                side_effect=lambda path: {
                    stage_parent: 1,
                    candidate_root: 1,
                    stage_root: 2,
                }[path],
            ):
                with self.assertRaises(StageIntegrityError):
                    _validate_publication_filesystems(
                        candidate_stage_root=candidate_root,
                        stage_root=stage_root,
                    )

    def test_replace_stage_root_restores_previous_stage_on_publish_failure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            stage_root = self._stage_tree(root / "public")
            candidate_root = self._stage_tree(root / "candidate")
            backup_root = stage_root.parent / f".{stage_root.name}.previous"
            real_replace = Path.replace

            def replace(path: Path, target: Path) -> Path:
                if path == candidate_root and target == stage_root:
                    raise OSError("publish failed")
                return real_replace(path, target)

            with patch.object(Path, "replace", autospec=True, side_effect=replace):
                with self.assertRaises(RetainedStageError):
                    _replace_stage_root(
                        candidate_stage_root=candidate_root,
                        stage_root=stage_root,
                    )

            self.assertTrue(stage_root.exists())
            self.assertTrue((stage_root / "manifest.json").is_file())
            self.assertFalse(backup_root.exists())

    def test_replace_stage_root_raises_when_rollback_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            stage_root = self._stage_tree(root / "public")
            candidate_root = self._stage_tree(root / "candidate")
            real_replace = Path.replace
            call_count = 0

            def replace(path: Path, target: Path) -> Path:
                nonlocal call_count
                call_count += 1
                if call_count == 2:
                    raise OSError("publish failed")
                if call_count == 3:
                    raise OSError("rollback failed")
                return real_replace(path, target)

            with patch.object(Path, "replace", autospec=True, side_effect=replace):
                with self.assertRaises(StageIntegrityError) as raised:
                    _replace_stage_root(
                        candidate_stage_root=candidate_root,
                        stage_root=stage_root,
                    )

            self.assertIn("roll back safely", str(raised.exception))

    def test_replace_stage_root_raises_when_publish_fails_without_prior_stage(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            stage_root = root / "public"
            candidate_root = self._stage_tree(root / "candidate")

            with patch.object(Path, "replace", autospec=True) as replace:
                replace.side_effect = OSError("publish failed")

                with self.assertRaises(StageIntegrityError) as raised:
                    _replace_stage_root(
                        candidate_stage_root=candidate_root,
                        stage_root=stage_root,
                    )

            self.assertIn("Could not finalize stage publication", str(raised.exception))

    def test_fsync_helpers_wrap_os_errors(self) -> None:
        with patch("buildish_site_pipeline.staging.publication.os.open") as open_:
            open_.side_effect = OSError("boom")
            with self.assertRaises(StageIntegrityError):
                _fsync_file(Path("/stage/manifest.json"))
            with self.assertRaises(StageIntegrityError):
                _fsync_directory(Path("/stage"))

    @staticmethod
    def _stage_tree(path: Path) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        (path / "manifest.json").write_text(
            json.dumps({"version": 1}),
            encoding="utf-8",
        )
        return path