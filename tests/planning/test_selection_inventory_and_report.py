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

"""Tests for planning selection, inventory, readiness, watch roots, and reporting."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from apache_buildish_site_pipeline.cli.errors import CommandExecutionError
from apache_buildish_site_pipeline.models import CatalogDocumentV1, PlanningTarget, ProviderSnapshotV1
from apache_buildish_site_pipeline.models.enums import MaterializationInputKind, MaterializationStatus
from apache_buildish_site_pipeline.planning import build_resolved_materialization_report, evaluate_planning
from apache_buildish_site_pipeline.planning.types import InputReadiness, LocalInputIdentity, ResolvedLocalInput
from apache_buildish_site_pipeline.planning.watch_roots import derive_watch_plan


class PlanningEvaluationTests(unittest.TestCase):
    def test_build_target_creates_ready_build_plan(self) -> None:
        catalog = _sample_catalog()
        provider_snapshot = _sample_provider_snapshot()
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            _mkdir(workspace_root / "site/root-pages")
            _mkdir(workspace_root / "site/root-assets")
            _mkdir(workspace_root / "vendor/brand")
            _mkdir(workspace_root / "components/runtime/docs")
            _mkdir(workspace_root / "components/runtime/docs/releases/4.0.0")
            _mkdir(workspace_root / "components/runtime/docs/maintenance/4.0")

            evaluation = evaluate_planning(
                target=PlanningTarget.BUILD,
                catalog=catalog,
                provider_snapshot=provider_snapshot,
                workspace_root=workspace_root,
            )

        self.assertTrue(evaluation.selected_versions.deterministic)
        self.assertTrue(evaluation.build_bridge.ready)
        self.assertIsNotNone(evaluation.build_plan_candidate)
        self.assertTrue(all(local_input.watch_eligible is not None for local_input in evaluation.local_inputs))

    def test_watch_target_marks_released_context_not_watch_eligible_and_detects_stale_marker(self) -> None:
        catalog = _sample_catalog()
        provider_snapshot = _sample_provider_snapshot()
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            _mkdir(workspace_root / "site/root-pages")
            _mkdir(workspace_root / "site/root-assets")
            _mkdir(workspace_root / "vendor/brand")
            development_root = workspace_root / "components/runtime/docs"
            released_root = workspace_root / "components/runtime/docs/releases/4.0.0"
            _mkdir(development_root)
            _mkdir(workspace_root / "components/runtime/docs/maintenance/4.0")
            _mkdir(released_root)
            (released_root / ".site-pipeline-materialization.json").write_text(
                json.dumps({"version": "3.9.0"}),
                encoding="utf-8",
            )

            evaluation = evaluate_planning(
                target=PlanningTarget.WATCH,
                catalog=catalog,
                provider_snapshot=provider_snapshot,
                workspace_root=workspace_root,
                stage_root=workspace_root / ".stage",
                work_root=workspace_root / ".work",
                report_output=workspace_root / "materialization-report.json",
            )
            report = build_resolved_materialization_report(evaluation)

        released_entries = [entry for entry in report.entries if entry.input_kind.value == "released"]
        self.assertEqual(released_entries[0].status, MaterializationStatus.STALE)
        self.assertFalse(released_entries[0].watch_eligible)
        self.assertTrue(all(entry.watch_eligible is not None for entry in report.entries))

    def test_watch_target_excludes_conflicting_watch_roots(self) -> None:
        catalog = _sample_catalog()
        provider_snapshot = _sample_provider_snapshot()
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            _mkdir(workspace_root / "site/root-pages")
            _mkdir(workspace_root / "site/root-assets")
            _mkdir(workspace_root / "vendor/brand")
            _mkdir(workspace_root / "components/runtime/docs")
            _mkdir(workspace_root / "components/runtime/docs/maintenance/4.0")
            _mkdir(workspace_root / "components/runtime/docs/releases/4.0.0")
            stage_root = workspace_root / "components/runtime/docs"

            evaluation = evaluate_planning(
                target=PlanningTarget.WATCH,
                catalog=catalog,
                provider_snapshot=provider_snapshot,
                workspace_root=workspace_root,
                stage_root=stage_root,
            )

        self.assertIsNotNone(evaluation.watch_plan)
        self.assertEqual(evaluation.watch_plan.roots, (workspace_root / "site/root-assets", workspace_root / "site/root-pages", workspace_root / "vendor/brand"))
        self.assertEqual(len(evaluation.watch_plan.diagnostics), 2)

    def test_watch_target_rejects_more_than_32_watch_roots_with_clear_limit_error(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            local_inputs: list[ResolvedLocalInput] = []
            for root_number in range(33):
                watched_root = workspace_root / "watched" / f"root-{root_number:02d}"
                _mkdir(watched_root)
                local_inputs.append(
                    ResolvedLocalInput(
                        identity=LocalInputIdentity(
                            source_key=f"source-{root_number:02d}",
                            input_kind=MaterializationInputKind.DEVELOPMENT,
                            component_slug=f"component-{root_number:02d}",
                            artifact_key="runtime",
                            ref="main",
                        ),
                        declared_root=watched_root,
                        expected_local_path=watched_root,
                        provenance=None,
                        readiness=InputReadiness(status=MaterializationStatus.PRESENT),
                    )
                )

            with self.assertRaisesRegex(CommandExecutionError, "32 watch-root ceiling"):
                derive_watch_plan(
                    target=PlanningTarget.WATCH,
                    workspace_root=workspace_root,
                    local_inputs=tuple(local_inputs),
                )


def _sample_catalog() -> CatalogDocumentV1:
    return CatalogDocumentV1.model_validate(
        {
            "schemaVersion": 1,
            "defaults": {
                "metadataFile": "site/component.yaml",
                "pagesRoot": "site/pages",
                "docsRoot": "docs",
                "assetsRoot": "assets",
                "publication": {
                    "origin": "docs",
                    "developmentSegment": "development",
                    "docsSegment": "docs",
                    "assetsSegment": "assets",
                },
            },
            "site": {
                "pagesRoot": "site/root-pages",
                "assetsRoot": "site/root-assets",
                "vendorAssets": [{"source": "vendor/brand", "mountPath": "/assets/vendor/brand/"}],
            },
            "origins": {"docs": {"baseUrl": "https://docs.example.org"}},
            "sources": {"runtime": {"localDir": "components/runtime"}},
            "components": [
                {
                    "slug": "spark",
                    "content": {"source": "runtime"},
                    "publication": {"mountPath": "/spark/"},
                    "artifacts": [
                        {
                            "key": "runtime",
                            "source": "runtime",
                            "versioning": {
                                "developmentRef": "main",
                                "tagPattern": "^v.*$",
                            },
                            "publicationSelection": {
                                "development": True,
                                "lineHeads": {"mode": "allAuthored"},
                                "releases": {"mode": "latestPerLine"},
                                "candidates": {"mode": "none"},
                            },
                            "lifecycle": {
                                "releaseLines": [
                                    {"key": "4.0", "maintenanceRef": "maintenance/4.0", "latest": "4.0.0"}
                                ],
                                "releases": [{"version": "4.0.0"}],
                            },
                        }
                    ],
                }
            ],
        },
        by_alias=True,
        by_name=False,
    )


def _sample_provider_snapshot() -> ProviderSnapshotV1:
    return ProviderSnapshotV1.model_validate(
        {
            "schemaVersion": 1,
            "providers": [
                {
                    "key": "github",
                    "type": "githubReleases",
                    "fetchedAt": "2026-04-03T00:00:00Z",
                }
            ],
            "records": [
                {
                    "provider": "github",
                    "kind": "development",
                    "componentSlug": "spark",
                    "artifactKey": "runtime",
                    "ref": "main",
                    "commitSha": "aaaa",
                },
                {
                    "provider": "github",
                    "kind": "lineHead",
                    "componentSlug": "spark",
                    "artifactKey": "runtime",
                    "releaseLine": "4.0",
                    "ref": "maintenance/4.0",
                    "commitSha": "bbbb",
                },
                {
                    "provider": "github",
                    "kind": "released",
                    "componentSlug": "spark",
                    "artifactKey": "runtime",
                    "version": "4.0.0",
                    "tag": "v4.0.0",
                },
            ],
        },
        by_alias=True,
        by_name=False,
    )


def _mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)