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

from dataclasses import replace
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from apache_buildish_site_pipeline.cli.errors import RetainedStageError, StageIntegrityError
from apache_buildish_site_pipeline.commands.stage_report import build_stage_run_report
from apache_buildish_site_pipeline.models.enums import DiagnosticSeverity, RecordKind, StageCommand
from apache_buildish_site_pipeline.models.emitted.planning_stage_contract import (
    PipelineDiagnosticEntry,
)
from apache_buildish_site_pipeline.staging.aggregates import _build_content_index_entries, _write_aggregate_files
from apache_buildish_site_pipeline.staging.coordinator import (
    _run_worker_subprocess,
    _seed_next_stage_root,
    cleanup_after_publication,
    materialize_stage_tree,
    publish_stage,
    run_build,
)
from apache_buildish_site_pipeline.staging.ownership import OwnedUnit, OwnedUnitKind, build_owned_units
from apache_buildish_site_pipeline.staging.public_safety import REDACTED_LOCAL_PATH, sanitize_public_diagnostics
from apache_buildish_site_pipeline.staging.spec_builder import build_context_wire, build_worker_spec_for_unit
from apache_buildish_site_pipeline.staging import worker_entrypoint
from apache_buildish_site_pipeline.staging.worker_entrypoint import execute_worker_spec
from apache_buildish_site_pipeline.staging.worker_protocol import StagedPageContributionWire, WorkerResultWire, WorkerSpecWire
from apache_buildish_site_pipeline.staging.workdirs import RunWorkspace
from tests.support.staging import _build_request, _expand_workspace_for_multiple_owned_units, _stage_snapshot, _work_layout
from tests.support.workspace import _workspace


