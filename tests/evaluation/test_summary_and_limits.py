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

"""Direct coverage for evaluation summary and limit helpers."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import patch

from buildish_site_pipeline.evaluation.collector import DiagnosticCollector
from buildish_site_pipeline.evaluation.limits import _count_watch_entries, validate_limits
from buildish_site_pipeline.evaluation.summary import build_check_summary, build_run_status
from buildish_site_pipeline.evaluation.types import (
    BlockingCondition,
    DiagnosticCounts,
    PageInventory,
    RouteInventory,
    StageGateDecision,
    StageReadinessResult,
)
from buildish_site_pipeline.models.emitted.planning_stage_contract import (
    PipelineDiagnosticEntry,
)
from buildish_site_pipeline.models.enums import (
    CheckFailureThreshold,
    DiagnosticSeverity,
    RunStatus,
)


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

    def test_stage_readiness_result_normalizes_stage_gate_contract(self) -> None:
        build_plan = cast(Any, object())

        ready = StageReadinessResult.from_diagnostics(
            diagnostics=(),
            build_plan_candidate=build_plan,
        )
        blocked = StageReadinessResult.from_diagnostics(
            diagnostics=(
                PipelineDiagnosticEntry(
                    severity=DiagnosticSeverity.ERROR,
                    code="route-bad",
                    message="bad route",
                ),
            ),
            build_plan_candidate=build_plan,
        )
        unavailable = StageReadinessResult.from_diagnostics(
            diagnostics=(),
            build_plan_candidate=None,
        )

        self.assertTrue(ready.gate.allowed)
        self.assertIs(ready.build_plan, build_plan)
        self.assertFalse(blocked.gate.allowed)
        self.assertEqual(blocked.gate.blocking_conditions[0].code, "route-bad")
        self.assertIsNone(blocked.build_plan)
        self.assertFalse(unavailable.gate.allowed)
        self.assertEqual(unavailable.gate.blocking_conditions, ())

    def test_stage_readiness_result_rejects_contradictory_states(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "allowance must agree with build-plan availability",
        ):
            StageReadinessResult(
                gate=StageGateDecision(allowed=True, blocking_conditions=()),
                build_plan=None,
            )

        with self.assertRaisesRegex(
            ValueError,
            "may not carry blocking conditions",
        ):
            StageReadinessResult(
                gate=StageGateDecision(
                    allowed=True,
                    blocking_conditions=(
                        BlockingCondition(code="bad", message="bad"),
                    ),
                ),
                build_plan=cast(Any, object()),
            )

    def test_validate_limits_emits_diagnostics_for_each_exceeded_metric(self) -> None:
        collector = DiagnosticCollector()
        planning = SimpleNamespace(
            selected_versions=SimpleNamespace(contexts=(object(), object())),
            provider_index=SimpleNamespace(snapshot_bytes=2),
            watch_plan=None,
        )

        with (
            patch("buildish_site_pipeline.evaluation.limits._ROUTE_INVENTORY_LIMIT", 0),
            patch("buildish_site_pipeline.evaluation.limits._REDIRECT_INVENTORY_LIMIT", 0),
            patch("buildish_site_pipeline.evaluation.limits._CONTENT_INDEX_LIMIT", 0),
            patch("buildish_site_pipeline.evaluation.limits._SELECTED_VERSION_CONTEXT_LIMIT", 0),
            patch(
                "buildish_site_pipeline.evaluation.limits.DEFAULT_PROVIDER_SNAPSHOT_BYTES",
                0,
            ),
        ):
            validate_limits(
                planning=planning,
                route_inventory=RouteInventory(route_count=1, redirect_count=1),
                page_inventory=PageInventory(pages=(object(),)),
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

    def test_page_inventory_limit_accepts_exact_limit_and_measures_one_over(self) -> None:
        planning = SimpleNamespace(
            selected_versions=SimpleNamespace(contexts=()),
            provider_index=SimpleNamespace(snapshot_bytes=0),
            watch_plan=None,
        )
        exact_collector = DiagnosticCollector()
        exceeded_collector = DiagnosticCollector()

        with patch(
            "buildish_site_pipeline.evaluation.limits._CONTENT_INDEX_LIMIT",
            1,
        ):
            validate_limits(
                planning=planning,
                route_inventory=RouteInventory(route_count=0, redirect_count=0),
                page_inventory=PageInventory(pages=(object(),)),
                collector=exact_collector,
            )
            validate_limits(
                planning=planning,
                route_inventory=RouteInventory(route_count=0, redirect_count=0),
                page_inventory=PageInventory(pages=(object(), object()), complete=False),
                collector=exceeded_collector,
            )

        self.assertEqual(exact_collector.build(), ())
        diagnostic = exceeded_collector.build()[0]
        self.assertEqual(diagnostic.details["metric"], "contentIndexCount")
        self.assertEqual(diagnostic.details["measured"], 2)
        self.assertEqual(diagnostic.details["allowed"], 1)

    def test_count_watch_entries_stops_after_limit_plus_one(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first_entry = root / "first.md"
            second_entry = root / "second.md"
            first_entry.write_text("first\n", encoding="utf-8")
            second_entry.write_text("second\n", encoding="utf-8")
            original_iterdir = type(root).iterdir
            yielded_entries: list[Path] = []

            def _iterdir(path: Path):
                if path != root:
                    return original_iterdir(path)

                def _adversarial_entries():
                    for entry in (first_entry, second_entry):
                        yielded_entries.append(entry)
                        yield entry
                    raise AssertionError("watch discovery continued after limit plus one")

                return _adversarial_entries()

            planning = SimpleNamespace(watch_plan=SimpleNamespace(roots=(root,)))
            with patch.object(
                type(root),
                "iterdir",
                autospec=True,
                side_effect=_iterdir,
            ):
                counted = _count_watch_entries(planning, limit=1)

        self.assertEqual(counted, 2)
        self.assertEqual(yielded_entries, [first_entry, second_entry])

    def test_watch_entry_limit_accepts_exact_limit_and_measures_one_over(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first_entry = root / "first.md"
            first_entry.write_text("first\n", encoding="utf-8")
            planning = SimpleNamespace(
                selected_versions=SimpleNamespace(contexts=()),
                provider_index=SimpleNamespace(snapshot_bytes=0),
                watch_plan=SimpleNamespace(roots=(root,)),
            )
            exact_collector = DiagnosticCollector()
            with patch(
                "buildish_site_pipeline.evaluation.limits._WATCH_FILESYSTEM_ENTRY_LIMIT",
                1,
            ):
                validate_limits(
                    planning=planning,
                    route_inventory=RouteInventory(route_count=0, redirect_count=0),
                    page_inventory=PageInventory(pages=()),
                    collector=exact_collector,
                )

            second_entry = root / "second.md"
            second_entry.write_text("second\n", encoding="utf-8")
            exceeded_collector = DiagnosticCollector()
            with patch(
                "buildish_site_pipeline.evaluation.limits._WATCH_FILESYSTEM_ENTRY_LIMIT",
                1,
            ):
                validate_limits(
                    planning=planning,
                    route_inventory=RouteInventory(route_count=0, redirect_count=0),
                    page_inventory=PageInventory(pages=()),
                    collector=exceeded_collector,
                )

        self.assertEqual(exact_collector.build(), ())
        diagnostic = exceeded_collector.build()[0]
        self.assertEqual(diagnostic.details["metric"], "watchFilesystemEntryCount")
        self.assertEqual(diagnostic.details["measured"], 2)
        self.assertEqual(diagnostic.details["allowed"], 1)
