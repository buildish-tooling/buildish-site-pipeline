# Copyright 2026 The Apache Software Foundation

"""Publication-precondition tests for the staging engine."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from apache_buildish_site_pipeline.cli_errors import StageIntegrityError
from apache_buildish_site_pipeline.staging.execution import finalize_stage_publication


class StagingExecutionTests(unittest.TestCase):
    def test_publication_rejects_stage_root_with_symlinked_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            candidate_stage_root = _create_candidate_stage(workspace_root / "candidate-stage")
            real_site_root = workspace_root / "real-site"
            real_site_root.mkdir(parents=True, exist_ok=True)
            (workspace_root / "site").symlink_to(real_site_root, target_is_directory=True)

            with self.assertRaises(StageIntegrityError) as raised:
                finalize_stage_publication(
                    candidate_stage_root=candidate_stage_root,
                    stage_root=workspace_root / "site/.stage",
                )

            self.assertIn("resolves through a symlink", str(raised.exception))
            self.assertTrue(candidate_stage_root.exists())

    def test_initial_publication_rejects_cross_filesystem_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            candidate_stage_root = _create_candidate_stage(workspace_root / "candidate-stage")
            stage_root = workspace_root / "site/.stage"
            stage_root.parent.mkdir(parents=True, exist_ok=True)

            with mock.patch(
                "apache_buildish_site_pipeline.staging.execution._stat_device_id",
                side_effect=_device_id_map(
                    {
                        candidate_stage_root.resolve(strict=False): 101,
                        stage_root.parent.resolve(strict=False): 202,
                    },
                ),
            ):
                with self.assertRaises(StageIntegrityError) as raised:
                    finalize_stage_publication(candidate_stage_root=candidate_stage_root, stage_root=stage_root)

            self.assertIn("same filesystem", str(raised.exception))
            self.assertTrue(candidate_stage_root.exists())
            self.assertFalse(stage_root.exists())

    def test_replacement_publication_rejects_cross_filesystem_candidate_before_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            candidate_stage_root = _create_candidate_stage(workspace_root / "candidate-stage")
            stage_root = workspace_root / "site/.stage"
            stage_root.mkdir(parents=True, exist_ok=True)
            keep_path = stage_root / "keep.txt"
            keep_path.write_text("trusted\n", encoding="utf-8")

            with mock.patch(
                "apache_buildish_site_pipeline.staging.execution._stat_device_id",
                side_effect=_device_id_map(
                    {
                        candidate_stage_root.resolve(strict=False): 101,
                        stage_root.resolve(strict=False): 202,
                        stage_root.parent.resolve(strict=False): 202,
                    },
                ),
            ):
                with self.assertRaises(StageIntegrityError) as raised:
                    finalize_stage_publication(
                        candidate_stage_root=candidate_stage_root,
                        stage_root=stage_root,
                        allow_replace_existing=True,
                    )

            self.assertIn("same filesystem", str(raised.exception))
            self.assertTrue(candidate_stage_root.exists())
            self.assertEqual(keep_path.read_text(encoding="utf-8"), "trusted\n")


def _create_candidate_stage(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    (path / "manifest.json").write_text('{"schemaVersion":1}\n', encoding="utf-8")
    return path


def _device_id_map(overrides: dict[Path, int]):
    def _lookup(path: Path) -> int:
        normalized_path = path.resolve(strict=False)
        if normalized_path in overrides:
            return overrides[normalized_path]
        return normalized_path.stat().st_dev

    return _lookup