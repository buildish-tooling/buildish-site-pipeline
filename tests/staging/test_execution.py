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

"""Publication and private-write safety tests for the staging engine."""

from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from buildish_site_pipeline.cli.errors import StageIntegrityError
from buildish_site_pipeline.commands.shared import load_workspace_inputs
from buildish_site_pipeline.evaluation import EvaluationMode, EvaluationRequest, run_evaluation
from buildish_site_pipeline.models.enums import PlanningTarget, StageCommand
from buildish_site_pipeline.planning import evaluate_planning
from buildish_site_pipeline.staging.aggregates import _load_unit_contribution_manifests, _write_json_file
from buildish_site_pipeline.staging.coordinator import publish_stage
from buildish_site_pipeline.staging.publication import finalize_stage_publication
from buildish_site_pipeline.staging.types import WorkRootLayout
from buildish_site_pipeline.staging.worker_protocol import ContributionFileRefs, UnitContributionManifestWire, WorkerResultWire, write_unit_manifest
from buildish_site_pipeline.staging.workdirs import prepare_next_stage_root
from tests.support.workspace import _workspace


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

            with mock.patch("buildish_site_pipeline.staging.file_writes.os.replace", side_effect=_fail_replace), self.assertRaises(StageIntegrityError) as raised:
                    _write_json_file(json_path, [_JsonStub('{"componentId":"runtime"}')])

            self.assertIn("Could not write stage text file", str(raised.exception))
            self.assertEqual(json_path.read_text(encoding="utf-8"), "trusted\n")
            self.assertEqual(list(json_path.parent.glob(".components.json.*.tmp")), [])

    def test_worker_manifest_write_replaces_existing_file_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            manifest_path = workspace_root / "work/fragments/component_spark.json"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text('{"unitId":"old"}\n', encoding="utf-8")

            write_unit_manifest(manifest_path, UnitContributionManifestWire(unit_id="component:spark"))

            self.assertIn('"unitId": "component:spark"', manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(list(manifest_path.parent.glob(".component_spark.json.*.tmp")), [])

    def test_worker_manifest_write_cleans_temp_file_and_preserves_existing_content_on_replace_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            manifest_path = workspace_root / "work/fragments/component_spark.json"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text('{"unitId":"trusted"}\n', encoding="utf-8")

            def _fail_replace(path, target):
                del path, target
                raise OSError("replace blocked")

            with mock.patch(
                "buildish_site_pipeline.staging.worker_protocol.Path.replace",
                new=_fail_replace,
            ), self.assertRaises(StageIntegrityError) as raised:
                write_unit_manifest(
                    manifest_path,
                    UnitContributionManifestWire(unit_id="component:spark"),
                )

            self.assertIn("Could not write worker contribution manifest", str(raised.exception))
            self.assertEqual(manifest_path.read_text(encoding="utf-8"), '{"unitId":"trusted"}\n')
            self.assertEqual(list(manifest_path.parent.glob(".component_spark.json.*.tmp")), [])

    def test_page_contribution_loading_rejects_manifest_outside_private_fragment_root(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            layout = _work_layout(workspace_root)
            outside_manifest = workspace_root / "escape/component_spark.json"
            write_unit_manifest(outside_manifest, UnitContributionManifestWire(unit_id="component:spark"))

            with self.assertRaises(StageIntegrityError) as raised:
                _load_unit_contribution_manifests(
                    layout=layout,
                    worker_results=(
                        WorkerResultWire(
                            unit_id="component:spark",
                            contribution_files=ContributionFileRefs(unit_manifest=str(outside_manifest)),
                        ),
                    ),
                    retained_unit_manifests=(),
                )

            self.assertIn("coordinator-owned location", str(raised.exception))

    def test_page_contribution_loading_rejects_symlinked_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            layout = _work_layout(workspace_root)
            real_manifest = workspace_root / "real/component_spark.json"
            write_unit_manifest(real_manifest, UnitContributionManifestWire(unit_id="component:spark"))
            manifest_path = layout.fragments_root / "component_spark.json"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.symlink_to(real_manifest)

            with self.assertRaises(StageIntegrityError) as raised:
                _load_unit_contribution_manifests(
                    layout=layout,
                    worker_results=(
                        WorkerResultWire(
                            unit_id="component:spark",
                            contribution_files=ContributionFileRefs(unit_manifest=str(manifest_path)),
                        ),
                    ),
                    retained_unit_manifests=(),
                )

            self.assertIn("normal file", str(raised.exception))

    def test_page_contribution_loading_rejects_manifest_with_mismatched_unit_id(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            layout = _work_layout(workspace_root)
            manifest_path = layout.fragments_root / "component_spark.json"
            write_unit_manifest(
                manifest_path,
                UnitContributionManifestWire(unit_id="component:other"),
            )

            with self.assertRaises(StageIntegrityError) as raised:
                _load_unit_contribution_manifests(
                    layout=layout,
                    worker_results=(
                        WorkerResultWire(
                            unit_id="component:spark",
                            contribution_files=ContributionFileRefs(
                                unit_manifest=str(manifest_path)
                            ),
                        ),
                    ),
                    retained_unit_manifests=(),
                )

            self.assertIn("does not match the worker result", str(raised.exception))

    def test_page_contribution_loading_rejects_duplicate_unit_manifests(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            layout = _work_layout(workspace_root)
            manifest_path = layout.fragments_root / "component_spark.json"
            write_unit_manifest(
                manifest_path,
                UnitContributionManifestWire(unit_id="component:spark"),
            )

            with self.assertRaises(StageIntegrityError) as raised:
                _load_unit_contribution_manifests(
                    layout=layout,
                    worker_results=(
                        WorkerResultWire(
                            unit_id="component:spark",
                            contribution_files=ContributionFileRefs(
                                unit_manifest=str(manifest_path)
                            ),
                        ),
                    ),
                    retained_unit_manifests=(
                        UnitContributionManifestWire(unit_id="component:spark"),
                    ),
                )

            self.assertIn("Duplicate worker contribution manifest", str(raised.exception))

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

    def test_initial_publication_syncs_published_stage_before_returning(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            candidate_stage_root = _create_candidate_stage(workspace_root / "candidate-stage")
            stage_root = workspace_root / "site/.stage"
            stage_root.parent.mkdir(parents=True, exist_ok=True)

            with mock.patch(
                "buildish_site_pipeline.staging.publication._fsync_published_stage",
            ) as fsync_published_stage:
                publication = finalize_stage_publication(candidate_stage_root=candidate_stage_root, stage_root=stage_root)

        self.assertEqual(publication.stage_root, stage_root.resolve(strict=False))
        fsync_published_stage.assert_called_once_with(stage_root.resolve(strict=False))

    def test_candidate_stage_root_preparation_rejects_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            real_root = workspace_root / "real-stage"
            real_root.mkdir(parents=True, exist_ok=True)
            symlink_root = workspace_root / "candidate-stage"
            symlink_root.symlink_to(real_root, target_is_directory=True)

            with self.assertRaises(StageIntegrityError) as raised:
                prepare_next_stage_root(symlink_root)

        self.assertIn("must not be a symlink", str(raised.exception))

    def test_candidate_stage_root_preparation_rejects_non_directory_and_non_empty_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            file_root = workspace_root / "candidate-stage-file"
            file_root.write_text("not a directory\n", encoding="utf-8")
            non_empty_root = workspace_root / "candidate-stage-dir"
            non_empty_root.mkdir(parents=True, exist_ok=True)
            (non_empty_root / "manifest.json").write_text("{}\n", encoding="utf-8")

            with self.assertRaises(StageIntegrityError) as file_error:
                prepare_next_stage_root(file_root)
            with self.assertRaises(StageIntegrityError) as directory_error:
                prepare_next_stage_root(non_empty_root)

        self.assertIn("must be a directory", str(file_error.exception))
        self.assertIn("must be absent or empty", str(directory_error.exception))

    def test_replacement_publication_syncs_published_stage_before_returning(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            candidate_stage_root = _create_candidate_stage(workspace_root / "candidate-stage")
            stage_root = _create_candidate_stage(workspace_root / "site/.stage")

            with mock.patch(
                "buildish_site_pipeline.staging.publication._fsync_published_stage",
            ) as fsync_published_stage:
                publication = finalize_stage_publication(
                    candidate_stage_root=candidate_stage_root,
                    stage_root=stage_root,
                    allow_replace_existing=True,
                )

        self.assertEqual(publication.stage_root, stage_root.resolve(strict=False))
        fsync_published_stage.assert_called_once_with(stage_root.resolve(strict=False))

    def test_initial_publication_rejects_cross_filesystem_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            candidate_stage_root = _create_candidate_stage(workspace_root / "candidate-stage")
            stage_root = workspace_root / "site/.stage"
            stage_root.parent.mkdir(parents=True, exist_ok=True)

            with mock.patch(
                "buildish_site_pipeline.staging.publication._stat_device_id",
                side_effect=_device_id_map(
                    {
                        candidate_stage_root.resolve(strict=False): 101,
                        stage_root.parent.resolve(strict=False): 202,
                    },
                ),
            ), self.assertRaises(StageIntegrityError) as raised:
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
                "buildish_site_pipeline.staging.publication._stat_device_id",
                side_effect=_device_id_map(
                    {
                        candidate_stage_root.resolve(strict=False): 101,
                        stage_root.resolve(strict=False): 202,
                        stage_root.parent.resolve(strict=False): 202,
                    },
                ),
            ), self.assertRaises(StageIntegrityError) as raised:
                finalize_stage_publication(
                    candidate_stage_root=candidate_stage_root,
                    stage_root=stage_root,
                    allow_replace_existing=True,
                )

            self.assertIn("same filesystem", str(raised.exception))
            self.assertTrue(candidate_stage_root.exists())
            self.assertEqual(keep_path.read_text(encoding="utf-8"), "trusted\n")

    def test_renderer_probe_never_observes_manifest_pointing_to_missing_data_files(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            stage_root = workspace_root / "site/.stage"
            watched_file = workspace_root / "components/runtime/docs/releases/4.0.0/index.md"
            failures: list[str] = []
            stop_event = threading.Event()

            def _probe() -> None:
                while not stop_event.is_set():
                    manifest_path = stage_root / "manifest.json"
                    if not manifest_path.exists():
                        continue
                    try:
                        manifest_text = manifest_path.read_text(encoding="utf-8")
                        manifest = json.loads(manifest_text)
                        for relative_path in manifest.get("dataFiles", {}).values():
                            if relative_path is None:
                                continue
                            if not (stage_root / relative_path).is_file():
                                try:
                                    if manifest_path.read_text(encoding="utf-8") != manifest_text:
                                        break
                                except FileNotFoundError:
                                    break
                                failures.append(str(relative_path))
                                stop_event.set()
                                return
                    except FileNotFoundError:
                        continue

            probe_thread = threading.Thread(target=_probe)
            probe_thread.start()
            try:
                for index in range(3):
                    watched_file.write_text(f"probe cycle {index}\n", encoding="utf-8")
                    publication = _publish_workspace_stage(workspace_root)
                    self.assertTrue(publication.manifest_path.is_file())
            finally:
                stop_event.set()
                probe_thread.join(timeout=5)

        self.assertEqual(failures, [])


def _create_candidate_stage(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    (path / "manifest.json").write_text('{"schemaVersion":1}\n', encoding="utf-8")
    return path


def _work_layout(workspace_root: Path) -> WorkRootLayout:
    work_root = workspace_root / "work"
    next_stage_root = workspace_root / "next-stage"
    content_root = next_stage_root / "content"
    static_root = next_stage_root / "static"
    data_root = next_stage_root / "data"
    fragments_root = work_root / "fragments"
    units_root = work_root / "units"
    for path in (work_root, next_stage_root, content_root, static_root, data_root, fragments_root, units_root):
        path.mkdir(parents=True, exist_ok=True)
    return WorkRootLayout(
        work_root=work_root,
        next_stage_root=next_stage_root,
        content_root=content_root,
        static_root=static_root,
        data_root=data_root,
        fragments_root=fragments_root,
        units_root=units_root,
    )


def _publish_workspace_stage(workspace_root: Path):
    loaded_inputs = load_workspace_inputs(workspace_root)
    planning = evaluate_planning(
        target=PlanningTarget.BUILD,
        catalog=loaded_inputs.catalog,
        provider_snapshot=loaded_inputs.provider_snapshot,
        workspace_root=workspace_root,
        component_documents=loaded_inputs.component_documents,
        stage_root=workspace_root / "site/.stage",
        work_root=workspace_root / ".buildish/work",
    )
    evaluation = run_evaluation(
        request=EvaluationRequest(mode=EvaluationMode.BUILD),
        planning=planning,
    )
    if evaluation.build_plan is None:
        raise AssertionError("expected build plan for publication probe")
    return publish_stage(
        build_plan=evaluation.build_plan,
        diagnostics=evaluation.diagnostics,
        provider_snapshot=loaded_inputs.provider_snapshot,
        stage_root=workspace_root / "site/.stage",
        allow_replace_existing=(workspace_root / "site/.stage").exists(),
        command=StageCommand.BUILD,
    )


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