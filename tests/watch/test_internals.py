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

"""Focused tests for watch-loop coordination helpers."""

from __future__ import annotations

import io
import json
import logging
import signal
import tempfile
import threading
import unittest
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import buildish_site_pipeline.commands.watch as watch_command
from buildish_site_pipeline.cli import _run
from buildish_site_pipeline.cli.contract import (
    ReportFormat,
    ReportRequest,
    RepositoryLayout,
    WatchEventFormat,
    WatchEventRequest,
    WatchInvocation,
)
from buildish_site_pipeline.cli.errors import InvocationError, StageIntegrityError
from buildish_site_pipeline.commands.watch import (
    TrustedStageState,
    _WatchIo,
    _dirty_component_unit_id,
    _dirty_unit_ids_for_paths,
    _emit_cycle_report,
    _failed_cycle_outcome,
    _graceful_watch_shutdown,
    _load_trusted_stage,
    _open_watch_event_output,
    _run_follow_up_cycle,
    _run_watch_cycle,
    _select_incremental_build,
    _stage_path_is_claimed,
    run_watch,
)
from buildish_site_pipeline.commands.watch_events import (
    _WatchEventStream,
    _build_plan_watch_roots,
    _coalesce_dirty_paths,
    _derive_watch_roots,
    _is_pipeline_owned_path,
)
from buildish_site_pipeline.commands.shared import load_workspace_inputs
from buildish_site_pipeline.models.enums import (
    CheckFailureThreshold,
    DiagnosticSeverity,
    DocumentFormat,
    PlanningTarget,
    RunStatus,
    StageCommand,
)
from buildish_site_pipeline.models.loading import load_stage_manifest
from buildish_site_pipeline.models.emitted.planning_stage_contract import (
    PipelineDiagnosticEntry,
    StageRunReportV1,
    StageRunSummary,
)
from buildish_site_pipeline.planning import evaluate_planning
from buildish_site_pipeline.staging.ownership import build_owned_units
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
            repo_root / "site/catalog.yaml",
        )

        self.assertEqual(
            _coalesce_dirty_paths(changed_paths),
            (
                repo_root / "site/catalog.yaml",
                repo_root / "components/runtime/docs/releases",
            ),
        )

    def test_derive_watch_roots_keeps_site_catalog_provider_and_planning_inputs_visible(self) -> None:
        workspace_root = Path("/workspace")
        site_root = workspace_root / "site"
        catalog_path = site_root / "catalog.yaml"
        provider_snapshot_path = workspace_root / "provider-snapshot.json"
        planning_roots = (
            workspace_root / "components/runtime/docs",
            site_root / "catalog.yaml",
        )

        self.assertEqual(
            _derive_watch_roots(
                site_root=site_root,
                catalog_path=catalog_path,
                provider_snapshot_path=provider_snapshot_path,
                planning_roots=planning_roots,
            ),
            (
                provider_snapshot_path,
                site_root,
                workspace_root / "components/runtime/docs",
            ),
        )

    def test_derive_watch_roots_keeps_external_site_root_visible(self) -> None:
        workspace_root = Path("/workspace")
        site_root = Path("/catalog-repo/site")
        catalog_path = site_root / "catalog.yaml"

        self.assertEqual(
            _derive_watch_roots(
                site_root=site_root,
                catalog_path=catalog_path,
                provider_snapshot_path=None,
                planning_roots=(workspace_root / "components/runtime/docs",),
            ),
            (site_root, workspace_root / "components/runtime/docs"),
        )

    def test_build_plan_watch_roots_include_component_cache_and_site_inputs(self) -> None:
        build_plan = SimpleNamespace(
            site=SimpleNamespace(
                site_pages_root=Path("/workspace/site/pages"),
                site_assets_root=Path("/workspace/site/assets"),
                vendor_assets=(
                    SimpleNamespace(source_path=Path("/workspace/site/package.json")),
                ),
                components=(
                    SimpleNamespace(
                        metadata_file=Path("/workspace/components/runtime/component.yaml"),
                        pages_root=Path("/workspace/components/runtime/docs"),
                        assets_root=Path("/workspace/components/runtime/assets"),
                        content_source=SimpleNamespace(
                            local_dir=Path("/workspace/buildish-mammoth-cache/site/pages")
                        ),
                    ),
                ),
            )
        )

        self.assertEqual(
            _build_plan_watch_roots(build_plan),
            (
                Path("/workspace/site/pages"),
                Path("/workspace/site/assets"),
                Path("/workspace/site/package.json"),
                Path("/workspace/components/runtime/component.yaml"),
                Path("/workspace/components/runtime/docs"),
                Path("/workspace/components/runtime/assets"),
                Path("/workspace/buildish-mammoth-cache/site/pages"),
            ),
        )

    def test_pipeline_owned_path_detection_filters_stage_work_renderer_outputs_event_outputs_and_backup_descendants(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            stage_root = workspace_root / "site/.stage"
            work_root = workspace_root / "site/.site-pipeline-work"
            report_output = workspace_root / "watch-report.json"
            event_output = workspace_root / "site/.watch-events.123456.jsonl"
            generated_build_path = workspace_root / "site/build/fake-hugo.log"
            generated_resource_parent = workspace_root / "site/resources"
            generated_resource = workspace_root / "site/resources/_gen/assets/main.css"
            backup_descendant = workspace_root / "site/..stage.backup.abcdef/content/index.md"
            authored_path = workspace_root / "components/runtime/docs/index.md"

            self.assertTrue(
                _is_pipeline_owned_path(
                    path=stage_root / "manifest.json",
                    stage_root=stage_root,
                    work_root=work_root,
                    report_output=report_output,
                    event_output=event_output,
                ),
            )
            self.assertTrue(
                _is_pipeline_owned_path(
                    path=work_root / "watch/cycle-000001/stage/manifest.json",
                    stage_root=stage_root,
                    work_root=work_root,
                    report_output=report_output,
                    event_output=event_output,
                ),
            )
            self.assertTrue(
                _is_pipeline_owned_path(
                    path=workspace_root / ".watch-report.json.123.tmp",
                    stage_root=stage_root,
                    work_root=work_root,
                    report_output=report_output,
                    event_output=event_output,
                ),
            )
            self.assertTrue(
                _is_pipeline_owned_path(
                    path=event_output,
                    stage_root=stage_root,
                    work_root=work_root,
                    report_output=report_output,
                    event_output=event_output,
                ),
            )
            self.assertTrue(
                _is_pipeline_owned_path(
                    path=generated_build_path,
                    stage_root=stage_root,
                    work_root=work_root,
                    report_output=report_output,
                    event_output=event_output,
                ),
            )
            self.assertTrue(
                _is_pipeline_owned_path(
                    path=generated_resource_parent,
                    stage_root=stage_root,
                    work_root=work_root,
                    report_output=report_output,
                    event_output=event_output,
                ),
            )
            self.assertTrue(
                _is_pipeline_owned_path(
                    path=generated_resource,
                    stage_root=stage_root,
                    work_root=work_root,
                    report_output=report_output,
                    event_output=event_output,
                ),
            )
            self.assertTrue(
                _is_pipeline_owned_path(
                    path=backup_descendant,
                    stage_root=stage_root,
                    work_root=work_root,
                    report_output=report_output,
                    event_output=event_output,
                ),
            )
            self.assertFalse(
                _is_pipeline_owned_path(
                    path=authored_path,
                    stage_root=stage_root,
                    work_root=work_root,
                    report_output=report_output,
                    event_output=event_output,
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
            site_root = workspace_root / "site"
            dirty_unit_ids = _dirty_unit_ids_for_paths(
                build_plan=build_plan,
                units=units,
                dirty_paths=(dirty_path,),
                workspace_root=workspace_root,
                site_root=site_root,
                catalog_path=site_root / "catalog.yaml",
                provider_snapshot_path=site_root / "provider-snapshot.json",
            )
            if trusted_stage is None:
                self.fail("expected trusted stage")
            selection = _select_incremental_build(
                trusted_stage=trusted_stage,
                build_plan=build_plan,
                dirty_paths=(dirty_path,),
                workspace_root=workspace_root,
                site_root=site_root,
                catalog_path=site_root / "catalog.yaml",
                provider_snapshot_path=site_root / "provider-snapshot.json",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(dirty_unit_ids, frozenset({"component:spark"}))
        self.assertEqual(selection.included_unit_ids, frozenset({"component:spark"}))
        self.assertIn("content/spark", selection.seed_stage_removals)
        self.assertIn("static/spark/assets", selection.seed_stage_removals)
        self.assertNotIn("content/site", selection.seed_stage_removals)

    def test_dirty_unit_mapping_broadens_provider_snapshot_changes_to_all_units(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            _expand_workspace_for_multiple_owned_units(workspace_root)
            build_plan = _build_plan(workspace_root)

        if build_plan is None:
            self.fail("expected watch build plan")
        units = build_owned_units(build_plan)
        site_root = workspace_root / "site"
        dirty_unit_ids = _dirty_unit_ids_for_paths(
            build_plan=build_plan,
            units=units,
            dirty_paths=(workspace_root / "site/provider-snapshot.json",),
            workspace_root=workspace_root,
            site_root=site_root,
            catalog_path=site_root / "catalog.yaml",
            provider_snapshot_path=site_root / "provider-snapshot.json",
        )

        self.assertEqual(dirty_unit_ids, frozenset(unit.unit_id for unit in units))

    def test_dirty_unit_mapping_broadens_catalog_metadata_changes_to_all_units(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            _expand_workspace_for_multiple_owned_units(workspace_root)
            build_plan = _build_plan(workspace_root)

        if build_plan is None:
            self.fail("expected watch build plan")
        units = build_owned_units(build_plan)
        site_root = workspace_root / "site"
        dirty_unit_ids = _dirty_unit_ids_for_paths(
            build_plan=build_plan,
            units=units,
            dirty_paths=(workspace_root / "site/catalog.yaml",),
            workspace_root=workspace_root,
            site_root=site_root,
            catalog_path=site_root / "catalog.yaml",
            provider_snapshot_path=site_root / "provider-snapshot.json",
        )

        self.assertEqual(dirty_unit_ids, frozenset(unit.unit_id for unit in units))

    @mock.patch.dict("os.environ", {"WATCHFILES_FORCE_POLLING": "1"}, clear=False)
    def test_watch_event_stream_still_collects_changes_when_polling_is_forced(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            changed_file = workspace_root / "components/runtime/docs/index.md"
            fake_events = iter(({(None, str(changed_file))}, set()))
            with mock.patch(
                "buildish_site_pipeline.commands.watch_events.watch",
                return_value=fake_events,
            ):
                stream = _WatchEventStream(
                    watch_roots=(workspace_root,),
                    stage_root=workspace_root / "site/.stage",
                    work_root=workspace_root / ".buildish/work",
                    report_output=None,
                    event_output=None,
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
            with mock.patch(
                "buildish_site_pipeline.commands.watch_events.watch",
                return_value=fake_events,
            ):
                stream = _WatchEventStream(
                    watch_roots=(workspace_root,),
                    stage_root=workspace_root / "site/.stage",
                    work_root=workspace_root / ".buildish/work",
                    report_output=None,
                    event_output=None,
                    stop_event=threading.Event(),
                )
                try:
                    dirty_paths = stream.collect_dirty_paths(wait_for_first=True)
                finally:
                    stream.close()

        self.assertEqual(dirty_paths, (noisy_grandparent.resolve(strict=False),))

    @mock.patch.dict("os.environ", {"WATCHFILES_FORCE_POLLING": "1"}, clear=False)
    def test_watch_event_stream_returns_empty_tuple_for_poll_timeout_after_startup(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            fake_events = iter((set(),))
            with mock.patch(
                "buildish_site_pipeline.commands.watch_events.watch",
                return_value=fake_events,
            ):
                stream = _WatchEventStream(
                    watch_roots=(workspace_root,),
                    stage_root=workspace_root / "site/.stage",
                    work_root=workspace_root / ".buildish/work",
                    report_output=None,
                    event_output=None,
                    stop_event=threading.Event(),
                )
                try:
                    dirty_paths = stream.collect_dirty_paths(wait_for_first=False)
                finally:
                    stream.close()

        self.assertEqual(dirty_paths, ())

    @mock.patch.dict("os.environ", {"WATCHFILES_FORCE_POLLING": "1"}, clear=False)
    def test_watch_event_stream_prime_advances_the_native_generator(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            raw_events = mock.MagicMock()
            raw_events.__next__.return_value = set()
            with mock.patch(
                "buildish_site_pipeline.commands.watch_events.watch",
                return_value=raw_events,
            ):
                stream = _WatchEventStream(
                    watch_roots=(workspace_root,),
                    stage_root=workspace_root / "site/.stage",
                    work_root=workspace_root / ".buildish/work",
                    report_output=None,
                    event_output=None,
                    stop_event=threading.Event(),
                )
                try:
                    primed = stream.prime()
                finally:
                    stream.close()

        self.assertTrue(primed)
        raw_events.__next__.assert_called_once_with()

    @mock.patch.dict("os.environ", {"WATCHFILES_FORCE_POLLING": "1"}, clear=False)
    def test_watch_event_stream_replacement_closes_and_primes_new_generator(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            first_root = workspace_root / "components/first"
            second_root = workspace_root / "components/second"
            first_events = mock.MagicMock()
            second_events = mock.MagicMock()
            second_events.__next__.return_value = set()
            with mock.patch(
                "buildish_site_pipeline.commands.watch_events.watch",
                side_effect=(first_events, second_events),
            ) as open_watch:
                stream = _WatchEventStream(
                    watch_roots=(first_root,),
                    stage_root=workspace_root / "site/.stage",
                    work_root=workspace_root / ".buildish/work",
                    report_output=None,
                    event_output=None,
                    stop_event=threading.Event(),
                )
                try:
                    replaced = stream.replace_watch_roots((second_root,))
                finally:
                    stream.close()

        self.assertTrue(replaced)
        self.assertEqual(stream.watch_roots, (second_root,))
        self.assertEqual(open_watch.call_count, 2)
        self.assertEqual(open_watch.call_args_list[1].args, (str(second_root),))
        first_events.close.assert_called_once_with()
        second_events.__next__.assert_called_once_with()
        second_events.close.assert_called_once_with()

    @mock.patch.dict("os.environ", {"WATCHFILES_FORCE_POLLING": "1"}, clear=False)
    def test_watch_event_stream_collects_from_replacement_root(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            first_root = workspace_root / "components/first"
            second_root = workspace_root / "components/second"
            first_root.mkdir(parents=True)
            second_root.mkdir(parents=True)
            stop_event = threading.Event()
            stream = _WatchEventStream(
                watch_roots=(first_root,),
                stage_root=workspace_root / "site/.stage",
                work_root=workspace_root / ".buildish/work",
                report_output=None,
                event_output=None,
                stop_event=stop_event,
            )
            try:
                self.assertTrue(stream.prime())
                self.assertTrue(stream.replace_watch_roots((second_root,)))
                ignored_file = first_root / "ignored.md"
                watched_file = second_root / "watched.md"
                ignored_file.write_text("old root\n", encoding="utf-8")
                watched_file.write_text("new root\n", encoding="utf-8")

                dirty_paths = stream.collect_dirty_paths(wait_for_first=True)
            finally:
                stop_event.set()
                stream.close()

        if dirty_paths is None:
            self.fail("replacement watcher stopped before observing the new root")
        self.assertTrue(
            any(
                watched_file.resolve(strict=False) == dirty_path
                or watched_file.resolve(strict=False).is_relative_to(dirty_path)
                for dirty_path in dirty_paths
            )
        )
        self.assertFalse(
            any(
                ignored_file.resolve(strict=False) == dirty_path
                or ignored_file.resolve(strict=False).is_relative_to(dirty_path)
                for dirty_path in dirty_paths
            )
        )

    @mock.patch.dict("os.environ", {"WATCHFILES_FORCE_POLLING": "1"}, clear=False)
    def test_watch_event_stream_returns_none_when_shutdown_is_already_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            stop_event = threading.Event()
            stop_event.set()
            with mock.patch(
                "buildish_site_pipeline.commands.watch_events.watch",
                return_value=iter(()),
            ):
                stream = _WatchEventStream(
                    watch_roots=(workspace_root,),
                    stage_root=workspace_root / "site/.stage",
                    work_root=workspace_root / ".buildish/work",
                    report_output=None,
                    event_output=None,
                    stop_event=stop_event,
                )
                try:
                    dirty_paths = stream.collect_dirty_paths(wait_for_first=True)
                finally:
                    stream.close()

        self.assertIsNone(dirty_paths)

    @mock.patch.dict("os.environ", {"WATCHFILES_FORCE_POLLING": "1"}, clear=False)
    def test_watch_event_stream_close_closes_the_underlying_iterator(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            raw_events = mock.Mock()
            with mock.patch(
                "buildish_site_pipeline.commands.watch_events.watch",
                return_value=raw_events,
            ):
                stream = _WatchEventStream(
                    watch_roots=(workspace_root,),
                    stage_root=workspace_root / "site/.stage",
                    work_root=workspace_root / ".buildish/work",
                    report_output=None,
                    event_output=None,
                    stop_event=threading.Event(),
                )
                stream.close()

        raw_events.close.assert_called_once_with()

    def test_watch_event_output_supports_disabled_stdout_and_file_sinks(self) -> None:
        stdout = io.StringIO()

        with _open_watch_event_output(request=None, stdout=stdout) as sink:
            self.assertIsNone(sink)

        with _open_watch_event_output(
            request=WatchEventRequest(
                event_format=WatchEventFormat.JSONL,
                output_path=None,
            ),
            stdout=stdout,
        ) as sink:
            if sink is None:
                self.fail("expected stdout-backed event sink")
            sink.write("stdout-event\n")

        with tempfile.TemporaryDirectory() as tempdir:
            output_path = Path(tempdir) / "events.jsonl"
            with _open_watch_event_output(
                request=WatchEventRequest(
                    event_format=WatchEventFormat.JSONL,
                    output_path=output_path,
                ),
                stdout=stdout,
            ) as sink:
                if sink is None:
                    self.fail("expected file-backed event sink")
                sink.write("file-event\n")

            self.assertEqual(output_path.read_text(encoding="utf-8"), "file-event\n")

        self.assertEqual(stdout.getvalue(), "stdout-event\n")

    def test_watch_event_output_requires_a_path_for_file_backed_sinks(self) -> None:
        request = SimpleNamespace(writes_to_stdout=False, output_path=None)

        with self.assertRaisesRegex(AssertionError, "must exist for file-backed sinks"):
            with _open_watch_event_output(request=request, stdout=io.StringIO()):
                pass

    def test_watch_io_emits_jsonl_cycle_and_ready_events(self) -> None:
        sink = io.StringIO()
        watch_io = _WatchIo(
            event_request=WatchEventRequest(
                event_format=WatchEventFormat.JSONL,
                output_path=None,
            ),
            event_sink=sink,
        )
        successful_report = _watch_report(cycle=2)
        failed_report = _watch_report(
            cycle=3,
            succeeded=False,
            wrote_stage=False,
            stage_usable=True,
            status=RunStatus.ERRORS,
            error_count=1,
        )

        watch_io.emit_cycle_event(successful_report)
        watch_io.emit_cycle_event(failed_report)
        watch_io.emit_ready(successful_report)

        payloads = [json.loads(line) for line in sink.getvalue().splitlines()]
        self.assertEqual(
            [payload["event"] for payload in payloads],
            ["cycle-succeeded", "cycle-failed", "ready"],
        )
        self.assertEqual(payloads[0]["cycle"], 2)
        self.assertEqual(payloads[1]["errorCount"], 1)

    def test_watch_io_rejects_missing_sink_and_unknown_event_format(self) -> None:
        ready_report = _watch_report(cycle=4)
        missing_sink_io = _WatchIo(
            event_request=WatchEventRequest(
                event_format=WatchEventFormat.JSONL,
                output_path=None,
            ),
            event_sink=None,
        )
        unsupported_format_io = _WatchIo(
            event_request=SimpleNamespace(event_format="yaml"),
            event_sink=io.StringIO(),
        )

        with self.assertRaisesRegex(AssertionError, "sink must exist"):
            missing_sink_io.emit_ready(ready_report)

        with self.assertRaisesRegex(AssertionError, "Unsupported watch event format"):
            unsupported_format_io.emit_ready(ready_report)

    def test_watch_io_emit_cycle_log_records_initial_scan_summary(self) -> None:
        watch_io = _WatchIo(event_request=None, event_sink=None)

        with self.assertLogs(logging.getLogger(watch_command.__name__), level="INFO") as captured:
            watch_io.emit_cycle_log(
                report=_watch_report(cycle=1),
                dirty_paths=(),
                watch_roots=(Path("/workspace"),),
            )

        output = "\n".join(captured.output)
        self.assertIn("watch cycle 1:", output)
        self.assertIn("watch dirty path count: <initial scan>", output)
        self.assertIn("watch root count: 1", output)
        self.assertNotIn("watch debug dirty paths", output)

    def test_watch_io_emit_cycle_log_records_debug_dirty_paths_and_roots(self) -> None:
        watch_io = _WatchIo(event_request=None, event_sink=None)

        with self.assertLogs(logging.getLogger(watch_command.__name__), level="DEBUG") as captured:
            watch_io.emit_cycle_log(
                report=_watch_report(cycle=5),
                dirty_paths=(Path("/workspace/site/catalog.yaml"),),
                watch_roots=(Path("/workspace"), Path("/catalog")),
            )

        output = "\n".join(captured.output)
        self.assertIn("watch dirty path count: 1", output)
        self.assertIn("watch debug dirty paths: /workspace/site/catalog.yaml", output)
        self.assertIn("watch debug roots: /workspace, /catalog", output)

    def test_graceful_watch_shutdown_marks_stop_event_and_restores_handlers(self) -> None:
        previous_sigint = signal.getsignal(signal.SIGINT)

        with _graceful_watch_shutdown() as controller:
            current_sigint = signal.getsignal(signal.SIGINT)
            self.assertIsNot(current_sigint, previous_sigint)
            current_sigint(signal.SIGINT, None)
            self.assertTrue(controller.shutdown_requested)
            self.assertTrue(controller.stop_event.is_set())

        self.assertIs(signal.getsignal(signal.SIGINT), previous_sigint)

    def test_emit_cycle_report_skips_revalidation_when_no_output_path_is_configured(self) -> None:
        invocation = _watch_invocation(Path("/workspace"))

        with mock.patch.object(watch_command, "revalidate_report_request") as revalidate, mock.patch.object(
            watch_command,
            "emit_report",
        ) as emit:
            _emit_cycle_report(
                invocation=invocation,
                report=_watch_report(cycle=1),
                stdout=io.StringIO(),
            )

        revalidate.assert_not_called()
        emit.assert_not_called()

    def test_emit_cycle_report_revalidates_and_emits_file_backed_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            invocation = _watch_invocation(
                workspace_root,
                report_output=workspace_root / "watch-report.json",
            )
            report = _watch_report(cycle=2)
            stdout = io.StringIO()

            with mock.patch.object(
                watch_command,
                "revalidate_report_request",
                return_value=invocation.report_request,
            ) as revalidate, mock.patch.object(
                watch_command,
                "emit_report",
            ) as emit, mock.patch.object(
                watch_command,
                "render_text_report",
                return_value="watch rendered",
            ) as render:
                _emit_cycle_report(invocation=invocation, report=report, stdout=stdout)

        revalidate.assert_called_once_with(
            cwd=invocation.layout.cwd,
            request=invocation.report_request,
            forbidden_roots=(invocation.layout.stage_root, invocation.layout.work_root),
        )
        render.assert_called_once_with(report)
        emit.assert_called_once_with(
            request=invocation.report_request,
            report=report,
            text_output="watch rendered",
            stdout=stdout,
        )

    def test_failed_cycle_outcome_reuses_prior_trusted_stage_metadata(self) -> None:
        trusted_stage = SimpleNamespace(
            stage_root=Path("/workspace/site/.stage"),
            manifest_path=Path("/workspace/site/.stage/manifest.json"),
        )
        diagnostics = (
            PipelineDiagnosticEntry(
                severity=DiagnosticSeverity.ERROR,
                code="watch.failure",
                message="broken",
            ),
        )

        outcome = _failed_cycle_outcome(
            cycle_number=7,
            trusted_stage=trusted_stage,
            prior_watch_roots=(Path("/workspace"),),
            diagnostics=diagnostics,
        )

        self.assertTrue(outcome.report.summary.stage_usable)
        self.assertEqual(outcome.report.stage_root_path, str(trusted_stage.stage_root))
        self.assertEqual(outcome.watch_roots, (Path("/workspace"),))

    def test_run_follow_up_cycle_raises_when_cycle_leaves_no_trusted_stage(self) -> None:
        invocation = _watch_invocation(Path("/workspace"))
        prior_stage = SimpleNamespace(
            stage_root=Path("/workspace/site/.stage"),
            manifest_path=Path("/workspace/site/.stage/manifest.json"),
        )
        failed_outcome = SimpleNamespace(
            report=_watch_report(
                cycle=2,
                succeeded=False,
                wrote_stage=False,
                stage_usable=False,
                status=RunStatus.ERRORS,
                error_count=1,
            ),
            trusted_stage=None,
            watch_roots=(Path("/workspace"),),
        )
        watch_io = mock.Mock()

        with mock.patch.object(watch_command, "_run_watch_cycle", return_value=failed_outcome):
            with self.assertRaisesRegex(StageIntegrityError, "left no trustworthy stage"):
                _run_follow_up_cycle(
                    invocation=invocation,
                    cycle_number=1,
                    trusted_stage=prior_stage,
                    last_watch_roots=(Path("/workspace"),),
                    dirty_paths=(Path("/workspace/site/catalog.yaml"),),
                    stdout=io.StringIO(),
                    watch_io=watch_io,
                )

    def test_run_follow_up_cycle_returns_explicit_outcome(self) -> None:
        invocation = _watch_invocation(Path("/workspace"))
        prior_stage = SimpleNamespace(
            stage_root=Path("/workspace/site/.stage"),
            manifest_path=Path("/workspace/site/.stage/manifest.json"),
        )
        report = _watch_report(cycle=2, succeeded=True, wrote_stage=True, stage_usable=True)
        watch_outcome = SimpleNamespace(
            report=report,
            trusted_stage=prior_stage,
            watch_roots=(Path("/workspace"), Path("/workspace/components")),
        )
        watch_io = mock.Mock()

        with mock.patch.object(watch_command, "_run_watch_cycle", return_value=watch_outcome):
            outcome = _run_follow_up_cycle(
                invocation=invocation,
                cycle_number=1,
                trusted_stage=prior_stage,
                last_watch_roots=(Path("/workspace"),),
                dirty_paths=(Path("/workspace/site/catalog.yaml"),),
                stdout=io.StringIO(),
                watch_io=watch_io,
            )

        self.assertEqual(outcome.cycle_number, 2)
        self.assertIs(outcome.report, report)
        self.assertIs(outcome.trusted_stage, prior_stage)
        self.assertEqual(outcome.watch_roots, watch_outcome.watch_roots)

        watch_io.emit_cycle_event.assert_called_once_with(watch_outcome.report)
        watch_io.emit_cycle_log.assert_called_once()

    def test_stage_path_is_claimed_handles_exact_and_nested_claims(self) -> None:
        self.assertTrue(
            _stage_path_is_claimed(
                "content/spark/index.md",
                {"content/spark"},
                set(),
            ),
        )
        self.assertTrue(
            _stage_path_is_claimed(
                "content",
                set(),
                {"content/spark/index.md"},
            ),
        )
        self.assertFalse(
            _stage_path_is_claimed(
                "content/flink/index.md",
                {"content/spark"},
                set(),
            ),
        )

    def test_run_watch_rejects_same_report_and_event_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            output_path = workspace_root / "watch-output.json"
            invocation = WatchInvocation(
                layout=_watch_invocation(workspace_root).layout,
                fail_on_severity=CheckFailureThreshold.ERROR,
                report_request=ReportRequest(
                    report_format=ReportFormat.JSON,
                    schema_version=1,
                    output_path=output_path,
                ),
                unstable_event_request=WatchEventRequest(
                    event_format=WatchEventFormat.JSONL,
                    output_path=output_path,
                ),
            )

            with self.assertRaisesRegex(InvocationError, "must differ"):
                run_watch(invocation, stdout=io.StringIO())

    def test_run_watch_cycle_returns_failed_report_when_stage_gate_blocks_build(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            invocation = _watch_invocation(workspace_root)
            prior_watch_roots = (workspace_root,)
            trusted_stage = _trusted_stage(workspace_root / "site/.stage")
            planning = SimpleNamespace(watch_plan=None)
            evaluation = SimpleNamespace(
                stage_gate=SimpleNamespace(allowed=False),
                build_plan=None,
                diagnostics=(
                    PipelineDiagnosticEntry(
                        severity=DiagnosticSeverity.ERROR,
                        code="watch.blocked",
                        message="blocked",
                    ),
                ),
            )
            loaded_inputs = SimpleNamespace(
                catalog=object(),
                catalog_path=invocation.layout.catalog_path,
                provider_snapshot=object(),
                provider_snapshot_path=None,
                component_documents=object(),
            )

            with mock.patch.object(
                watch_command,
                "load_workspace_inputs",
                return_value=loaded_inputs,
            ), mock.patch.object(
                watch_command,
                "evaluate_planning",
                return_value=planning,
            ), mock.patch.object(
                watch_command,
                "run_evaluation",
                return_value=evaluation,
            ), mock.patch.object(
                watch_command,
                "build_stage_run_report",
                return_value=_watch_report(
                    cycle=3,
                    succeeded=False,
                    wrote_stage=False,
                    stage_usable=True,
                    status=RunStatus.ERRORS,
                    error_count=1,
                ),
            ):
                outcome = _run_watch_cycle(
                    invocation=invocation,
                    cycle_number=3,
                    trusted_stage=trusted_stage,
                    prior_watch_roots=prior_watch_roots,
                    dirty_paths=(),
                )

        self.assertIs(outcome.trusted_stage, trusted_stage)
        self.assertEqual(outcome.watch_roots, prior_watch_roots)
        self.assertFalse(outcome.report.summary.succeeded)

    def test_run_watch_cycle_returns_failed_outcome_when_build_raises_stage_integrity_error(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            _expand_workspace_for_multiple_owned_units(workspace_root)
            invocation = _watch_invocation(workspace_root)
            build_plan = _build_plan(workspace_root)
            planning = SimpleNamespace(watch_plan=None)
            evaluation = SimpleNamespace(
                stage_gate=SimpleNamespace(allowed=True),
                build_plan=build_plan,
                diagnostics=(),
            )
            loaded_inputs = SimpleNamespace(
                catalog=object(),
                provider_snapshot=object(),
                component_documents=object(),
                catalog_path=workspace_root / "site/catalog.yaml",
                provider_snapshot_path=workspace_root / "provider-snapshot.json",
            )
            sentinel = SimpleNamespace(report=_watch_report(cycle=4), trusted_stage=None, watch_roots=(workspace_root,))

            with mock.patch.object(
                watch_command,
                "load_workspace_inputs",
                return_value=loaded_inputs,
            ), mock.patch.object(
                watch_command,
                "evaluate_planning",
                return_value=planning,
            ), mock.patch.object(
                watch_command,
                "run_evaluation",
                return_value=evaluation,
            ), mock.patch.object(
                watch_command,
                "_select_incremental_build",
                return_value=watch_command.IncrementalBuildSelection(),
            ), mock.patch.object(
                watch_command,
                "run_build",
                side_effect=StageIntegrityError("boom"),
            ), mock.patch.object(
                watch_command,
                "_failed_cycle_outcome",
                return_value=sentinel,
            ) as failed_outcome:
                outcome = _run_watch_cycle(
                    invocation=invocation,
                    cycle_number=4,
                    trusted_stage=None,
                    prior_watch_roots=(workspace_root,),
                    dirty_paths=(workspace_root / "site/content/index.md",),
                )

        self.assertIs(outcome, sentinel)
        failed_outcome.assert_called_once()

    def test_run_watch_cycle_returns_failed_outcome_when_published_stage_is_not_trusted(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            _expand_workspace_for_multiple_owned_units(workspace_root)
            invocation = _watch_invocation(workspace_root)
            build_plan = _build_plan(workspace_root)
            planning = SimpleNamespace(watch_plan=None)
            evaluation = SimpleNamespace(
                stage_gate=SimpleNamespace(allowed=True),
                build_plan=build_plan,
                diagnostics=(),
            )
            loaded_inputs = SimpleNamespace(
                catalog=object(),
                provider_snapshot=object(),
                component_documents=object(),
                catalog_path=workspace_root / "site/catalog.yaml",
                provider_snapshot_path=workspace_root / "provider-snapshot.json",
            )
            build_outcome = SimpleNamespace(
                layout=SimpleNamespace(next_stage_root=workspace_root / "site/.stage.next"),
            )
            publication = SimpleNamespace(stage_root=workspace_root / "site/.stage", manifest_path=workspace_root / "site/.stage/manifest.json")
            sentinel = SimpleNamespace(report=_watch_report(cycle=5), trusted_stage=None, watch_roots=(workspace_root,))

            with mock.patch.object(
                watch_command,
                "load_workspace_inputs",
                return_value=loaded_inputs,
            ), mock.patch.object(
                watch_command,
                "evaluate_planning",
                return_value=planning,
            ), mock.patch.object(
                watch_command,
                "run_evaluation",
                return_value=evaluation,
            ), mock.patch.object(
                watch_command,
                "_select_incremental_build",
                return_value=watch_command.IncrementalBuildSelection(),
            ), mock.patch.object(
                watch_command,
                "run_build",
                return_value=build_outcome,
            ), mock.patch.object(
                watch_command,
                "finalize_stage_publication",
                return_value=publication,
            ), mock.patch.object(
                watch_command,
                "cleanup_after_publication",
            ), mock.patch.object(
                watch_command.shutil,
                "rmtree",
            ), mock.patch.object(
                watch_command,
                "_load_trusted_stage",
                return_value=None,
            ), mock.patch.object(
                watch_command,
                "_failed_cycle_outcome",
                return_value=sentinel,
            ) as failed_outcome:
                outcome = _run_watch_cycle(
                    invocation=invocation,
                    cycle_number=5,
                    trusted_stage=None,
                    prior_watch_roots=(workspace_root,),
                    dirty_paths=(workspace_root / "site/content/index.md",),
                )

        self.assertIs(outcome, sentinel)
        failed_outcome.assert_called_once()

    def test_dirty_unit_ids_detect_site_vendor_and_component_inputs(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            _expand_workspace_for_multiple_owned_units(workspace_root)
            build_plan = _build_plan(workspace_root)
            units = build_owned_units(build_plan)
            vendor_asset = build_plan.site.vendor_assets[0].source_path
            component = build_plan.site.components[0]

            self.assertEqual(
                _dirty_unit_ids_for_paths(
                    build_plan=build_plan,
                    units=units,
                    dirty_paths=(build_plan.site.site_pages_root / "index.md",),
                    workspace_root=workspace_root,
                    site_root=workspace_root / "site",
                    catalog_path=workspace_root / "site/catalog.yaml",
                    provider_snapshot_path=None,
                ),
                frozenset({"site-pages"}),
            )
            self.assertEqual(
                _dirty_unit_ids_for_paths(
                    build_plan=build_plan,
                    units=units,
                    dirty_paths=(build_plan.site.site_assets_root / "robots.txt",),
                    workspace_root=workspace_root,
                    site_root=workspace_root / "site",
                    catalog_path=workspace_root / "site/catalog.yaml",
                    provider_snapshot_path=None,
                ),
                frozenset({"site-assets"}),
            )
            self.assertEqual(
                _dirty_unit_ids_for_paths(
                    build_plan=build_plan,
                    units=units,
                    dirty_paths=(vendor_asset,),
                    workspace_root=workspace_root,
                    site_root=workspace_root / "site",
                    catalog_path=workspace_root / "site/catalog.yaml",
                    provider_snapshot_path=None,
                ),
                frozenset({"vendor-assets"}),
            )
            self.assertEqual(
                _dirty_unit_ids_for_paths(
                    build_plan=build_plan,
                    units=units,
                    dirty_paths=(component.content_source.local_dir / "README.md",),
                    workspace_root=workspace_root,
                    site_root=workspace_root / "site",
                    catalog_path=workspace_root / "site/catalog.yaml",
                    provider_snapshot_path=None,
                ),
                frozenset({f"component:{component.slug}"}),
            )

    def test_dirty_unit_ids_return_all_units_for_site_or_workspace_root_changes(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            _expand_workspace_for_multiple_owned_units(workspace_root)
            build_plan = _build_plan(workspace_root)
            units = build_owned_units(build_plan)
            current_unit_ids = frozenset(unit.unit_id for unit in units)
            site_root = workspace_root / "site"

            self.assertEqual(
                _dirty_unit_ids_for_paths(
                    build_plan=build_plan,
                    units=units,
                    dirty_paths=(site_root,),
                    workspace_root=workspace_root,
                    site_root=site_root,
                    catalog_path=workspace_root / "site/catalog.yaml",
                    provider_snapshot_path=None,
                ),
                current_unit_ids,
            )
            self.assertEqual(
                _dirty_unit_ids_for_paths(
                    build_plan=build_plan,
                    units=units,
                    dirty_paths=(workspace_root,),
                    workspace_root=workspace_root,
                    site_root=site_root,
                    catalog_path=workspace_root / "site/catalog.yaml",
                    provider_snapshot_path=None,
                ),
                current_unit_ids,
            )

    def test_dirty_component_unit_id_returns_none_for_unmatched_paths(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            _expand_workspace_for_multiple_owned_units(workspace_root)
            build_plan = _build_plan(workspace_root)

            self.assertIsNone(
                _dirty_component_unit_id(
                    build_plan=build_plan,
                    dirty_path=workspace_root / "README.md",
                ),
            )

    def test_is_pipeline_owned_path_detects_exact_report_output_and_optional_event_output(self) -> None:
        stage_root = Path("/workspace/site/.stage")
        work_root = Path("/workspace/site/.site-pipeline-work")
        report_output = Path("/workspace/watch-report.json")
        generated_build_path = Path("/workspace/site/build/fake-hugo.log")
        generated_resource_parent = Path("/workspace/site/resources")
        generated_resource = Path("/workspace/site/resources/_gen/assets/main.css")

        self.assertTrue(
            _is_pipeline_owned_path(
                path=report_output,
                stage_root=stage_root,
                work_root=work_root,
                report_output=report_output,
                event_output=None,
            ),
        )
        self.assertTrue(
            _is_pipeline_owned_path(
                path=generated_build_path,
                stage_root=stage_root,
                work_root=work_root,
                report_output=None,
                event_output=None,
            ),
        )
        self.assertTrue(
            _is_pipeline_owned_path(
                path=generated_resource_parent,
                stage_root=stage_root,
                work_root=work_root,
                report_output=None,
                event_output=None,
            ),
        )
        self.assertTrue(
            _is_pipeline_owned_path(
                path=generated_resource,
                stage_root=stage_root,
                work_root=work_root,
                report_output=None,
                event_output=None,
            ),
        )
        self.assertFalse(
            _is_pipeline_owned_path(
                path=Path("/workspace/site/content/index.md"),
                stage_root=stage_root,
                work_root=work_root,
                report_output=None,
                event_output=None,
            ),
        )

    def test_load_trusted_stage_returns_none_when_manifest_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            stage_root = Path(tempdir) / "stage"
            stage_root.mkdir()

            self.assertIsNone(_load_trusted_stage(stage_root))


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
    return planning.build_plan_result.candidate


def _watch_invocation(
    workspace_root: Path,
    *,
    report_output: Path | None = None,
) -> WatchInvocation:
    site_root = workspace_root / "site"
    return WatchInvocation(
        layout=RepositoryLayout(
            cwd=workspace_root,
            workspace_root=workspace_root,
            catalog_path=site_root / "catalog.yaml",
            site_root=site_root,
            stage_root=site_root / ".stage",
            work_root=site_root / ".site-pipeline-work",
        ),
        fail_on_severity=CheckFailureThreshold.ERROR,
        report_request=ReportRequest(
            report_format=ReportFormat.TEXT,
            schema_version=None,
            output_path=report_output,
        ),
        unstable_event_request=None,
    )


def _trusted_stage(stage_root: Path) -> TrustedStageState:
    stage_root.mkdir(parents=True, exist_ok=True)
    _write_stage_manifest(stage_root)
    manifest_path = stage_root / "manifest.json"
    manifest = load_stage_manifest(
        manifest_path.read_text(encoding="utf-8"),
        document_format=DocumentFormat.JSON,
        source_name=str(manifest_path),
    )
    return TrustedStageState(
        stage_root=stage_root,
        manifest_path=manifest_path,
        manifest=manifest,
        incremental_state=None,
    )


def _watch_report(
    *,
    cycle: int,
    succeeded: bool = True,
    wrote_stage: bool = True,
    stage_usable: bool = True,
    status: RunStatus = RunStatus.CLEAN,
    error_count: int = 0,
    warning_count: int = 0,
    info_count: int = 0,
) -> StageRunReportV1:
    return StageRunReportV1(
        schema_version=1,
        generated_at=datetime(2026, 4, 5, tzinfo=UTC),
        command=StageCommand.WATCH,
        summary=StageRunSummary(
            status=status,
            succeeded=succeeded,
            wrote_stage=wrote_stage,
            stage_usable=stage_usable,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
        ),
        stage_root_path="/workspace/site/.stage" if stage_usable else None,
        manifest_path="/workspace/site/.stage/manifest.json" if stage_usable else None,
        cycle=cycle,
        diagnostics=[],
    )
