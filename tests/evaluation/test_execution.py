# Copyright 2026 The Apache Software Foundation

"""Tests for evaluation execution and stage gating."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from apache_buildish_site_pipeline.evaluation import EvaluationMode, EvaluationRequest, build_check_report, run_evaluation
from apache_buildish_site_pipeline.models import CatalogDocumentV1, PlanningTarget, ProviderSnapshotV1
from apache_buildish_site_pipeline.models.enums import RunStatus
from apache_buildish_site_pipeline.planning import evaluate_planning


class EvaluationExecutionTests(unittest.TestCase):
    def test_clean_build_allows_staging(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            planning = _planning_eval(Path(tempdir))
            result = run_evaluation(
                request=EvaluationRequest(mode=EvaluationMode.BUILD),
                planning=planning,
            )

        self.assertTrue(result.stage_gate.allowed)
        self.assertIsNotNone(result.build_plan)
        self.assertEqual(result.run_status, RunStatus.CLEAN)

    def test_stale_input_blocks_stage_and_appears_in_check_report(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            planning = _planning_eval(workspace_root, stale_release=True)
            result = run_evaluation(
                request=EvaluationRequest(mode=EvaluationMode.CHECK),
                planning=planning,
            )
            report = build_check_report(result)

        self.assertFalse(result.stage_gate.allowed)
        self.assertEqual(result.run_status, RunStatus.ERRORS)
        self.assertTrue(any(diagnostic.code == "input-stale" for diagnostic in report.diagnostics))

    def test_route_collision_blocks_stage(self) -> None:
        catalog = _catalog(shared_mount_path=True)
        provider_snapshot = _provider_snapshot()
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            _prepare_workspace(workspace_root)
            _mkdir(workspace_root / "components/runtime-two/docs")
            _mkdir(workspace_root / "components/runtime-two/docs/maintenance/4.0")
            _mkdir(workspace_root / "components/runtime-two/docs/releases/4.0.0")
            planning = evaluate_planning(
                target=PlanningTarget.BUILD,
                catalog=catalog,
                provider_snapshot=provider_snapshot,
                workspace_root=workspace_root,
            )
            result = run_evaluation(
                request=EvaluationRequest(mode=EvaluationMode.BUILD),
                planning=planning,
            )

        self.assertFalse(result.stage_gate.allowed)
        self.assertTrue(any(diagnostic.code == "publication-route-collision" for diagnostic in result.diagnostics))


def _planning_eval(workspace_root: Path, *, stale_release: bool = False):
    catalog = _catalog(shared_mount_path=False)
    provider_snapshot = _provider_snapshot()
    _prepare_workspace(workspace_root)
    if stale_release:
        marker_path = workspace_root / "components/runtime/docs/releases/4.0.0/.site-pipeline-materialization.json"
        marker_path.write_text(json.dumps({"version": "3.9.0"}), encoding="utf-8")
    return evaluate_planning(
        target=PlanningTarget.BUILD,
        catalog=catalog,
        provider_snapshot=provider_snapshot,
        workspace_root=workspace_root,
    )


def _catalog(*, shared_mount_path: bool) -> CatalogDocumentV1:
    runtime_two_mount_path = "/spark/" if shared_mount_path else "/flink/"
    return CatalogDocumentV1.model_validate(
        {
            "schemaVersion": 1,
            "defaults": {
                "docsRoot": "docs",
                "publication": {"origin": "docs"},
            },
            "site": {},
            "origins": {"docs": {"baseUrl": "https://docs.example.org"}},
            "sources": {
                "runtime": {"localDir": "components/runtime"},
                "runtime-two": {"localDir": "components/runtime-two"},
            },
            "components": [
                {
                    "slug": "spark",
                    "content": {"source": "runtime"},
                    "publication": {"mountPath": "/spark/"},
                    "artifacts": [
                        {
                            "key": "runtime",
                            "source": "runtime",
                            "versioning": {"developmentRef": "main", "tagPattern": "^v.*$"},
                            "publicationSelection": {
                                "development": True,
                                "lineHeads": {"mode": "allAuthored"},
                                "releases": {"mode": "latestPerLine"},
                            },
                            "lifecycle": {
                                "releaseLines": [{"key": "4.0", "maintenanceRef": "maintenance/4.0", "latest": "4.0.0"}],
                                "releases": [{"version": "4.0.0"}],
                            },
                        }
                    ],
                },
                {
                    "slug": "flink",
                    "content": {"source": "runtime-two"},
                    "publication": {"mountPath": runtime_two_mount_path},
                    "artifacts": [
                        {
                            "key": "runtime",
                            "source": "runtime-two",
                            "versioning": {"developmentRef": "main", "tagPattern": "^v.*$"},
                        }
                    ],
                },
            ],
        },
        by_alias=True,
        by_name=False,
    )


def _provider_snapshot() -> ProviderSnapshotV1:
    return ProviderSnapshotV1.model_validate(
        {
            "schemaVersion": 1,
            "providers": [{"key": "github", "type": "githubReleases", "fetchedAt": "2026-04-03T00:00:00Z"}],
            "records": [
                {"provider": "github", "kind": "development", "componentSlug": "spark", "artifactKey": "runtime", "ref": "main"},
                {"provider": "github", "kind": "lineHead", "componentSlug": "spark", "artifactKey": "runtime", "releaseLine": "4.0", "ref": "maintenance/4.0"},
                {"provider": "github", "kind": "released", "componentSlug": "spark", "artifactKey": "runtime", "version": "4.0.0", "tag": "v4.0.0"},
                {"provider": "github", "kind": "development", "componentSlug": "flink", "artifactKey": "runtime", "ref": "main"},
            ],
        },
        by_alias=True,
        by_name=False,
    )


def _prepare_workspace(workspace_root: Path) -> None:
    _mkdir(workspace_root / "components/runtime/docs")
    _mkdir(workspace_root / "components/runtime/docs/maintenance/4.0")
    _mkdir(workspace_root / "components/runtime/docs/releases/4.0.0")
    _mkdir(workspace_root / "components/runtime-two/docs")


def _mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)