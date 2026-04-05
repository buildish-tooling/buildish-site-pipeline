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

"""End-to-end-ish CLI tests over the real command surface."""

from __future__ import annotations

import io
import importlib
import json
import logging
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from apache_buildish_site_pipeline.cli import _run
from apache_buildish_site_pipeline.cli import main as cli_main, parse_invocation
from apache_buildish_site_pipeline.cli.contract import (
    ReportFormat,
    ReportRequest,
    RepositoryLayout,
    WatchCycleFailedEvent,
    WatchCycleSucceededEvent,
    WatchEventFormat,
    WatchEventRequest,
    WatchInvocation,
    WatchReadyEvent,
)
from apache_buildish_site_pipeline.cli.dispatch import dispatch_command as _dispatch_command
from apache_buildish_site_pipeline.cli.errors import CommandExecutionError, InvocationError, SitePipelineCliError
from apache_buildish_site_pipeline.models.enums import CheckFailureThreshold, RunStatus
from tests.support.workspace import _cwd, _fake_watch_event_stream_factory, _workspace


cli_main_module = importlib.import_module("apache_buildish_site_pipeline.cli.main")


class CliTests(unittest.TestCase):
    def test_watch_event_classes_serialize_expected_payloads(self) -> None:
        stage_root_path = "/workspace/stage"
        manifest_path = f"{stage_root_path}/manifest.json"
        ready_event = WatchReadyEvent(
            cycle=3,
            stage_root_path=stage_root_path,
            manifest_path=manifest_path,
        )
        succeeded_event = WatchCycleSucceededEvent(
            cycle=4,
            stage_root_path=stage_root_path,
            manifest_path=manifest_path,
            status=RunStatus.CLEAN,
            succeeded=True,
            wrote_stage=True,
            stage_usable=True,
            error_count=0,
            warning_count=1,
            info_count=2,
        )
        failed_event = WatchCycleFailedEvent(
            cycle=5,
            stage_root_path=None,
            manifest_path=None,
            status=RunStatus.ERRORS,
            succeeded=False,
            wrote_stage=False,
            stage_usable=False,
            error_count=1,
            warning_count=0,
            info_count=0,
        )

        self.assertEqual(
            ready_event.to_json_payload(),
            {
                "event": "ready",
                "cycle": 3,
                "stageRootPath": "/workspace/stage",
                "manifestPath": "/workspace/stage/manifest.json",
            },
        )
        self.assertEqual(
            succeeded_event.to_json_payload(),
            {
                "event": "cycle-succeeded",
                "cycle": 4,
                "stageRootPath": "/workspace/stage",
                "manifestPath": "/workspace/stage/manifest.json",
                "status": "clean",
                "succeeded": True,
                "wroteStage": True,
                "stageUsable": True,
                "errorCount": 0,
                "warningCount": 1,
                "infoCount": 2,
            },
        )
        self.assertEqual(
            failed_event.to_json_payload(),
            {
                "event": "cycle-failed",
                "cycle": 5,
                "stageRootPath": None,
                "manifestPath": None,
                "status": "errors",
                "succeeded": False,
                "wroteStage": False,
                "stageUsable": False,
                "errorCount": 1,
                "warningCount": 0,
                "infoCount": 0,
            },
        )

    def test_plan_json_report_to_stdout(self) -> None:
        with _workspace() as workspace_root:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(
                    argv=["plan", "--for", "build", "--report-format", "json", "--report-schema-version", "1"],
                    stdout=stdout,
                    stderr=stderr,
                )

        report = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(report["target"], "build")
        self.assertGreaterEqual(len(report["entries"]), 1)
        self.assertEqual(stderr.getvalue(), "")

    def test_check_json_report_respects_fail_on(self) -> None:
        with _workspace() as workspace_root:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(
                    argv=["check", "--fail-on", "error", "--report-format", "json", "--report-schema-version", "1"],
                    stdout=stdout,
                    stderr=stderr,
                )

        report = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertTrue(report["summary"]["passed"])
        self.assertEqual(stderr.getvalue(), "")

    def test_build_creates_stage_and_manifest(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(
                    argv=["build", "--report-format", "json", "--report-schema-version", "1"],
                    stdout=stdout,
                    stderr=stderr,
                )

            report = json.loads(stdout.getvalue())
            manifest_path = workspace_root / "site/.stage/manifest.json"
            staged_file = workspace_root / "site/.stage/content/components/spark/contexts/releases/4.0.0/index.md"

            self.assertEqual(exit_code, 0)
            self.assertTrue(report["summary"]["succeeded"])
            self.assertTrue(manifest_path.exists())
            self.assertTrue(staged_file.exists())
            self.assertEqual(stderr.getvalue(), "")

    def test_build_supports_explicit_workspace_root_and_catalog(self) -> None:
        with _workspace(with_content_file=True) as workspace_root, tempfile.TemporaryDirectory() as runner_dir, tempfile.TemporaryDirectory() as catalog_dir:
            runner_root = Path(runner_dir)
            catalog_site_root = Path(catalog_dir)
            authored_site_root = workspace_root / "site"
            (catalog_site_root / "components.yaml").write_text(
                (authored_site_root / "components.yaml").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (catalog_site_root / "provider-snapshot.json").write_text(
                (authored_site_root / "provider-snapshot.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(runner_root):
                exit_code = _run(
                    argv=[
                        "build",
                        "--workspace-root",
                        str(workspace_root),
                        "--catalog",
                        str(catalog_site_root / "components.yaml"),
                        "--report-format",
                        "json",
                        "--report-schema-version",
                        "1",
                        "--report-output",
                        "build-report.json",
                    ],
                    stdout=stdout,
                    stderr=stderr,
                )

            report = json.loads((runner_root / "build-report.json").read_text(encoding="utf-8"))
            manifest_path = catalog_site_root / ".stage/manifest.json"

            self.assertEqual(exit_code, 0)
            self.assertTrue(report["summary"]["succeeded"])
            self.assertTrue(manifest_path.exists())
            self.assertEqual(stderr.getvalue(), "")

    def test_build_rejects_non_empty_stage_root(self) -> None:
        with _workspace() as workspace_root:
            stage_root = workspace_root / "site/.stage"
            stage_root.mkdir(parents=True, exist_ok=True)
            (stage_root / "keep.txt").write_text("x", encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(argv=["build"], stdout=stdout, stderr=stderr)

        self.assertEqual(exit_code, 3)
        self.assertIn("Stage root must be absent or empty", stderr.getvalue())

    def test_build_rejects_stage_root_with_symlinked_parent(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            real_site_root = workspace_root / "real-site"
            (workspace_root / "site").rename(real_site_root)
            (workspace_root / "site").symlink_to(real_site_root, target_is_directory=True)
            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(argv=["build"], stdout=stdout, stderr=stderr)

        self.assertEqual(exit_code, 3)
        self.assertIn("resolves through a symlink", stderr.getvalue())

    def test_plan_revalidates_report_output_before_file_emission(self) -> None:
        with _workspace() as workspace_root:
            reports_dir = workspace_root / "reports"
            reports_dir.mkdir(parents=True, exist_ok=True)
            stdout = io.StringIO()
            stderr = io.StringIO()

            def _dispatch_and_mutate(invocation):
                result = _dispatch_command(invocation)
                real_reports_dir = workspace_root / "real-reports"
                reports_dir.rename(real_reports_dir)
                reports_dir.symlink_to(real_reports_dir, target_is_directory=True)
                return result

            with mock.patch("apache_buildish_site_pipeline.cli.main.dispatch_command", side_effect=_dispatch_and_mutate):
                with _cwd(workspace_root):
                    exit_code = _run(
                        argv=[
                            "plan",
                            "--report-format",
                            "json",
                            "--report-schema-version",
                            "1",
                            "--report-output",
                            "reports/out.json",
                        ],
                        stdout=stdout,
                        stderr=stderr,
                    )

            self.assertEqual(exit_code, 2)
            self.assertEqual(stdout.getvalue(), "")
            self.assertIn("Report output parent directory resolves through a symlink", stderr.getvalue())
            self.assertFalse((workspace_root / "reports/out.json").exists())

    def test_watch_json_stdout_is_rejected(self) -> None:
        with _workspace() as workspace_root:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(
                    argv=["watch", "--report-format", "json", "--report-schema-version", "1"],
                    stdout=stdout,
                    stderr=stderr,
                )

        self.assertEqual(exit_code, 2)
        self.assertIn("watch JSON reports must be written to a file", stderr.getvalue())

    def test_watch_unstable_events_write_jsonl_to_stdout(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            report_path = workspace_root / "watch-report.json"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with mock.patch(
                "apache_buildish_site_pipeline.commands.watch._open_watch_event_stream",
                new=_fake_watch_event_stream_factory(responses=[(True, None)]),
            ):
                with _cwd(workspace_root):
                    exit_code = _run(
                        argv=[
                            "watch",
                            "--quiet",
                            "--unstable-events",
                            "jsonl",
                            "--report-format",
                            "json",
                            "--report-schema-version",
                            "1",
                            "--report-output",
                            str(report_path),
                        ],
                        stdout=stdout,
                        stderr=stderr,
                    )

        events = _parse_jsonl(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual([event["event"] for event in events], ["cycle-succeeded", "ready"])
        self.assertEqual(events[0]["cycle"], 1)
        self.assertEqual(events[1]["cycle"], 1)
        self.assertEqual(stderr.getvalue(), "")

    def test_watch_unstable_events_keep_human_report_on_stderr_when_stdout_is_reserved(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with mock.patch(
                "apache_buildish_site_pipeline.commands.watch._open_watch_event_stream",
                new=_fake_watch_event_stream_factory(responses=[(True, None)]),
            ):
                with _cwd(workspace_root):
                    exit_code = _run(
                        argv=["watch", "--quiet", "--unstable-events", "jsonl"],
                        stdout=stdout,
                        stderr=stderr,
                    )

        events = _parse_jsonl(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual([event["event"] for event in events], ["cycle-succeeded", "ready"])
        self.assertIn("watch clean: succeeded=yes", stderr.getvalue())

    def test_watch_unstable_events_can_write_jsonl_to_a_file_owned_by_watch(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            events_path = workspace_root / "site/.watch-events.jsonl"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with mock.patch(
                "apache_buildish_site_pipeline.commands.watch._open_watch_event_stream",
                new=_fake_watch_event_stream_factory(responses=[(True, None)]),
            ):
                with _cwd(workspace_root):
                    exit_code = _run(
                        argv=[
                            "watch",
                            "--quiet",
                            "--unstable-events",
                            "jsonl",
                            "--unstable-events-output",
                            str(events_path),
                        ],
                        stdout=stdout,
                        stderr=stderr,
                    )
                events = _parse_jsonl(events_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual([event["event"] for event in events], ["cycle-succeeded", "ready"])
        self.assertIn("watch clean: succeeded=yes", stdout.getvalue())
        self.assertEqual(stderr.getvalue(), "")

    def test_watch_unstable_events_output_requires_unstable_events(self) -> None:
        with _workspace() as workspace_root:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(
                    argv=["watch", "--unstable-events-output", "events.jsonl"],
                    stdout=stdout,
                    stderr=stderr,
                )

        self.assertEqual(exit_code, 2)
        self.assertIn("only valid together with --unstable-events", stderr.getvalue())

    def test_watch_unstable_events_output_rejects_same_file_as_report_output(self) -> None:
        with _workspace() as workspace_root:
            shared_path = workspace_root / "events-and-report.json"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(
                    argv=[
                        "watch",
                        "--unstable-events",
                        "jsonl",
                        "--unstable-events-output",
                        str(shared_path),
                        "--report-output",
                        str(shared_path),
                    ],
                    stdout=stdout,
                    stderr=stderr,
                )

        self.assertEqual(exit_code, 2)
        self.assertIn("must differ from --report-output", stderr.getvalue())

    def test_watch_unstable_events_emit_cycle_failed_for_later_failure(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            report_path = workspace_root / "watch-report.json"
            watched_file = workspace_root / "components/runtime/docs/releases/4.0.0/index.md"
            stdout = io.StringIO()
            stderr = io.StringIO()

            def _break_catalog_then_trigger_cycle():
                (workspace_root / "site/components.yaml").unlink()
                return (watched_file,)

            with mock.patch(
                "apache_buildish_site_pipeline.commands.watch._open_watch_event_stream",
                new=_fake_watch_event_stream_factory(
                    responses=[
                        (True, _break_catalog_then_trigger_cycle),
                        (False, None),
                    ],
                ),
            ):
                with _cwd(workspace_root):
                    exit_code = _run(
                        argv=[
                            "watch",
                            "--quiet",
                            "--unstable-events",
                            "jsonl",
                            "--report-format",
                            "json",
                            "--report-schema-version",
                            "1",
                            "--report-output",
                            str(report_path),
                        ],
                        stdout=stdout,
                        stderr=stderr,
                    )

        events = _parse_jsonl(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual([event["event"] for event in events], ["cycle-succeeded", "ready", "cycle-failed"])
        self.assertTrue(events[-1]["stageUsable"])
        self.assertEqual(stderr.getvalue(), "")

    def test_watch_default_writes_lifecycle_summary_to_stderr(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            report_path = workspace_root / "watch-report.json"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with mock.patch(
                "apache_buildish_site_pipeline.commands.watch._open_watch_event_stream",
                new=_fake_watch_event_stream_factory(responses=[(True, None)]),
            ):
                with _cwd(workspace_root):
                    exit_code = _run(
                        argv=[
                            "watch",
                            "--report-format",
                            "json",
                            "--report-schema-version",
                            "1",
                            "--report-output",
                            str(report_path),
                        ],
                        stdout=stdout,
                        stderr=stderr,
                    )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("watch cycle 1: watch clean: succeeded=yes", stderr.getvalue())

    def test_watch_quiet_suppresses_lifecycle_summary(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            report_path = workspace_root / "watch-report.json"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with mock.patch(
                "apache_buildish_site_pipeline.commands.watch._open_watch_event_stream",
                new=_fake_watch_event_stream_factory(responses=[(True, None)]),
            ):
                with _cwd(workspace_root):
                    exit_code = _run(
                        argv=[
                            "watch",
                            "--quiet",
                            "--report-format",
                            "json",
                            "--report-schema-version",
                            "1",
                            "--report-output",
                            str(report_path),
                        ],
                        stdout=stdout,
                        stderr=stderr,
                    )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")

    def test_watch_verbose_writes_sink_and_dirty_count_details_to_stderr(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            report_path = workspace_root / "watch-report.json"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with mock.patch(
                "apache_buildish_site_pipeline.commands.watch._open_watch_event_stream",
                new=_fake_watch_event_stream_factory(responses=[(True, None)]),
            ):
                with _cwd(workspace_root):
                    exit_code = _run(
                        argv=[
                            "watch",
                            "--verbose",
                            "--report-format",
                            "json",
                            "--report-schema-version",
                            "1",
                            "--report-output",
                            str(report_path),
                        ],
                        stdout=stdout,
                        stderr=stderr,
                    )

        self.assertEqual(exit_code, 0)
        self.assertIn("watch report sink:", stderr.getvalue())
        self.assertIn("watch event sink: disabled", stderr.getvalue())
        self.assertIn("watch dirty path count: <initial scan>", stderr.getvalue())
        self.assertIn("watch root count: 1", stderr.getvalue())

    def test_watch_stdout_guard_redirects_plain_prints_when_events_own_stdout(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            report_path = workspace_root / "watch-report.json"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with mock.patch(
                "apache_buildish_site_pipeline.commands.watch._open_watch_event_stream",
                new=_fake_watch_event_stream_factory(responses=[(True, None)]),
            ):
                import apache_buildish_site_pipeline.commands.watch as watch_command

                original_cycle = watch_command._run_watch_cycle  # noqa: SLF001

                def _noisy_run_watch_cycle(*args: object, **kwargs: object):
                    sys.stdout.write("accidental stdout line\n")  # noqa: TID251
                    return original_cycle(*args, **kwargs)

                with mock.patch.object(watch_command, "_run_watch_cycle", side_effect=_noisy_run_watch_cycle):
                    with _cwd(workspace_root):
                        exit_code = _run(
                            argv=[
                                "watch",
                                "--quiet",
                                "--unstable-events",
                                "jsonl",
                                "--report-format",
                                "json",
                                "--report-schema-version",
                                "1",
                                "--report-output",
                                str(report_path),
                            ],
                            stdout=stdout,
                            stderr=stderr,
                        )

        events = _parse_jsonl(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual([event["event"] for event in events], ["cycle-succeeded", "ready"])
        self.assertIn("accidental stdout line", stderr.getvalue())

    def test_watch_debug_writes_cycle_details_to_stderr(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            report_path = workspace_root / "watch-report.json"
            watched_file = workspace_root / "components/runtime/docs/releases/4.0.0/index.md"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with mock.patch(
                "apache_buildish_site_pipeline.commands.watch._open_watch_event_stream",
                new=_fake_watch_event_stream_factory(
                    responses=[
                        (True, (watched_file,)),
                        (False, None),
                    ],
                ),
            ):
                with _cwd(workspace_root):
                    exit_code = _run(
                        argv=[
                            "watch",
                            "--debug",
                            "--report-format",
                            "json",
                            "--report-schema-version",
                            "1",
                            "--report-output",
                            str(report_path),
                        ],
                        stdout=stdout,
                        stderr=stderr,
                    )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("watch cycle 1: watch clean: succeeded=yes", stderr.getvalue())
        self.assertIn("watch dirty path count: <initial scan>", stderr.getvalue())
        self.assertIn("watch debug dirty paths: <initial scan>", stderr.getvalue())
        self.assertIn(str(watched_file), stderr.getvalue())
        self.assertIn("watch debug roots:", stderr.getvalue())

    def test_json_reports_require_schema_version(self) -> None:
        with _workspace() as workspace_root:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(argv=["plan", "--report-format", "json"], stdout=stdout, stderr=stderr)

        self.assertEqual(exit_code, 2)
        self.assertIn("requires --report-schema-version 1", stderr.getvalue())

    def test_watch_initial_failure_without_trusted_stage_exits_three(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            (workspace_root / "site/components.yaml").unlink()
            report_path = workspace_root / "watch-report.json"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(
                    argv=[
                        "watch",
                        "--report-format",
                        "json",
                        "--report-schema-version",
                        "1",
                        "--report-output",
                        str(report_path),
                    ],
                    stdout=stdout,
                    stderr=stderr,
                )
            report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 3)
        self.assertEqual(report["command"], "watch")
        self.assertEqual(report["cycle"], 1)
        self.assertFalse(report["summary"]["stageUsable"])
        self.assertIn("Initial watch cycle failed", stderr.getvalue())

    def test_watch_initial_watch_root_limit_failure_is_reported_clearly(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            report_path = workspace_root / "watch-report.json"
            stdout = io.StringIO()
            stderr = io.StringIO()
            with mock.patch(
                "apache_buildish_site_pipeline.commands.watch.evaluate_planning",
                side_effect=CommandExecutionError("Planning derived more than the 32 watch-root ceiling"),
            ):
                with _cwd(workspace_root):
                    exit_code = _run(
                        argv=[
                            "watch",
                            "--quiet",
                            "--report-format",
                            "json",
                            "--report-schema-version",
                            "1",
                            "--report-output",
                            str(report_path),
                        ],
                        stdout=stdout,
                        stderr=stderr,
                    )
            report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 3)
        self.assertEqual(report["command"], "watch")
        self.assertEqual(report["cycle"], 1)
        self.assertFalse(report["summary"]["stageUsable"])
        self.assertFalse(report["summary"]["wroteStage"])
        self.assertIn("32 watch-root ceiling", report["diagnostics"][-1]["message"])
        self.assertIn("Initial watch cycle failed", stderr.getvalue())

    def test_watch_retains_last_trusted_stage_on_later_cycle_failure(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            report_path = workspace_root / "watch-report.json"
            watched_file = workspace_root / "components/runtime/docs/releases/4.0.0/index.md"
            manifest_path = workspace_root / "site/.stage/manifest.json"
            staged_file = workspace_root / "site/.stage/content/components/spark/contexts/releases/4.0.0/index.md"
            stdout = io.StringIO()
            stderr = io.StringIO()

            def _break_catalog_then_trigger_cycle():
                (workspace_root / "site/components.yaml").unlink()
                return (watched_file,)

            with mock.patch(
                "apache_buildish_site_pipeline.commands.watch._open_watch_event_stream",
                new=_fake_watch_event_stream_factory(
                    responses=[
                        (True, _break_catalog_then_trigger_cycle),
                        (False, None),
                    ],
                ),
            ):
                with _cwd(workspace_root):
                    exit_code = _run(
                        argv=[
                            "watch",
                            "--quiet",
                            "--report-format",
                            "json",
                            "--report-schema-version",
                            "1",
                            "--report-output",
                            str(report_path),
                        ],
                        stdout=stdout,
                        stderr=stderr,
                    )
            report = json.loads(report_path.read_text(encoding="utf-8"))
            manifest_exists = manifest_path.exists()
            staged_file_exists = staged_file.exists()

        self.assertEqual(exit_code, 0)
        self.assertEqual(report["command"], "watch")
        self.assertEqual(report["cycle"], 2)
        self.assertFalse(report["summary"]["succeeded"])
        self.assertFalse(report["summary"]["wroteStage"])
        self.assertTrue(report["summary"]["stageUsable"])
        self.assertTrue(manifest_exists)
        self.assertTrue(staged_file_exists)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")

    def test_watch_retains_last_trusted_stage_on_catalog_dirty_path_failure(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            report_path = workspace_root / "watch-report.json"
            catalog_path = workspace_root / "site/components.yaml"
            manifest_path = workspace_root / "site/.stage/manifest.json"
            staged_file = workspace_root / "site/.stage/content/components/spark/contexts/releases/4.0.0/index.md"
            stdout = io.StringIO()
            stderr = io.StringIO()

            def _break_catalog_then_trigger_catalog_cycle():
                catalog_path.write_text("schemaVersion: 1\ncomponents: [\n", encoding="utf-8")
                return (catalog_path,)

            with mock.patch(
                "apache_buildish_site_pipeline.commands.watch._open_watch_event_stream",
                new=_fake_watch_event_stream_factory(
                    responses=[
                        (True, _break_catalog_then_trigger_catalog_cycle),
                        (False, None),
                    ],
                ),
            ), _cwd(workspace_root):
                    exit_code = _run(
                        argv=[
                            "watch",
                            "--quiet",
                            "--report-format",
                            "json",
                            "--report-schema-version",
                            "1",
                            "--report-output",
                            str(report_path),
                        ],
                        stdout=stdout,
                        stderr=stderr,
                    )
            report = json.loads(report_path.read_text(encoding="utf-8"))
            manifest_exists = manifest_path.exists()
            staged_file_exists = staged_file.exists()

        self.assertEqual(exit_code, 0)
        self.assertEqual(report["command"], "watch")
        self.assertEqual(report["cycle"], 2)
        self.assertFalse(report["summary"]["succeeded"])
        self.assertFalse(report["summary"]["wroteStage"])
        self.assertTrue(report["summary"]["stageUsable"])
        self.assertTrue(manifest_exists)
        self.assertTrue(staged_file_exists)
        self.assertIn("site/components.yaml", report["diagnostics"][-1]["message"])
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")

    def test_watch_retains_last_trusted_stage_when_replacement_would_delete_unknown_path(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            report_path = workspace_root / "watch-report.json"
            watched_file = workspace_root / "components/runtime/docs/releases/4.0.0/index.md"
            manifest_path = workspace_root / "site/.stage/manifest.json"
            unknown_stage_path = workspace_root / "site/.stage/operator-note.txt"
            stdout = io.StringIO()
            stderr = io.StringIO()

            def _inject_unknown_stage_path_then_trigger_cycle():
                unknown_stage_path.write_text("keep me\n", encoding="utf-8")
                return (watched_file,)

            with mock.patch(
                "apache_buildish_site_pipeline.commands.watch._open_watch_event_stream",
                new=_fake_watch_event_stream_factory(
                    responses=[
                        (True, _inject_unknown_stage_path_then_trigger_cycle),
                        (False, None),
                    ],
                ),
            ), _cwd(workspace_root):
                    exit_code = _run(
                        argv=[
                            "watch",
                            "--quiet",
                            "--report-format",
                            "json",
                            "--report-schema-version",
                            "1",
                            "--report-output",
                            str(report_path),
                        ],
                        stdout=stdout,
                        stderr=stderr,
                    )
            report = json.loads(report_path.read_text(encoding="utf-8"))
            manifest_exists = manifest_path.exists()
            unknown_stage_path_exists = unknown_stage_path.exists()

        self.assertEqual(exit_code, 0)
        self.assertEqual(report["command"], "watch")
        self.assertEqual(report["cycle"], 2)
        self.assertFalse(report["summary"]["succeeded"])
        self.assertFalse(report["summary"]["wroteStage"])
        self.assertTrue(report["summary"]["stageUsable"])
        self.assertTrue(manifest_exists)
        self.assertTrue(unknown_stage_path_exists)
        self.assertIn("ambiguous ownership", report["diagnostics"][-1]["message"])
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")

    def test_watch_orderly_shutdown_after_steady_state_exits_zero(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            report_path = workspace_root / "watch-report.json"
            captured_watch_roots: list[tuple[Path, ...]] = []
            stdout = io.StringIO()
            stderr = io.StringIO()

            with mock.patch(
                "apache_buildish_site_pipeline.commands.watch._open_watch_event_stream",
                new=_fake_watch_event_stream_factory(
                    responses=[(True, None)],
                    captured_watch_roots=captured_watch_roots,
                ),
            ), _cwd(workspace_root):
                    exit_code = _run(
                        argv=[
                            "watch",
                            "--quiet",
                            "--report-format",
                            "json",
                            "--report-schema-version",
                            "1",
                            "--report-output",
                            str(report_path),
                        ],
                        stdout=stdout,
                        stderr=stderr,
                    )
            report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(report["cycle"], 1)
        self.assertTrue(report["summary"]["succeeded"])
        self.assertEqual(captured_watch_roots, [(workspace_root.resolve(strict=False),)])
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")

    def test_watch_runs_immediate_follow_up_cycle_for_pending_dirty_set(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            report_path = workspace_root / "watch-report.json"
            watched_file = workspace_root / "components/runtime/docs/releases/4.0.0/index.md"
            watched_directory = watched_file.parent
            stdout = io.StringIO()
            stderr = io.StringIO()

            with mock.patch(
                "apache_buildish_site_pipeline.commands.watch._open_watch_event_stream",
                new=_fake_watch_event_stream_factory(
                    responses=[
                        (True, (watched_file,)),
                        (False, (watched_directory, watched_file)),
                        (False, ()),
                        (True, None),
                    ],
                ),
            ), _cwd(workspace_root):
                    exit_code = _run(
                        argv=[
                            "watch",
                            "--quiet",
                            "--report-format",
                            "json",
                            "--report-schema-version",
                            "1",
                            "--report-output",
                            str(report_path),
                        ],
                        stdout=stdout,
                        stderr=stderr,
                    )
            report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(report["cycle"], 3)
        self.assertTrue(report["summary"]["succeeded"])
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")

    def test_check_build_and_watch_reuse_shared_planning_layers(self) -> None:
        import apache_buildish_site_pipeline.commands.build as build_command
        import apache_buildish_site_pipeline.commands.check as check_command
        import apache_buildish_site_pipeline.commands.watch as watch_command

        with _workspace(with_content_file=True) as workspace_root:
            observed_calls: list[tuple[str, str, str]] = []
            expected_workspace_root = str(workspace_root)
            expected_catalog_path = str(workspace_root / "site/components.yaml")
            expected_stage_root = str(workspace_root / "site/.stage")
            expected_work_root = str(workspace_root / "site/.site-pipeline-work")

            def _record_loader(command_name: str, real_loader):
                def _wrapper(*args, **kwargs):
                    workspace_root = args[0] if args else kwargs["workspace_root"]
                    catalog_path = args[1] if len(args) > 1 else kwargs.get("catalog_path")
                    loaded_inputs = real_loader(*args, **kwargs)
                    observed_calls.append(("load", command_name, f"{workspace_root}:{catalog_path}"))
                    return loaded_inputs

                return _wrapper

            def _record_planning(command_name: str, real_planning):
                def _wrapper(*args, **kwargs):
                    planning = real_planning(*args, **kwargs)
                    workspace_root = kwargs["workspace_root"]
                    stage_root = kwargs["stage_root"]
                    work_root = kwargs["work_root"]
                    target = kwargs["target"]
                    observed_calls.append(
                        (
                            "planning",
                            command_name,
                            ":".join(
                                (
                                    target.value,
                                    str(workspace_root),
                                    str(stage_root),
                                    str(work_root),
                                ),
                            ),
                        ),
                    )
                    return planning

                return _wrapper

            def _record_evaluation(command_name: str, real_evaluation):
                def _wrapper(*args, **kwargs):
                    request = kwargs["request"]
                    observed_calls.append(("evaluation", command_name, request.mode.value))
                    return real_evaluation(*args, **kwargs)

                return _wrapper

            with _cwd(workspace_root):
                with (
                    mock.patch.object(build_command, "load_workspace_inputs", new=_record_loader("build", build_command.load_workspace_inputs)),
                    mock.patch.object(check_command, "load_workspace_inputs", new=_record_loader("check", check_command.load_workspace_inputs)),
                    mock.patch.object(watch_command, "load_workspace_inputs", new=_record_loader("watch", watch_command.load_workspace_inputs)),
                    mock.patch.object(build_command, "evaluate_planning", new=_record_planning("build", build_command.evaluate_planning)),
                    mock.patch.object(check_command, "evaluate_planning", new=_record_planning("check", check_command.evaluate_planning)),
                    mock.patch.object(watch_command, "evaluate_planning", new=_record_planning("watch", watch_command.evaluate_planning)),
                    mock.patch.object(build_command, "run_evaluation", new=_record_evaluation("build", build_command.run_evaluation)),
                    mock.patch.object(check_command, "run_evaluation", new=_record_evaluation("check", check_command.run_evaluation)),
                    mock.patch.object(watch_command, "run_evaluation", new=_record_evaluation("watch", watch_command.run_evaluation)),
                    mock.patch(
                        "apache_buildish_site_pipeline.commands.watch._open_watch_event_stream",
                        new=_fake_watch_event_stream_factory(responses=[(True, None)]),
                    ),
                ):
                    self.assertEqual(_run(argv=["check"], stdout=io.StringIO(), stderr=io.StringIO()), 0)
                    self.assertEqual(_run(argv=["build"], stdout=io.StringIO(), stderr=io.StringIO()), 0)
                    self.assertEqual(_run(argv=["watch", "--quiet"], stdout=io.StringIO(), stderr=io.StringIO()), 0)

        self.assertEqual(
            observed_calls,
            [
                ("load", "check", f"{expected_workspace_root}:{expected_catalog_path}"),
                ("planning", "check", f"build:{expected_workspace_root}:{expected_stage_root}:{expected_work_root}"),
                ("evaluation", "check", "check"),
                ("load", "build", f"{expected_workspace_root}:{expected_catalog_path}"),
                ("planning", "build", f"build:{expected_workspace_root}:{expected_stage_root}:{expected_work_root}"),
                ("evaluation", "build", "build"),
                ("load", "watch", f"{expected_workspace_root}:{expected_catalog_path}"),
                ("planning", "watch", f"watch:{expected_workspace_root}:{expected_stage_root}:{expected_work_root}"),
                ("evaluation", "watch", "watch"),
            ],
        )


def _parse_jsonl(text: str) -> list[dict[str, object]]:
    return [json.loads(line) for line in text.splitlines() if line.strip()]


class CliInternalTests(unittest.TestCase):
    def test_parse_invocation_raises_invocation_error_for_missing_command(self) -> None:
        with self.assertRaises(InvocationError):
            parse_invocation([])

    def test_main_delegates_to_run_with_process_streams(self) -> None:
        stdout = object()
        stderr = object()

        with (
            mock.patch.object(cli_main_module, "sys", mock.Mock(stdout=stdout, stderr=stderr)),
            mock.patch("apache_buildish_site_pipeline.cli.main._run", return_value=7) as run_mock,
        ):
            self.assertEqual(cli_main(["plan"]), 7)

        run_mock.assert_called_once_with(argv=["plan"], stdout=stdout, stderr=stderr)

    def test_run_rejects_event_and_report_output_collisions_after_revalidation(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            cwd = Path(tempdir)
            layout = RepositoryLayout(
                cwd=cwd,
                workspace_root=cwd,
                catalog_path=cwd / "site/components.yaml",
                site_root=cwd / "site",
                stage_root=cwd / "site/.stage",
                work_root=cwd / "site/.site-pipeline-work",
            )
            invocation = WatchInvocation(
                layout=layout,
                fail_on_severity=CheckFailureThreshold.ERROR,
                report_request=ReportRequest(
                    report_format=ReportFormat.TEXT,
                    schema_version=None,
                    output_path=cwd / "reports/watch.txt",
                ),
                unstable_event_request=WatchEventRequest(
                    event_format=WatchEventFormat.JSONL,
                    output_path=cwd / "events/watch.jsonl",
                ),
            )
            shared_output = cwd / "shared/output.txt"
            stdout = io.StringIO()
            stderr = io.StringIO()

            with (
                mock.patch("apache_buildish_site_pipeline.cli.main.parse_invocation", return_value=invocation),
                mock.patch(
                    "apache_buildish_site_pipeline.cli.main.revalidate_report_request",
                    return_value=ReportRequest(
                        report_format=ReportFormat.TEXT,
                        schema_version=None,
                        output_path=shared_output,
                    ),
                ),
                mock.patch(
                    "apache_buildish_site_pipeline.cli.main.revalidate_watch_event_request",
                    return_value=WatchEventRequest(
                        event_format=WatchEventFormat.JSONL,
                        output_path=shared_output,
                    ),
                ),
            ):
                exit_code = _run(argv=["watch"], stdout=stdout, stderr=stderr)

        self.assertEqual(exit_code, 2)
        self.assertIn("must differ from --report-output", stderr.getvalue())

    def test_run_maps_generic_cli_errors_to_internal_failures(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with (
            mock.patch("apache_buildish_site_pipeline.cli.main.parse_invocation", return_value=object()),
            mock.patch(
                "apache_buildish_site_pipeline.cli.main.dispatch_command",
                side_effect=SitePipelineCliError("generic cli failure"),
            ),
        ):
            exit_code = _run(argv=["plan"], stdout=stdout, stderr=stderr)

        self.assertEqual(exit_code, 3)
        self.assertIn("generic cli failure", stderr.getvalue())

    def test_resolve_cli_path_joins_relative_paths_against_cwd(self) -> None:
        cwd = Path.cwd() / "site-pipeline-tests"
        self.assertEqual(
            cli_main_module._resolve_cli_path(cwd=cwd, raw_path="reports/out.json"),  # noqa: SLF001
            cwd / "reports/out.json",
        )

    def test_emit_error_falls_back_to_stderr_when_logging_is_unconfigured(self) -> None:
        class _FlushTrackingStringIO(io.StringIO):
            def __init__(self) -> None:
                super().__init__()
                self.flushed = False

            def flush(self) -> None:
                self.flushed = True
                super().flush()

        stderr = _FlushTrackingStringIO()
        root_logger = logging.getLogger()
        original_handlers = list(root_logger.handlers)
        try:
            root_logger.handlers.clear()
            cli_main_module._emit_error("broken", stderr=stderr)  # noqa: SLF001
        finally:
            root_logger.handlers[:] = original_handlers

        self.assertEqual(stderr.getvalue(), "site-pipeline: broken\n")
        self.assertTrue(stderr.flushed)