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
from apache_buildish_site_pipeline.evaluation import EvaluationMode, EvaluationRequest, run_evaluation
from apache_buildish_site_pipeline.models.enums import DiagnosticSeverity, PlanningTarget, StageCommand
from apache_buildish_site_pipeline.models.planning_stage_contract import PipelineDiagnosticEntry
from apache_buildish_site_pipeline.planning import evaluate_planning
from apache_buildish_site_pipeline.staging.aggregates import _build_content_index_entries, _write_aggregate_files
from apache_buildish_site_pipeline.staging.coordinator import cleanup_after_publication, run_build
from apache_buildish_site_pipeline.staging.ownership import OwnedUnit, OwnedUnitKind
from apache_buildish_site_pipeline.staging.public_safety import REDACTED_LOCAL_PATH
from apache_buildish_site_pipeline.staging.types import BuildRequest, OperatorPolicy, StageDestination, WorkRootLayout
from apache_buildish_site_pipeline.staging.worker_entrypoint import execute_worker_spec
from apache_buildish_site_pipeline.staging.worker_protocol import StagedPageContributionWire, WorkerSpecWire
from apache_buildish_site_pipeline.staging.workdirs import RunWorkspace
from tests.test_cli import _workspace


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


def _build_request(workspace_root: Path, *, pool_size: int) -> BuildRequest:
    loaded_inputs = _loaded_inputs(workspace_root)
    planning = evaluate_planning(
        target=PlanningTarget.BUILD,
        catalog=loaded_inputs.catalog,
        provider_snapshot=loaded_inputs.provider_snapshot,
        workspace_root=workspace_root,
        component_documents=loaded_inputs.component_documents,
        stage_root=workspace_root / f"site/.stage-{pool_size}",
        work_root=workspace_root / f".buildish/work-{pool_size}",
    )
    evaluation = run_evaluation(
        request=EvaluationRequest(mode=EvaluationMode.BUILD),
        planning=planning,
    )
    if evaluation.build_plan is None:
        raise AssertionError("expected a build plan for the staging worker test fixture")
    return BuildRequest(
        command=StageCommand.BUILD,
        build_plan=evaluation.build_plan,
        diagnostics=evaluation.diagnostics,
        provider_snapshot=loaded_inputs.provider_snapshot,
        destination=StageDestination(stage_root=workspace_root / f"candidate-stage-{pool_size}"),
        operator_policy=OperatorPolicy(pool_size=pool_size),
    )


def _expand_workspace_for_multiple_owned_units(workspace_root: Path) -> None:
    components_path = workspace_root / "site/components.yaml"
    authored = components_path.read_text(encoding="utf-8")
    components_path.write_text(
        authored.replace(
            "site: {}",
            "site:\n  pagesRoot: site/root-pages\n  assetsRoot: site/root-assets\n  vendorAssets:\n    - source: vendor/brand\n      mountPath: /assets/vendor/brand/",
        ),
        encoding="utf-8",
    )
    (workspace_root / "site/root-pages").mkdir(parents=True, exist_ok=True)
    (workspace_root / "site/root-pages/index.md").write_text("site page\n", encoding="utf-8")
    (workspace_root / "site/root-assets").mkdir(parents=True, exist_ok=True)
    (workspace_root / "site/root-assets/site.css").write_text("body {}\n", encoding="utf-8")
    (workspace_root / "vendor/brand").mkdir(parents=True, exist_ok=True)
    (workspace_root / "vendor/brand/logo.svg").write_text("<svg/>", encoding="utf-8")


def _loaded_inputs(workspace_root: Path):
    from apache_buildish_site_pipeline.commands.shared import load_workspace_inputs

    return load_workspace_inputs(workspace_root)


def _stage_snapshot(stage_root: Path) -> dict[str, object]:
    snapshot: dict[str, object] = {}
    for file_path in sorted(path for path in stage_root.rglob("*") if path.is_file()):
        relative_path = file_path.relative_to(stage_root).as_posix()
        if file_path.suffix == ".json":
            snapshot[relative_path] = _normalized_json(json.loads(file_path.read_text(encoding="utf-8")))
        else:
            snapshot[relative_path] = file_path.read_bytes()
    return snapshot


def _normalized_json(value: object) -> object:
    if isinstance(value, dict):
        return {key: _normalized_json(item) for key, item in value.items() if key != "generatedAt"}
    if isinstance(value, list):
        return [_normalized_json(item) for item in value]
    return value


def _work_layout(workspace_root: Path) -> WorkRootLayout:
    work_root = workspace_root / "work"
    next_stage_root = workspace_root / "next-stage"
    content_root = next_stage_root / "content"
    static_root = next_stage_root / "static"
    data_root = next_stage_root / "data"
    fragments_root = work_root / "fragments"
    units_root = work_root / "units"
    for path in (work_root, next_stage_root, content_root, static_root, data_root, fragments_root, units_root):
        path.mkdir(parents=True, exist_ok=True)
    return WorkRootLayout(
        work_root=work_root,
        next_stage_root=next_stage_root,
        content_root=content_root,
        static_root=static_root,
        data_root=data_root,
        fragments_root=fragments_root,
        units_root=units_root,
    )