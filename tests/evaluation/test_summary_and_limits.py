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

"""Direct coverage for evaluation summary and limit helpers."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from apache_buildish_site_pipeline.evaluation.collector import DiagnosticCollector
from apache_buildish_site_pipeline.evaluation.limits import _count_watch_entries, validate_limits
from apache_buildish_site_pipeline.evaluation.summary import build_check_summary, build_run_status
from apache_buildish_site_pipeline.evaluation.types import DiagnosticCounts, PageScanResult, RouteInventory
from apache_buildish_site_pipeline.models.enums import CheckFailureThreshold, RunStatus


class SummaryAndLimitsTests(unittest.TestCase):
    def test_build_run_status_prefers_errors_before_warnings(self) -> None:
        self.assertEqual(
            build_run_status(DiagnosticCounts(error_count=1, warning_count=99, info_count=0)),
            RunStatus.ERRORS,
        )
        self.assertEqual(
            build_run_status(DiagnosticCounts(error_count=0, warning_count=1, info_count=0)),
            RunStatus.WARNINGS,
        )
        self.assertEqual(
            build_run_status(DiagnosticCounts(error_count=0, warning_count=0, info_count=5)),
            RunStatus.CLEAN,
        )

    def test_build_check_summary_honors_warning_failure_threshold(self) -> None:
        summary = build_check_summary(
            counts=DiagnosticCounts(error_count=0, warning_count=1, info_count=2),
            fail_on_severity=CheckFailureThreshold.WARNING,
        )

        self.assertFalse(summary.passed)
        self.assertEqual(summary.status, RunStatus.WARNINGS)

    def test_validate_limits_emits_diagnostics_for_each_exceeded_metric(self) -> None:
        collector = DiagnosticCollector()
        planning = SimpleNamespace(
            selected_versions=SimpleNamespace(contexts=(object(), object())),
            provider_index=SimpleNamespace(snapshot_bytes=2),
            watch_plan=None,
        )

        with (
            patch("apache_buildish_site_pipeline.evaluation.limits._ROUTE_INVENTORY_LIMIT", 0),
            patch("apache_buildish_site_pipeline.evaluation.limits._REDIRECT_INVENTORY_LIMIT", 0),
            patch("apache_buildish_site_pipeline.evaluation.limits._CONTENT_INDEX_LIMIT", 0),
            patch("apache_buildish_site_pipeline.evaluation.limits._SELECTED_VERSION_CONTEXT_LIMIT", 0),
            patch("apache_buildish_site_pipeline.evaluation.limits._PROVIDER_SNAPSHOT_BYTES_LIMIT", 0),
        ):
            validate_limits(
                planning=planning,
                route_inventory=RouteInventory(route_count=1, redirect_count=1),
                page_scan=PageScanResult(pages=(object(),)),
                collector=collector,
            )

        metrics = {entry.details["metric"] for entry in collector.build()}
        self.assertEqual(
            metrics,
            {
                "routeInventoryCount",
                "redirectInventoryCount",
                "contentIndexCount",
                "selectedVersionContextCount",
                "providerSnapshotBytes",
            },
        )

    def test_count_watch_entries_deduplicates_overlapping_roots(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "pages/nested").mkdir(parents=True)
            (root / "pages/index.md").write_text("# docs\n", encoding="utf-8")
            (root / "pages/nested/guide.md").write_text("# guide\n", encoding="utf-8")
            planning = SimpleNamespace(
                watch_plan=SimpleNamespace(roots=(root / "pages", root / "pages/nested")),
            )

            counted = _count_watch_entries(planning)

        self.assertEqual(counted, 3)
