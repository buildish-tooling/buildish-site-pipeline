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
from apache_buildish_site_pipeline.models.planning_stage_contract import ReducedDiagnosticDetailsSummary


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