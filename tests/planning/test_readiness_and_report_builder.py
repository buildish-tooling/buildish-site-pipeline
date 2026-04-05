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

"""Direct coverage for planning readiness and report-builder helpers."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from apache_buildish_site_pipeline.models.enums import (
    DiagnosticSeverity,
    MaterializationInputKind,
    MaterializationStatus,
    PlanningTarget,
)
from apache_buildish_site_pipeline.models.planning_stage_contract import PipelineDiagnosticEntry
from apache_buildish_site_pipeline.planning.readiness import classify_input_readiness
from apache_buildish_site_pipeline.planning.report_builder import build_resolved_materialization_report
from apache_buildish_site_pipeline.planning.types import (
    InputReadiness,
    LocalInputIdentity,
    MaterializationStatusReason,
    ResolvedLocalInput,
)


class ReadinessAndReportBuilderTests(unittest.TestCase):
    def test_classify_input_readiness_rejects_paths_outside_declared_root(self) -> None:
        local_input = self._local_input(Path("/workspace/root"), Path("/workspace/elsewhere"))

        readiness = classify_input_readiness((local_input,))[0].readiness

        self.assertEqual(readiness.status, MaterializationStatus.UNRESOLVED)
        self.assertEqual(
            readiness.reason,
            MaterializationStatusReason.PATH_OUTSIDE_DECLARED_ROOT,
        )

    def test_classify_input_readiness_detects_invalid_materialization_marker(self) -> None:
        with TemporaryDirectory() as temp_dir:
            expected_path = Path(temp_dir) / "docs"
            expected_path.mkdir()
            (expected_path / ".site-pipeline-materialization.json").write_text(
                "{not-json}",
                encoding="utf-8",
            )

            readiness = classify_input_readiness(
                (self._local_input(Path(temp_dir), expected_path),)
            )[0].readiness

        self.assertEqual(readiness.status, MaterializationStatus.UNRESOLVED)
        self.assertEqual(readiness.reason, MaterializationStatusReason.INVALID_MARKER)

    def test_classify_input_readiness_detects_stale_identity_marker(self) -> None:
        with TemporaryDirectory() as temp_dir:
            expected_path = Path(temp_dir) / "docs"
            expected_path.mkdir()
            (expected_path / ".site-pipeline-materialization.json").write_text(
                json.dumps({"version": "4.0.1"}),
                encoding="utf-8",
            )
            local_input = self._local_input(Path(temp_dir), expected_path, version="4.0.0")

            readiness = classify_input_readiness((local_input,))[0].readiness

        self.assertEqual(readiness.status, MaterializationStatus.STALE)
        self.assertEqual(
            readiness.reason,
            MaterializationStatusReason.STALE_IDENTITY_MISMATCH,
        )

    def test_build_resolved_materialization_report_merges_watch_diagnostics(self) -> None:
        local_input = self._local_input(
            Path("/workspace"),
            Path("/workspace/docs"),
            readiness=InputReadiness(
                status=MaterializationStatus.MISSING,
                reason=MaterializationStatusReason.PATH_MISSING,
            ),
            watch_eligible=True,
            provenance="component:runtime",
        )
        evaluation = SimpleNamespace(
            target=PlanningTarget.WATCH,
            local_inputs=(local_input,),
            diagnostics=(
                PipelineDiagnosticEntry(
                    severity=DiagnosticSeverity.WARNING,
                    code="planning-warning",
                    message="Planning warning",
                ),
            ),
            watch_plan=SimpleNamespace(
                diagnostics=(
                    PipelineDiagnosticEntry(
                        severity=DiagnosticSeverity.INFO,
                        code="watch-info",
                        message="Watch info",
                    ),
                )
            ),
        )

        report = build_resolved_materialization_report(evaluation)

        self.assertEqual(report.entries[0].reason, "pathMissing")
        self.assertTrue(report.entries[0].watch_eligible)
        self.assertEqual(
            [entry.code for entry in report.diagnostics],
            ["planning-warning", "watch-info"],
        )

    @staticmethod
    def _local_input(
        declared_root: Path,
        expected_path: Path,
        *,
        version: str | None = None,
        readiness: InputReadiness | None = None,
        watch_eligible: bool | None = None,
        provenance: str | None = None,
    ) -> ResolvedLocalInput:
        return ResolvedLocalInput(
            identity=LocalInputIdentity(
                source_key="runtime",
                input_kind=MaterializationInputKind.DEVELOPMENT,
                component_slug="spark",
                artifact_key="docs",
                version=version,
            ),
            declared_root=declared_root,
            expected_local_path=expected_path,
            provenance=provenance,
            readiness=readiness or InputReadiness(status=MaterializationStatus.PRESENT),
            watch_eligible=watch_eligible,
        )