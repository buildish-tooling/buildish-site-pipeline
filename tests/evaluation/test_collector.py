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

"""Tests for evaluation diagnostic collection."""

from __future__ import annotations

import unittest

from apache_buildish_site_pipeline.evaluation.collector import DiagnosticCollector
from apache_buildish_site_pipeline.models.enums import DiagnosticSeverity
from apache_buildish_site_pipeline.models.planning_stage_contract import (
    PipelineDiagnosticEntry,
    ReducedDiagnosticDetailsSummary,
)


class DiagnosticCollectorTests(unittest.TestCase):
    def test_orders_diagnostics_and_reduces_large_details(self) -> None:
        collector = DiagnosticCollector()
        collector.add(
            severity=DiagnosticSeverity.WARNING,
            code="warning-two",
            message="second",
            details={"payload": "x" * 9000},
        )
        collector.add(
            severity=DiagnosticSeverity.ERROR,
            code="error-one",
            message="first",
        )

        diagnostics = collector.build()

        self.assertEqual(diagnostics[0].code, "error-one")
        self.assertIsInstance(diagnostics[1].details, ReducedDiagnosticDetailsSummary)

    def test_extend_and_counts_include_prebuilt_entries(self) -> None:
        collector = DiagnosticCollector()
        collector.extend(
            (
                PipelineDiagnosticEntry(
                    severity=DiagnosticSeverity.INFO,
                    code="info-one",
                    message="from extend",
                ),
            )
        )
        collector.add(
            severity=DiagnosticSeverity.WARNING,
            code="warning-one",
            message="from add",
        )

        counts = collector.counts()

        self.assertEqual(counts.error_count, 0)
        self.assertEqual(counts.warning_count, 1)
        self.assertEqual(counts.info_count, 1)

    def test_add_rejects_non_object_details(self) -> None:
        collector = DiagnosticCollector()

        with self.assertRaises(TypeError):
            collector.add(
                severity=DiagnosticSeverity.ERROR,
                code="bad-details",
                message="broken",
                details=["not", "an", "object"],
            )

    def test_add_preserves_small_object_details(self) -> None:
        collector = DiagnosticCollector()
        details = {"component": "spark"}

        collector.add(
            severity=DiagnosticSeverity.INFO,
            code="small-details",
            message="kept",
            details=details,
        )

        self.assertEqual(collector.build()[0].details, details)