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

"""Tests for CLI reporting helpers."""

from __future__ import annotations

import io
import os
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from apache_buildish_site_pipeline.cli.contract import ReportFormat
from apache_buildish_site_pipeline.cli.errors import InvocationError
from apache_buildish_site_pipeline.cli.reporting import (
    build_report_request,
    build_watch_event_request,
    emit_report,
    render_text_report,
    revalidate_report_request,
    revalidate_watch_event_request,
)
from apache_buildish_site_pipeline.models.enums import (
    CheckFailureThreshold,
    PlanningTarget,
    RunStatus,
    StageCommand,
)
from apache_buildish_site_pipeline.models.planning_stage_contract import (
    CheckReportV1,
    CheckSummary,
    ResolvedMaterializationReportV1,
    StageRunReportV1,
    StageRunSummary,
)


class CliReportingTests(unittest.TestCase):
    """Verify CLI reporting request parsing and output behavior."""

    def test_report_output_uses_host_native_path_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            cwd = Path(tempdir)
            (cwd / "reports").mkdir()

            request = build_report_request(
                cwd=cwd,
                report_format="text",
                schema_version=None,
                report_output=r"reports\build-report.txt",
            )

        self.assertEqual(request.report_format, ReportFormat.TEXT)
        if os.name == "nt":
            self.assertEqual(request.output_path, cwd / "reports" / "build-report.txt")
        else:
            self.assertEqual(request.output_path, cwd / r"reports\build-report.txt")

    def test_text_format_rejects_schema_version(self) -> None:
        with self.assertRaises(InvocationError) as raised:
            build_report_request(
                cwd=Path.cwd(),
                report_format="text",
                schema_version=1,
                report_output="-",
            )

        self.assertIn(
            "--report-schema-version is only valid together with --report-format json",
            str(raised.exception),
        )

    def test_json_report_requires_schema_version(self) -> None:
        with self.assertRaises(InvocationError) as raised:
            build_report_request(
                cwd=Path.cwd(),
                report_format="json",
                schema_version=None,
                report_output="-",
            )

        self.assertIn(
            "JSON report output requires --report-schema-version 1",
            str(raised.exception),
        )

    def test_report_output_stdout_for_json_requires_explicit_permission(self) -> None:
        with self.assertRaises(InvocationError) as raised:
            build_report_request(
                cwd=Path.cwd(),
                report_format="json",
                schema_version=1,
                report_output="-",
                forbid_stdout_json=True,
            )

        self.assertIn(
            "watch JSON reports must be written to a file, not stdout",
            str(raised.exception),
        )

    def test_watch_event_output_requires_explicit_event_format(self) -> None:
        with self.assertRaises(InvocationError) as raised:
            build_watch_event_request(
                cwd=Path.cwd(),
                event_format=None,
                event_output="events.json",
            )

        self.assertIn(
            "--unstable-events-output is only valid together with --unstable-events",
            str(raised.exception),
        )

    def test_revalidate_report_request_rejects_output_symlink_created_after_parse(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            cwd = Path(tempdir)
            target = cwd / "report.txt"
            request = build_report_request(
                cwd=cwd,
                report_format="text",
                schema_version=None,
                report_output=target.name,
            )
            (cwd / "actual.txt").write_text("kept", encoding="utf-8")
            target.symlink_to(cwd / "actual.txt")

            with self.assertRaises(InvocationError) as raised:
                revalidate_report_request(cwd=cwd, request=request)

        self.assertIn("must not be a symlink", str(raised.exception))

    def test_revalidate_watch_event_request_rejects_forbidden_output_root(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            cwd = Path(tempdir)
            request = build_watch_event_request(
                cwd=cwd,
                event_format="jsonl",
                event_output="events.json",
            )

            with self.assertRaises(InvocationError) as raised:
                revalidate_watch_event_request(
                    cwd=cwd,
                    request=request,
                    forbidden_roots=(cwd,),
                )

        self.assertIn("must live outside", str(raised.exception))

    def test_emit_report_appends_newline_to_stdout_but_not_to_files(self) -> None:
        payload = self._plan_report()
        text_output = render_text_report(payload)
        stdout = io.StringIO()
        request = build_report_request(
            cwd=Path.cwd(),
            report_format="text",
            schema_version=None,
            report_output="-",
        )

        emit_report(report=payload, request=request, text_output=text_output, stdout=stdout)

        self.assertTrue(stdout.getvalue().endswith("\n"))
        with tempfile.TemporaryDirectory() as tempdir:
            cwd = Path(tempdir)
            request = build_report_request(
                cwd=cwd,
                report_format="text",
                schema_version=None,
                report_output="report.txt",
            )

            emit_report(
                report=payload,
                request=request,
                text_output=text_output,
                stdout=io.StringIO(),
            )

            self.assertFalse(
                (cwd / "report.txt").read_text(encoding="utf-8").endswith("\n")
            )

    def test_render_text_report_formats_plan_check_and_stage_reports(self) -> None:
        self.assertIn("plan build", render_text_report(self._plan_report()))
        self.assertIn("check warnings", render_text_report(self._check_report()))
        self.assertIn("build errors", render_text_report(self._stage_report()))

    @staticmethod
    def _plan_report() -> ResolvedMaterializationReportV1:
        return ResolvedMaterializationReportV1(
            schema_version=1,
            generated_at=datetime(2026, 4, 5, tzinfo=UTC),
            target=PlanningTarget.BUILD,
            entries=[],
            diagnostics=[],
        )

    @staticmethod
    def _check_report() -> CheckReportV1:
        return CheckReportV1(
            schema_version=1,
            generated_at=datetime(2026, 4, 5, tzinfo=UTC),
            command="check",
            summary=CheckSummary(
                status=RunStatus.WARNINGS,
                passed=False,
                fail_on_severity=CheckFailureThreshold.WARNING,
                error_count=0,
                warning_count=1,
                info_count=0,
            ),
            diagnostics=[],
        )

    @staticmethod
    def _stage_report() -> StageRunReportV1:
        return StageRunReportV1(
            schema_version=1,
            generated_at=datetime(2026, 4, 5, tzinfo=UTC),
            command=StageCommand.BUILD,
            summary=StageRunSummary(
                status=RunStatus.ERRORS,
                succeeded=False,
                wrote_stage=False,
                stage_usable=False,
                error_count=1,
                warning_count=0,
                info_count=0,
            ),
            diagnostics=[],
        )