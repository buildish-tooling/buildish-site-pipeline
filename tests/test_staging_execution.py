# Copyright 2026 The Apache Software Foundation

"""Publication and private-write safety tests for the staging engine."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from apache_buildish_site_pipeline.cli_errors import StageIntegrityError
from apache_buildish_site_pipeline.staging.execution import _write_json_file, finalize_stage_publication


class StagingExecutionTests(unittest.TestCase):
    def test_private_json_write_replaces_existing_file_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            json_path = workspace_root / "stage/data/components.json"
            json_path.parent.mkdir(parents=True, exist_ok=True)
            json_path.write_text("old\n", encoding="utf-8")

            _write_json_file(json_path, [_JsonStub('{"componentId":"runtime"}')])

            self.assertEqual(json_path.read_text(encoding="utf-8"), '[\n{"componentId":"runtime"}\n]\n')
            self.assertEqual(list(json_path.parent.glob(".components.json.*.tmp")), [])

    def test_private_json_write_cleans_temp_file_and_preserves_existing_content_on_replace_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            json_path = workspace_root / "stage/data/components.json"
            json_path.parent.mkdir(parents=True, exist_ok=True)
            json_path.write_text("trusted\n", encoding="utf-8")

            def _fail_replace(src, dst):
                del src, dst
                raise OSError("replace blocked")

            with mock.patch("apache_buildish_site_pipeline.staging.execution.os.replace", side_effect=_fail_replace):
                with self.assertRaises(StageIntegrityError) as raised:
                    _write_json_file(json_path, [_JsonStub('{"componentId":"runtime"}')])

            self.assertIn("Could not write stage JSON file", str(raised.exception))
            self.assertEqual(json_path.read_text(encoding="utf-8"), "trusted\n")
            self.assertEqual(list(json_path.parent.glob(".components.json.*.tmp")), [])

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

    def test_publication_rejects_candidate_stage_with_nested_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            candidate_stage_root = _create_candidate_stage(workspace_root / "candidate-stage")
            stage_root = workspace_root / "site/.stage"
            data_root = candidate_stage_root / "data"
            data_root.mkdir(parents=True, exist_ok=True)
            real_payload = workspace_root / "routes.json"
            real_payload.write_text("[]\n", encoding="utf-8")
            (data_root / "routes.json").symlink_to(real_payload)

            with self.assertRaises(StageIntegrityError) as raised:
                finalize_stage_publication(candidate_stage_root=candidate_stage_root, stage_root=stage_root)

            self.assertIn("must not contain symlinks", str(raised.exception))
            self.assertTrue(candidate_stage_root.exists())
            self.assertFalse(stage_root.exists())

    def test_replacement_rejects_existing_stage_with_unknown_extra_path(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            candidate_stage_root = _create_candidate_stage(workspace_root / "candidate-stage")
            stage_root = _create_candidate_stage(workspace_root / "site/.stage")
            extra_path = stage_root / "notes.txt"
            extra_path.write_text("keep me\n", encoding="utf-8")

            with self.assertRaises(StageIntegrityError) as raised:
                finalize_stage_publication(
                    candidate_stage_root=candidate_stage_root,
                    stage_root=stage_root,
                    allow_replace_existing=True,
                )

            self.assertIn("ambiguous ownership", str(raised.exception))
            self.assertEqual(extra_path.read_text(encoding="utf-8"), "keep me\n")
            self.assertTrue(candidate_stage_root.exists())

    def test_replacement_rejects_existing_stage_with_path_type_change(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            candidate_stage_root = _create_candidate_stage(workspace_root / "candidate-stage")
            stage_root = _create_candidate_stage(workspace_root / "site/.stage")
            existing_file = stage_root / "data/routes"
            existing_file.parent.mkdir(parents=True, exist_ok=True)
            existing_file.write_text("legacy\n", encoding="utf-8")
            candidate_directory = candidate_stage_root / "data/routes"
            candidate_directory.mkdir(parents=True, exist_ok=True)
            (candidate_directory / "index.json").write_text("[]\n", encoding="utf-8")

            with self.assertRaises(StageIntegrityError) as raised:
                finalize_stage_publication(
                    candidate_stage_root=candidate_stage_root,
                    stage_root=stage_root,
                    allow_replace_existing=True,
                )

            self.assertIn("change existing path types ambiguously", str(raised.exception))
            self.assertEqual(existing_file.read_text(encoding="utf-8"), "legacy\n")
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


class _JsonStub:
    def __init__(self, serialized: str) -> None:
        self._serialized = serialized

    def model_dump_json(self, *, indent: int, exclude_none: bool) -> str:
        del indent, exclude_none
        return self._serialized


def _device_id_map(overrides: dict[Path, int]):
    def _lookup(path: Path) -> int:
        normalized_path = path.resolve(strict=False)
        if normalized_path in overrides:
            return overrides[normalized_path]
        return normalized_path.stat().st_dev

    return _lookup