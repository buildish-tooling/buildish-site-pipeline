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

"""Tests for CLI report-path handling."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from apache_buildish_site_pipeline.cli.reporting import build_report_request
from apache_buildish_site_pipeline.cli.contract import ReportFormat


class CliReportingTests(unittest.TestCase):
    """Verify the CLI path boundary for local report-output paths."""

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