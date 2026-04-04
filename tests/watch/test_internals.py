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

import io
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from apache_buildish_site_pipeline.cli import _run
from apache_buildish_site_pipeline.commands.watch import (
    _WatchEventStream,
    _coalesce_dirty_paths,
    _derive_watch_roots,
    _dirty_unit_ids_for_paths,
    _is_pipeline_owned_path,
    _load_trusted_stage,
    _select_incremental_build,
)
from apache_buildish_site_pipeline.commands.shared import load_workspace_inputs
from apache_buildish_site_pipeline.models.enums import PlanningTarget
from apache_buildish_site_pipeline.planning import evaluate_planning
from apache_buildish_site_pipeline.staging.ownership import build_owned_units
from tests.support.staging import _expand_workspace_for_multiple_owned_units
from tests.support.workspace import _cwd, _workspace


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

    def test_load_trusted_stage_reads_incremental_metadata_from_built_stage(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            _expand_workspace_for_multiple_owned_units(workspace_root)
            with _cwd(workspace_root):
                exit_code = _run(argv=["build"], stdout=mock.Mock(), stderr=mock.Mock())

            trusted_stage = _load_trusted_stage(workspace_root / "site/.stage")

        self.assertEqual(exit_code, 0)
        self.assertIsNotNone(trusted_stage)
        if trusted_stage is None or trusted_stage.incremental_state is None:
            self.fail("expected incremental trusted-stage metadata")
        self.assertTrue(any(claim.path_kind == "directory" for claim in trusted_stage.incremental_state.output_ownership.claims))
        self.assertTrue(any(entry.dependent_unit_ids for entry in trusted_stage.incremental_state.aggregate_dependencies.entries))

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

    def test_dirty_unit_mapping_targets_component_unit_for_component_edit(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            _expand_workspace_for_multiple_owned_units(workspace_root)
            build_plan = _build_plan(workspace_root)
            with _cwd(workspace_root):
                exit_code = _run(argv=["build"], stdout=io.StringIO(), stderr=io.StringIO())
            trusted_stage = _load_trusted_stage(workspace_root / "site/.stage")
            dirty_path = workspace_root / "components/runtime/docs/releases/4.0.0/index.md"

            if build_plan is None:
                self.fail("expected watch build plan")
            units = build_owned_units(build_plan)
            dirty_unit_ids = _dirty_unit_ids_for_paths(
                build_plan=build_plan,
                units=units,
                dirty_paths=(dirty_path,),
                repo_root=workspace_root,
            )
            if trusted_stage is None:
                self.fail("expected trusted stage")
            selection = _select_incremental_build(
                trusted_stage=trusted_stage,
                build_plan=build_plan,
                dirty_paths=(dirty_path,),
                repo_root=workspace_root,
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(dirty_unit_ids, frozenset({"component:spark"}))
        self.assertEqual(selection.included_unit_ids, frozenset({"component:spark"}))
        self.assertIn("content/components/spark", selection.seed_stage_removals)
        self.assertNotIn("content/site", selection.seed_stage_removals)

    def test_dirty_unit_mapping_broadens_provider_snapshot_changes_to_all_units(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            _expand_workspace_for_multiple_owned_units(workspace_root)
            build_plan = _build_plan(workspace_root)

        if build_plan is None:
            self.fail("expected watch build plan")
        units = build_owned_units(build_plan)
        dirty_unit_ids = _dirty_unit_ids_for_paths(
            build_plan=build_plan,
            units=units,
            dirty_paths=(workspace_root / "site/provider-snapshot.json",),
            repo_root=workspace_root,
        )

        self.assertEqual(dirty_unit_ids, frozenset(unit.unit_id for unit in units))

    def test_dirty_unit_mapping_broadens_catalog_metadata_changes_to_all_units(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            _expand_workspace_for_multiple_owned_units(workspace_root)
            build_plan = _build_plan(workspace_root)

        if build_plan is None:
            self.fail("expected watch build plan")
        units = build_owned_units(build_plan)
        dirty_unit_ids = _dirty_unit_ids_for_paths(
            build_plan=build_plan,
            units=units,
            dirty_paths=(workspace_root / "site/components.yaml",),
            repo_root=workspace_root,
        )

        self.assertEqual(dirty_unit_ids, frozenset(unit.unit_id for unit in units))

    @mock.patch.dict("os.environ", {"WATCHFILES_FORCE_POLLING": "1"}, clear=False)
    def test_watch_event_stream_still_collects_changes_when_polling_is_forced(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            changed_file = workspace_root / "components/runtime/docs/index.md"
            fake_events = iter(({(None, str(changed_file))}, set()))
            with mock.patch("apache_buildish_site_pipeline.commands.watch.watch", return_value=fake_events):
                stream = _WatchEventStream(
                    watch_roots=(workspace_root,),
                    stage_root=workspace_root / "site/.stage",
                    work_root=workspace_root / ".buildish/work",
                    report_output=None,
                    stop_event=threading.Event(),
                )
                try:
                    dirty_paths = stream.collect_dirty_paths(wait_for_first=True)
                finally:
                    stream.close()

        self.assertEqual(dirty_paths, (changed_file.resolve(strict=False),))

    @mock.patch.dict("os.environ", {"WATCHFILES_FORCE_POLLING": "1"}, clear=False)
    def test_watch_event_stream_coalesces_noisy_nested_batches_when_polling_is_forced(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            changed_file = workspace_root / "components/runtime/docs/releases/4.0.0/index.md"
            noisy_parent = changed_file.parent
            noisy_grandparent = noisy_parent.parent
            fake_events = iter(
                (
                    {(None, str(changed_file))},
                    {(None, str(noisy_parent)), (None, str(changed_file))},
                    {(None, str(noisy_grandparent))},
                    set(),
                ),
            )
            with mock.patch("apache_buildish_site_pipeline.commands.watch.watch", return_value=fake_events):
                stream = _WatchEventStream(
                    watch_roots=(workspace_root,),
                    stage_root=workspace_root / "site/.stage",
                    work_root=workspace_root / ".buildish/work",
                    report_output=None,
                    stop_event=threading.Event(),
                )
                try:
                    dirty_paths = stream.collect_dirty_paths(wait_for_first=True)
                finally:
                    stream.close()

        self.assertEqual(dirty_paths, (noisy_grandparent.resolve(strict=False),))


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


def _build_plan(workspace_root: Path):
    loaded_inputs = load_workspace_inputs(workspace_root)
    planning = evaluate_planning(
        target=PlanningTarget.WATCH,
        catalog=loaded_inputs.catalog,
        provider_snapshot=loaded_inputs.provider_snapshot,
        workspace_root=workspace_root,
        component_documents=loaded_inputs.component_documents,
        stage_root=workspace_root / "site/.stage",
        work_root=workspace_root / ".buildish/work",
    )
    return planning.build_plan_candidate