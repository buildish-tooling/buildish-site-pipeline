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

"""Coordinator/worker boundary tests for staging execution."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from apache_buildish_site_pipeline.commands.stage_report import build_stage_run_report
from apache_buildish_site_pipeline.models.enums import DiagnosticSeverity, StageCommand
from apache_buildish_site_pipeline.models.planning_stage_contract import PipelineDiagnosticEntry
from apache_buildish_site_pipeline.staging.aggregates import _build_content_index_entries, _write_aggregate_files
from apache_buildish_site_pipeline.staging.coordinator import cleanup_after_publication, run_build
from apache_buildish_site_pipeline.staging.ownership import OwnedUnit, OwnedUnitKind, build_owned_units
from apache_buildish_site_pipeline.staging.public_safety import REDACTED_LOCAL_PATH
from apache_buildish_site_pipeline.staging.worker_entrypoint import execute_worker_spec
from apache_buildish_site_pipeline.staging.worker_protocol import StagedPageContributionWire, WorkerSpecWire
from apache_buildish_site_pipeline.staging.workdirs import RunWorkspace
from tests.support.staging import _build_request, _expand_workspace_for_multiple_owned_units, _stage_snapshot, _work_layout
from tests.support.workspace import _workspace


class StagingWorkerTests(unittest.TestCase):
    def test_run_workspace_derives_private_unit_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            layout = _work_layout(workspace_root)
            run_workspace = RunWorkspace(workspace_root=workspace_root, layout=layout)

            unit_workspace = run_workspace.workspace_for_unit(
                OwnedUnit(
                    unit_id="component:spark",
                    owner_id="component:spark",
                    kind=OwnedUnitKind.COMPONENT,
                    content_stage_roots=(Path("content/components/spark"),),
                    static_stage_roots=(Path("static/components/spark"),),
                ),
            )

            self.assertEqual(unit_workspace.fragment_path, layout.fragments_root / "component_spark.json")
            self.assertEqual(unit_workspace.unit_root, layout.units_root / "component_spark")
            self.assertTrue(unit_workspace.unit_root.is_dir())
            self.assertEqual(unit_workspace.content_roots, (layout.next_stage_root / "content/components/spark",))
            self.assertEqual(unit_workspace.static_roots, (layout.next_stage_root / "static/components/spark",))

    def test_worker_entrypoint_reports_unknown_unit_kind_as_failure_wire(self) -> None:
        result = execute_worker_spec(
            WorkerSpecWire(
                unit_id="broken",
                unit_kind="not-a-unit",
                owner_id="broken",
                workspace_root="/workspace",
                unit_root="/workspace/.work/units/broken",
                fragment_path="/workspace/.work/fragments/broken.json",
            ),
        )

        self.assertFalse(result.succeeded)
        self.assertIsNotNone(result.failure)
        self.assertEqual(result.failure.category, "unknownUnitKind")

    def test_build_outputs_are_equivalent_for_pool_sizes_one_and_two(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            _expand_workspace_for_multiple_owned_units(workspace_root)
            request_one = _build_request(workspace_root, pool_size=1)
            request_two = _build_request(workspace_root, pool_size=2)

            outcome_one = run_build(request_one)
            outcome_two = run_build(request_two)
            try:
                snapshot_one = _stage_snapshot(outcome_one.layout.next_stage_root)
                snapshot_two = _stage_snapshot(outcome_two.layout.next_stage_root)
            finally:
                cleanup_after_publication(outcome_one)
                cleanup_after_publication(outcome_two)
                shutil.rmtree(outcome_one.layout.next_stage_root, ignore_errors=True)
                shutil.rmtree(outcome_two.layout.next_stage_root, ignore_errors=True)

        self.assertEqual(outcome_one.worker_count, 1)
        self.assertEqual(outcome_two.worker_count, 2)
        self.assertEqual(snapshot_one, snapshot_two)

    def test_stage_run_report_sanitizes_machine_local_diagnostic_details(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            report = build_stage_run_report(
                command=StageCommand.BUILD,
                evaluation=None,
                diagnostics=(
                    PipelineDiagnosticEntry(
                        severity=DiagnosticSeverity.WARNING,
                        code="demo.warning",
                        message="demo",
                        details={
                            "expectedLocalPath": str(workspace_root / "components/runtime/docs"),
                            "fragmentPath": str(workspace_root / ".work/fragments/component.json"),
                            "path": "/spark/public",
                        },
                    ),
                ),
                succeeded=False,
                wrote_stage=False,
                stage_usable=False,
                stage_root_path=None,
                manifest_path=None,
                workspace_root=workspace_root,
                private_roots=(workspace_root / ".work", workspace_root / "site/.stage"),
            )

        self.assertEqual(report.diagnostics[0].details["expectedLocalPath"], "components/runtime/docs")
        self.assertEqual(report.diagnostics[0].details["fragmentPath"], REDACTED_LOCAL_PATH)
        self.assertEqual(report.diagnostics[0].details["path"], "/spark/public")

    def test_aggregate_diagnostics_redact_private_machine_local_paths(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            request = _build_request(workspace_root, pool_size=1)
            layout = _work_layout(workspace_root)
            _write_aggregate_files(
                layout=layout,
                build_plan=request.build_plan,
                diagnostics=(
                    PipelineDiagnosticEntry(
                        severity=DiagnosticSeverity.WARNING,
                        code="demo.warning",
                        message="demo",
                        details={
                            "expectedLocalPath": str(workspace_root / "components/runtime/docs"),
                            "fragmentPath": str(layout.fragments_root / "component.json"),
                        },
                    ),
                ),
                provider_snapshot=request.provider_snapshot,
                page_contributions=(),
                unit_contribution_manifests=(),
                owned_units=build_owned_units(request.build_plan),
            )
            diagnostics_payload = json.loads((layout.data_root / "diagnostics.json").read_text(encoding="utf-8"))

        self.assertEqual(diagnostics_payload[0]["details"]["expectedLocalPath"], "components/runtime/docs")
        self.assertEqual(diagnostics_payload[0]["details"]["fragmentPath"], REDACTED_LOCAL_PATH)

    def test_content_index_omits_outside_workspace_source_paths(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            request = _build_request(workspace_root, pool_size=1)
            entries = _build_content_index_entries(
                request.build_plan,
                (
                    StagedPageContributionWire(
                        stage_relative_path="content/components/spark/contexts/releases/4.0.0/index.md",
                        component_slug="spark",
                        artifact_key="runtime",
                        section="release",
                        page_kind="release-page",
                        public_path="/spark/development/docs/releases/4.0.0",
                        public_url="https://docs.example.org/spark/development/docs/releases/4.0.0",
                        component_path="/spark/",
                        component_url="https://docs.example.org/spark/",
                        origin_key="docs",
                        source_path=str(Path(tempfile.gettempdir()) / "outside-source.md"),
                        canonical_url="https://docs.example.org/spark/development/docs/releases/4.0.0",
                        version_kind="released",
                        version="4.0.0",
                    ),
                ),
            )

        self.assertIsNone(entries[0].source_path)