class StagingWorkerTests(unittest.TestCase):
    def _component_unit(self, request) -> OwnedUnit:
        return next(
            unit
            for unit in build_owned_units(request.build_plan)
            if unit.kind is OwnedUnitKind.COMPONENT
        )

    def _assert_symlink_escape_failure(self, result) -> None:
        self.assertFalse(result.succeeded)
        self.assertIsNotNone(result.failure)
        self.assertEqual(result.failure.category, "StageIntegrityError")
        self.assertIn("escapes declared root", result.failure.message)

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
                    content_stage_roots=(Path("content/spark"),),
                    static_stage_roots=(Path("static/spark/assets"),),
                ),
            )

            self.assertEqual(unit_workspace.fragment_path, layout.fragments_root / "component_spark.json")
            self.assertEqual(unit_workspace.unit_root, layout.units_root / "component_spark")
            self.assertTrue(unit_workspace.unit_root.is_dir())
            self.assertEqual(unit_workspace.content_roots, (layout.next_stage_root / "content/spark",))
            self.assertEqual(unit_workspace.static_roots, (layout.next_stage_root / "static/spark/assets",))

    def test_worker_spec_uses_resolved_public_paths_for_component_roots(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            catalog_path = workspace_root / "site/catalog.yaml"
            catalog_text = catalog_path.read_text(encoding="utf-8")
            catalog_path.write_text(
                catalog_text.replace(
                    "    publication:\n      mountPath: /spark/\n",
                    "    publication:\n      mountPath: /products/spark/\n",
                    1,
                ),
                encoding="utf-8",
            )
            request = _build_request(workspace_root, pool_size=1)
            layout = _work_layout(workspace_root)
            unit = self._component_unit(request)

            spec = build_worker_spec_for_unit(
                unit=unit,
                workspace_root=request.build_plan.workspace_root,
                site_components=request.build_plan.site.components,
                run_workspace=RunWorkspace(workspace_root=workspace_root, layout=layout),
            )

        self.assertEqual(
            spec.component_pages_stage_root,
            str(layout.next_stage_root / "content/products/spark"),
        )
        self.assertEqual(
            spec.component_assets_stage_root,
            str(layout.next_stage_root / "static/products/spark/assets"),
        )
        self.assertEqual(
            spec.stage_meta.content_roots[0],
            str(layout.next_stage_root / "content/products/spark"),
        )
        self.assertEqual(
            spec.stage_meta.static_roots[0],
            str(layout.next_stage_root / "static/products/spark/assets"),
        )

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

    def test_worker_entrypoint_main_round_trips_one_json_payload(self) -> None:
        spec = WorkerSpecWire(
            unit_id="site-pages",
            unit_kind="site-pages",
            owner_id="site-pages",
            workspace_root="/workspace",
            fragment_path="/workspace/.work/fragments/site-pages.json",
            site_pages_source="/workspace/site/content",
            stage_meta={"content_roots": ("/workspace/site/.stage/content",)},
        )
        result = WorkerResultWire(unit_id="site-pages", succeeded=True, files_written=1)
        stdin = io.StringIO(spec.model_dump_json(by_alias=True))
        stdout = io.StringIO()

        with mock.patch.object(worker_entrypoint.sys, "stdin", stdin), mock.patch.object(
            worker_entrypoint.sys,
            "stdout",
            stdout,
        ), mock.patch.object(
            worker_entrypoint,
            "execute_worker_spec",
            return_value=result,
        ) as execute:
            exit_code = worker_entrypoint.main()

        self.assertEqual(exit_code, 0)
        execute.assert_called_once()
        self.assertEqual(
            json.loads(stdout.getvalue()),
            json.loads(result.model_dump_json(by_alias=True)),
        )

    def test_worker_entrypoint_rejects_site_pages_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            source_root = workspace_root / "site/content"
            source_root.mkdir(parents=True, exist_ok=True)
            outside_path = workspace_root / "outside-page.txt"
            outside_path.write_text("outside", encoding="utf-8")
            (source_root / "escape.txt").symlink_to(outside_path)

            result = execute_worker_spec(
                WorkerSpecWire(
                    unit_id="site-pages",
                    unit_kind="site-pages",
                    owner_id="site-pages",
                    workspace_root=str(workspace_root),
                    fragment_path=str(workspace_root / ".work/fragments/site-pages.json"),
                    site_pages_source=str(source_root),
                    stage_meta={
                        "content_roots": (str(workspace_root / "site/.stage/content"),),
                    },
                ),
            )

        self._assert_symlink_escape_failure(result)

    def test_worker_entrypoint_rejects_site_assets_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            source_root = workspace_root / "site/assets"
            source_root.mkdir(parents=True, exist_ok=True)
            outside_path = workspace_root / "outside-asset.bin"
            outside_path.write_text("outside", encoding="utf-8")
            (source_root / "escape.bin").symlink_to(outside_path)

            result = execute_worker_spec(
                WorkerSpecWire(
                    unit_id="site-assets",
                    unit_kind="site-assets",
                    owner_id="site-assets",
                    workspace_root=str(workspace_root),
                    fragment_path=str(workspace_root / ".work/fragments/site-assets.json"),
                    site_assets_source=str(source_root),
                    stage_meta={
                        "static_roots": (str(workspace_root / "site/.stage/static"),),
                    },
                ),
            )

        self._assert_symlink_escape_failure(result)

    def test_worker_entrypoint_rejects_component_pages_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            source_root = workspace_root / "components/runtime/docs"
            source_root.mkdir(parents=True, exist_ok=True)
            outside_path = workspace_root / "outside-component.txt"
            outside_path.write_text("outside", encoding="utf-8")
            (source_root / "escape.txt").symlink_to(outside_path)

            result = execute_worker_spec(
                WorkerSpecWire(
                    unit_id="component:spark",
                    unit_kind="component",
                    owner_id="component:spark",
                    workspace_root=str(workspace_root),
                    unit_root=str(workspace_root / ".work/units/component_spark"),
                    fragment_path=str(workspace_root / ".work/fragments/component_spark.json"),
                    component_slug="spark",
                    component_pages_source=str(source_root),
                    component_pages_stage_root=str(
                        workspace_root / "site/.stage/content/spark"
                    ),
                    component_publication={
                        "path": "/spark/",
                        "url": "https://docs.example.org/spark/",
                        "component_path": "/spark/",
                        "component_url": "https://docs.example.org/spark/",
                        "origin_key": "docs",
                    },
                    stage_meta={
                        "content_roots": (
                            str(workspace_root / "site/.stage/content/spark"),
                        ),
                    },
                ),
            )

        self._assert_symlink_escape_failure(result)

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

    def test_run_build_seeds_stage_root_and_can_skip_all_owned_units(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            request = _build_request(workspace_root, pool_size=1)
            seed_stage_root = workspace_root / "seed-stage"
            seed_stage_root.mkdir(parents=True, exist_ok=True)
            (seed_stage_root / "keep.txt").write_text("keep\n", encoding="utf-8")
            (seed_stage_root / "remove.txt").write_text("remove\n", encoding="utf-8")
            seeded_request = replace(
                request,
                seed_stage_root=seed_stage_root,
                seed_stage_removals=("remove.txt",),
                included_unit_ids=frozenset(),
            )

            outcome = run_build(seeded_request)
            try:
                self.assertEqual(outcome.built_unit_ids, ())
                self.assertTrue((outcome.layout.next_stage_root / "keep.txt").is_file())
                self.assertFalse((outcome.layout.next_stage_root / "remove.txt").exists())
            finally:
                cleanup_after_publication(outcome)
                shutil.rmtree(outcome.layout.next_stage_root, ignore_errors=True)

    def test_run_build_removes_work_root_when_owned_unit_execution_fails(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            request = _build_request(workspace_root, pool_size=1)

            with mock.patch(
                "apache_buildish_site_pipeline.staging.coordinator._run_owned_units",
                side_effect=RuntimeError("boom"),
            ), mock.patch(
                "apache_buildish_site_pipeline.staging.coordinator.remove_work_root",
            ) as remove_work_root:
                with self.assertRaisesRegex(RuntimeError, "boom"):
                    run_build(request)

        remove_work_root.assert_called_once()

    def test_materialize_stage_tree_returns_manifest_after_cleanup(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            request = _build_request(workspace_root, pool_size=1)
            outcome = SimpleNamespace(manifest=SimpleNamespace(schema_version=1))

            with mock.patch(
                "apache_buildish_site_pipeline.staging.coordinator.run_build",
                return_value=outcome,
            ) as run_build_mock, mock.patch(
                "apache_buildish_site_pipeline.staging.coordinator.cleanup_after_publication",
            ) as cleanup:
                manifest = materialize_stage_tree(
                    build_plan=request.build_plan,
                    diagnostics=request.diagnostics,
                    provider_snapshot=request.provider_snapshot,
                    stage_root=workspace_root / "visible-stage",
                )

        self.assertIs(manifest, outcome.manifest)
        run_build_mock.assert_called_once()
        cleanup.assert_called_once_with(outcome)

    def test_publish_stage_wraps_failures_when_retaining_assembly_root(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            request = _build_request(workspace_root, pool_size=1)
            assembly_root = workspace_root / "retained-assembly"
            assembly_root.mkdir(parents=True, exist_ok=True)

            with mock.patch(
                "apache_buildish_site_pipeline.staging.coordinator.run_build",
                side_effect=RuntimeError("boom"),
            ):
                with self.assertRaises(RetainedStageError) as failure:
                    publish_stage(
                        build_plan=request.build_plan,
                        diagnostics=request.diagnostics,
                        provider_snapshot=request.provider_snapshot,
                        stage_root=workspace_root / "visible-stage",
                        assembly_root=assembly_root,
                    )

            self.assertTrue(assembly_root.exists())

        self.assertIn("Retained failed stage assembly root", str(failure.exception))

    def test_publish_stage_removes_temporary_assembly_root_on_failure(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            request = _build_request(workspace_root, pool_size=1)
            temp_root = workspace_root / ".stage-build.failed"
            temp_root.mkdir(parents=True, exist_ok=True)

            with mock.patch(
                "apache_buildish_site_pipeline.staging.coordinator.tempfile.mkdtemp",
                return_value=str(temp_root),
            ), mock.patch(
                "apache_buildish_site_pipeline.staging.coordinator.run_build",
                side_effect=RuntimeError("boom"),
            ):
                with self.assertRaisesRegex(RuntimeError, "boom"):
                    publish_stage(
                        build_plan=request.build_plan,
                        diagnostics=request.diagnostics,
                        provider_snapshot=request.provider_snapshot,
                        stage_root=workspace_root / "visible-stage",
                    )

        self.assertFalse(temp_root.exists())

    def test_publish_stage_finalizes_and_cleans_up_on_success(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            request = _build_request(workspace_root, pool_size=1)
            outcome = SimpleNamespace(layout=SimpleNamespace(next_stage_root=workspace_root / "candidate-stage"))
            publication = SimpleNamespace(stage_root=workspace_root / "visible-stage")

            with mock.patch(
                "apache_buildish_site_pipeline.staging.coordinator.run_build",
                return_value=outcome,
            ), mock.patch(
                "apache_buildish_site_pipeline.staging.coordinator.finalize_stage_publication",
                return_value=publication,
            ) as finalize_stage_publication, mock.patch(
                "apache_buildish_site_pipeline.staging.coordinator.cleanup_after_publication",
            ) as cleanup:
                result = publish_stage(
                    build_plan=request.build_plan,
                    diagnostics=request.diagnostics,
                    provider_snapshot=request.provider_snapshot,
                    stage_root=workspace_root / "visible-stage",
                )

        self.assertIs(result, publication)
        finalize_stage_publication.assert_called_once_with(
            candidate_stage_root=outcome.layout.next_stage_root,
            stage_root=(workspace_root / "visible-stage").resolve(strict=False),
            allow_replace_existing=False,
        )
        cleanup.assert_called_once_with(outcome)

    def test_seed_next_stage_root_removes_paths_and_rejects_escape_attempts(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            seed_stage_root = workspace_root / "seed"
            seed_stage_root.mkdir(parents=True, exist_ok=True)
            (seed_stage_root / "keep.txt").write_text("keep\n", encoding="utf-8")
            (seed_stage_root / "remove.txt").write_text("remove\n", encoding="utf-8")
            (seed_stage_root / "nested").mkdir()
            (seed_stage_root / "nested/value.txt").write_text("nested\n", encoding="utf-8")

            candidate_stage_root = workspace_root / "candidate"
            _seed_next_stage_root(
                candidate_stage_root=candidate_stage_root,
                seed_stage_root=seed_stage_root,
                removals=("remove.txt", "nested", "missing.txt"),
            )

            self.assertTrue((candidate_stage_root / "keep.txt").is_file())
            self.assertFalse((candidate_stage_root / "remove.txt").exists())
            self.assertFalse((candidate_stage_root / "nested").exists())

            with self.assertRaisesRegex(StageIntegrityError, "escapes candidate root"):
                _seed_next_stage_root(
                    candidate_stage_root=workspace_root / "escape-candidate",
                    seed_stage_root=seed_stage_root,
                    removals=("../outside.txt",),
                )

    def test_run_worker_subprocess_rejects_exit_failures_and_malformed_json(self) -> None:
        spec = WorkerSpecWire(
            unit_id="spark",
            unit_kind="component",
            owner_id="spark",
            workspace_root="/workspace",
            fragment_path="/workspace/.work/fragments/spark.json",
        )

        with mock.patch(
            "apache_buildish_site_pipeline.staging.coordinator.subprocess.run",
            return_value=SimpleNamespace(returncode=7, stderr="boom", stdout=""),
        ):
            with self.assertRaisesRegex(StageIntegrityError, "exited with status 7: boom"):
                _run_worker_subprocess(spec)

        with mock.patch(
            "apache_buildish_site_pipeline.staging.coordinator.subprocess.run",
            return_value=SimpleNamespace(returncode=0, stderr="", stdout="{not-json"),
        ):
            with self.assertRaisesRegex(StageIntegrityError, "returned malformed JSON"):
                _run_worker_subprocess(spec)

    def test_context_wire_maps_candidate_and_named_ref_sections(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            request = _build_request(workspace_root, pool_size=1)
            layout = _work_layout(workspace_root)
            component = request.build_plan.site.components[0]
            component_unit = self._component_unit(request)
            released_context = next(
                owned_context
                for owned_context in component_unit.contexts
                if owned_context.context.kind is RecordKind.RELEASED
            )
            candidate_owned_context = replace(
                released_context,
                context_id="candidate",
                context=replace(
                    released_context.context,
                    kind=RecordKind.CANDIDATE,
                    version="4.0.0-rc1",
                    release_line="4.0",
                ),
            )
            named_ref_owned_context = replace(
                released_context,
                context_id="named-ref",
                context=replace(
                    released_context.context,
                    kind=RecordKind.NAMED_REF,
                    version=None,
                    named_ref_key="preview",
                    ref="refs/heads/preview",
                    release_line=None,
                ),
            )

            candidate_wire = build_context_wire(
                component=component,
                owned_context=candidate_owned_context,
                layout=layout,
            )
            named_ref_wire = build_context_wire(
                component=component,
                owned_context=named_ref_owned_context,
                layout=layout,
            )

        self.assertEqual((candidate_wire.page_kind, candidate_wire.section), ("candidate-page", "candidate"))
        self.assertTrue(candidate_wire.source_docs_root.endswith("/candidates/4.0.0-rc1"))
        self.assertEqual((named_ref_wire.page_kind, named_ref_wire.section), ("ref-page", "ref"))
        self.assertTrue(named_ref_wire.source_docs_root.endswith("/refs/preview"))

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

    def test_public_diagnostic_sanitizer_handles_nested_path_details(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            sanitized = sanitize_public_diagnostics(
                (
                    PipelineDiagnosticEntry(
                        severity=DiagnosticSeverity.WARNING,
                        code="demo.warning",
                        message="demo",
                        details={
                            "items": [
                                {"sourcePath": str(workspace_root / "components/runtime/docs/index.md")},
                                {"fragmentPath": str(workspace_root / ".work/fragments/component.json")},
                                {"externalUrl": "https://docs.example.org/spark/"},
                            ],
                            "manifestPath": str(workspace_root / "site/.stage/manifest.json"),
                        },
                    ),
                ),
                workspace_root=workspace_root,
                private_roots=(workspace_root / ".work", workspace_root / "site/.stage"),
            )

        self.assertEqual(sanitized[0].details["items"][0]["sourcePath"], "components/runtime/docs/index.md")
        self.assertEqual(sanitized[0].details["items"][1]["fragmentPath"], REDACTED_LOCAL_PATH)
        self.assertEqual(sanitized[0].details["items"][2]["externalUrl"], "https://docs.example.org/spark/")
        self.assertEqual(sanitized[0].details["manifestPath"], REDACTED_LOCAL_PATH)

    def test_stage_run_report_uses_planning_workspace_root_when_build_plan_is_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            report = build_stage_run_report(
                command=StageCommand.BUILD,
                evaluation=SimpleNamespace(
                    build_plan=None,
                    planning=SimpleNamespace(site=SimpleNamespace(workspace_root=workspace_root)),
                ),
                diagnostics=(
                    PipelineDiagnosticEntry(
                        severity=DiagnosticSeverity.WARNING,
                        code="demo.warning",
                        message="demo",
                        details={
                            "expectedLocalPath": str(workspace_root / "components/runtime/docs"),
                            "fragmentPath": str(workspace_root / ".work/fragments/component.json"),
                        },
                    ),
                ),
                succeeded=False,
                wrote_stage=False,
                stage_usable=False,
                stage_root_path=None,
                manifest_path=None,
                private_roots=(workspace_root / ".work",),
            )

        self.assertEqual(report.diagnostics[0].details["expectedLocalPath"], "components/runtime/docs")
        self.assertEqual(report.diagnostics[0].details["fragmentPath"], REDACTED_LOCAL_PATH)

    def test_content_index_omits_outside_workspace_source_paths(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            request = _build_request(workspace_root, pool_size=1)
            entries = _build_content_index_entries(
                request.build_plan,
                (
                    StagedPageContributionWire(
                        stage_relative_path="content/spark/releases/4.0.0/index.md",
                        component_slug="spark",
                        artifact_key="runtime",
                        section="release",
                        page_kind="release-page",
                        public_path="/spark/releases/4.0.0",
                        public_url="https://docs.example.org/spark/releases/4.0.0",
                        component_path="/spark/",
                        component_url="https://docs.example.org/spark/",
                        origin_key="docs",
                        source_path=str(Path(tempfile.gettempdir()) / "outside-source.md"),
                        canonical_url="https://docs.example.org/spark/releases/4.0.0",
                        version_kind="released",
                        version="4.0.0",
                    ),
                ),
            )

        self.assertIsNone(entries[0].source_path)