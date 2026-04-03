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

"""Tests for planning/evaluation/staged-contract schema models."""

from __future__ import annotations

import math
import unittest
from datetime import UTC, datetime

from pydantic import ValidationError

from apache_buildish_site_pipeline.models.enums import (
    CheckFailureThreshold,
    DiagnosticSeverity,
    DocumentFormat,
    MaterializationInputKind,
    MaterializationStatus,
    PlanningTarget,
    RunStatus,
    StageCommand,
)
from apache_buildish_site_pipeline.models.loading import (
    load_check_report,
    load_resolved_materialization_report,
    load_stage_manifest,
    load_stage_run_report,
)
from apache_buildish_site_pipeline.models.planning_stage_contract import (
    CheckReportV1,
    CheckSummary,
    PipelineDiagnosticEntry,
    ReducedDiagnosticDetailsSummary,
    ResolvedMaterializationEntry,
    ResolvedMaterializationReportV1,
    StageDataFiles,
    StageManifestV1,
    StageRoots,
    StageRunReportV1,
    StageRunSummary,
)


class PlanningStageContractTests(unittest.TestCase):
    """Validate the first planning/staging contract model family."""

    def test_resolved_materialization_report_requires_watch_eligible_in_watch_mode(self) -> None:
        entry = ResolvedMaterializationEntry(
            input_kind=MaterializationInputKind.SITE_PAGES,
            expected_local_path="/workspace/site/pages",
            status=MaterializationStatus.PRESENT,
        )

        with self.assertRaises(ValidationError):
            ResolvedMaterializationReportV1(
                schema_version=1,
                generated_at=datetime.now(tz=UTC),
                target=PlanningTarget.WATCH,
                entries=[entry],
            )

        report = ResolvedMaterializationReportV1(
            schema_version=1,
            generated_at=datetime.now(tz=UTC),
            target=PlanningTarget.BUILD,
            entries=[entry],
        )
        self.assertEqual(report.target, PlanningTarget.BUILD)

    def test_check_summary_enforces_normative_status_and_threshold_rules(self) -> None:
        summary = CheckSummary(
            status=RunStatus.WARNINGS,
            passed=False,
            fail_on_severity=CheckFailureThreshold.WARNING,
            error_count=0,
            warning_count=2,
            info_count=1,
        )
        self.assertFalse(summary.passed)

        with self.assertRaises(ValidationError):
            CheckSummary(
                status=RunStatus.CLEAN,
                passed=True,
                fail_on_severity=CheckFailureThreshold.ERROR,
                error_count=0,
                warning_count=1,
                info_count=0,
            )

        with self.assertRaises(ValidationError):
            CheckSummary(
                status=RunStatus.WARNINGS,
                passed=True,
                fail_on_severity=CheckFailureThreshold.WARNING,
                error_count=0,
                warning_count=2,
                info_count=0,
            )

    def test_pipeline_diagnostic_details_accept_reduced_summary_and_reject_non_json_values(self) -> None:
        diagnostic = PipelineDiagnosticEntry(
            severity=DiagnosticSeverity.ERROR,
            code="PIPELINE-001",
            message="Something failed",
            details=ReducedDiagnosticDetailsSummary(
                omitted=True,
                reason="sizeLimitExceeded",
                actual_bytes=4096,
                limit_bytes=1024,
                summary="details omitted",
            ),
        )
        self.assertTrue(diagnostic.details.omitted)

        with self.assertRaises(ValidationError):
            PipelineDiagnosticEntry(
                severity=DiagnosticSeverity.WARNING,
                code="PIPELINE-002",
                message="Bad details",
                details={"value": object()},
            )

        with self.assertRaises(ValidationError):
            PipelineDiagnosticEntry(
                severity=DiagnosticSeverity.WARNING,
                code="PIPELINE-003",
                message="Bad details",
                details={"value": math.nan},
            )

    def test_stage_run_report_enforces_cycle_manifest_and_stage_usability_rules(self) -> None:
        summary = StageRunSummary(
            status=RunStatus.ERRORS,
            succeeded=False,
            wrote_stage=False,
            stage_usable=True,
            error_count=1,
            warning_count=0,
            info_count=0,
        )
        report = StageRunReportV1(
            schema_version=1,
            generated_at=datetime.now(tz=UTC),
            command=StageCommand.WATCH,
            summary=summary,
            stage_root_path="/workspace/out/stage",
            manifest_path="/workspace/out/stage/manifest.json",
            cycle=3,
            diagnostics=[],
        )
        self.assertEqual(report.cycle, 3)

        with self.assertRaises(ValidationError):
            StageRunReportV1(
                schema_version=1,
                generated_at=datetime.now(tz=UTC),
                command=StageCommand.BUILD,
                summary=summary,
                cycle=1,
                diagnostics=[],
            )

        with self.assertRaises(ValidationError):
            StageRunReportV1(
                schema_version=1,
                generated_at=datetime.now(tz=UTC),
                command=StageCommand.WATCH,
                summary=StageRunSummary(
                    status=RunStatus.CLEAN,
                    succeeded=True,
                    wrote_stage=True,
                    stage_usable=True,
                    error_count=0,
                    warning_count=0,
                    info_count=0,
                ),
                stage_root_path="/workspace/out/stage",
                diagnostics=[],
                cycle=4,
            )

    def test_stage_manifest_validates_paths_and_serializes_literal_formats(self) -> None:
        manifest = StageManifestV1(
            schema_version=1,
            stage_layout_version=1,
            generated_at=datetime.now(tz=UTC),
            command=StageCommand.BUILD,
            front_matter_format="yaml",
            aggregate_format="json",
            roots=StageRoots(content="content", static="static", data="data"),
            data_files=StageDataFiles(
                components="data/components.json",
                artifacts="data/artifacts.json",
                routes="data/routes.json",
                redirects="data/redirects.json",
            ),
        )
        serialized = manifest.model_dump()
        self.assertEqual(serialized["frontMatterFormat"], "yaml")
        self.assertEqual(serialized["dataFiles"]["components"], "data/components.json")

        with self.assertRaises(ValidationError):
            StageRoots(content="content", static="content", data="data")

        with self.assertRaises(ValidationError):
            StageManifestV1(
                schema_version=1,
                stage_layout_version=1,
                generated_at=datetime.now(tz=UTC),
                command=StageCommand.BUILD,
                front_matter_format="yaml",
                aggregate_format="json",
                roots=StageRoots(content="content", static="static", data="data"),
                data_files=StageDataFiles(
                    components="components.json",
                    artifacts="data/artifacts.json",
                    routes="data/routes.json",
                    redirects="data/redirects.json",
                ),
            )

    def test_specialized_loaders_dispatch_to_the_correct_report_models(self) -> None:
        check_report = load_check_report(
            '{"schemaVersion":1,"generatedAt":"2026-04-03T18:00:00Z","command":"check","summary":{"status":"clean","passed":true,"failOnSeverity":"error","errorCount":0,"warningCount":0,"infoCount":1},"diagnostics":[]}',
            document_format=DocumentFormat.JSON,
            source_name="check.json",
        )
        self.assertIsInstance(check_report, CheckReportV1)

        planning_report = load_resolved_materialization_report(
            "schemaVersion: 1\ngeneratedAt: 2026-04-03T18:00:00Z\ntarget: watch\nentries:\n  - inputKind: sitePages\n    expectedLocalPath: /workspace/site/pages\n    status: present\n    watchEligible: true\n",
            document_format=DocumentFormat.YAML,
            source_name="plan.yaml",
        )
        self.assertIsInstance(planning_report, ResolvedMaterializationReportV1)

        stage_report = load_stage_run_report(
            '{"schemaVersion":1,"generatedAt":"2026-04-03T18:00:00Z","command":"watch","summary":{"status":"errors","succeeded":false,"wroteStage":false,"stageUsable":true,"errorCount":1,"warningCount":0,"infoCount":0},"stageRootPath":"/workspace/out/stage","manifestPath":"/workspace/out/stage/manifest.json","cycle":2,"diagnostics":[]}',
            document_format=DocumentFormat.JSON,
            source_name="stage-run.json",
        )
        self.assertIsInstance(stage_report, StageRunReportV1)

        stage_manifest = load_stage_manifest(
            '{"schemaVersion":1,"stageLayoutVersion":1,"generatedAt":"2026-04-03T18:00:00Z","command":"build","frontMatterFormat":"yaml","aggregateFormat":"json","roots":{"content":"content","static":"static","data":"data"},"dataFiles":{"components":"data/components.json","artifacts":"data/artifacts.json","routes":"data/routes.json","redirects":"data/redirects.json"}}',
            document_format=DocumentFormat.JSON,
            source_name="manifest.json",
        )
        self.assertIsInstance(stage_manifest, StageManifestV1)