# Copyright 2026 The Apache Software Foundation

"""End-to-end-ish CLI tests over the real command surface."""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from apache_buildish_site_pipeline.cli import _run


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
            staged_file = (
                workspace_root / "site/.stage/content/components/spark/contexts/releases/4.0.0/releases/4.0.0/index.md"
            )

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