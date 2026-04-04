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
import json
import os
import tempfile
import unittest
from unittest import mock
from contextlib import contextmanager
from pathlib import Path

from apache_buildish_site_pipeline.cli import _run
from apache_buildish_site_pipeline.cli_dispatch import dispatch_command as _dispatch_command
from apache_buildish_site_pipeline.cli_errors import CommandExecutionError


class CliTests(unittest.TestCase):
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

            with mock.patch("apache_buildish_site_pipeline.cli.dispatch_command", side_effect=_dispatch_and_mutate):
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
            report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(report["cycle"], 3)
        self.assertTrue(report["summary"]["succeeded"])
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")


@contextmanager
def _workspace(*, with_content_file: bool = False):
    with tempfile.TemporaryDirectory() as tempdir:
        workspace_root = Path(tempdir)
        _write_workspace_inputs(workspace_root, with_content_file=with_content_file)
        yield workspace_root


def _write_workspace_inputs(workspace_root: Path, *, with_content_file: bool) -> None:
    (workspace_root / "site").mkdir(parents=True, exist_ok=True)
    (workspace_root / "site/components.yaml").write_text(
        """
schemaVersion: 1
defaults:
  docsRoot: docs
  publication:
    origin: docs
site: {}
origins:
  docs:
    baseUrl: https://docs.example.org
sources:
  runtime:
    localDir: components/runtime
components:
  - slug: spark
    content:
      source: runtime
    publication:
      mountPath: /spark/
    artifacts:
      - key: runtime
        source: runtime
        versioning:
          developmentRef: main
          tagPattern: ^v.*$
        publicationSelection:
          development: true
          lineHeads:
            mode: allAuthored
          releases:
            mode: latestPerLine
        lifecycle:
          releaseLines:
            - key: '4.0'
              maintenanceRef: maintenance/4.0
              latest: '4.0.0'
          releases:
            - version: '4.0.0'
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (workspace_root / "site/provider-snapshot.json").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "providers": [
                    {"key": "github", "type": "githubReleases", "fetchedAt": "2026-04-03T00:00:00Z"},
                ],
                "records": [
                    {
                        "provider": "github",
                        "kind": "development",
                        "componentSlug": "spark",
                        "artifactKey": "runtime",
                        "ref": "main",
                    },
                    {
                        "provider": "github",
                        "kind": "lineHead",
                        "componentSlug": "spark",
                        "artifactKey": "runtime",
                        "releaseLine": "4.0",
                        "ref": "maintenance/4.0",
                    },
                    {
                        "provider": "github",
                        "kind": "released",
                        "componentSlug": "spark",
                        "artifactKey": "runtime",
                        "version": "4.0.0",
                        "tag": "v4.0.0",
                    },
                ],
            },
        )
        + "\n",
        encoding="utf-8",
    )
    (workspace_root / "components/runtime/docs/maintenance/4.0").mkdir(parents=True, exist_ok=True)
    (workspace_root / "components/runtime/docs/releases/4.0.0").mkdir(parents=True, exist_ok=True)
    if with_content_file:
        (workspace_root / "components/runtime/docs/releases/4.0.0/index.md").write_text("hello\n", encoding="utf-8")


@contextmanager
def _cwd(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


class _FakeWatchEventStream:
    def __init__(self, responses: list[tuple[bool, object]]) -> None:
        self._responses = list(responses)

    def collect_dirty_paths(self, *, wait_for_first: bool):
        if not self._responses:
            raise AssertionError("watch test exhausted fake event-stream responses")
        expected_wait_for_first, response = self._responses.pop(0)
        if expected_wait_for_first is not wait_for_first:
            raise AssertionError(f"expected wait_for_first={expected_wait_for_first}, got {wait_for_first}")
        return response() if callable(response) else response

    def close(self) -> None:
        return None


def _fake_watch_event_stream_factory(*, responses: list[tuple[bool, object]], captured_watch_roots: list[tuple[Path, ...]] | None = None):
    @contextmanager
    def _factory(*, watch_roots: tuple[Path, ...], stage_root: Path, work_root: Path, report_output: Path | None, stop_event):
        del stage_root, work_root, report_output, stop_event
        if captured_watch_roots is not None:
            captured_watch_roots.append(watch_roots)
        yield _FakeWatchEventStream(list(responses))

    return _factory