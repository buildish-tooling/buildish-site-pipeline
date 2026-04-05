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

"""Tests for evaluation execution and stage gating."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_alias_collision_blocks_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            planning = _planning_eval(
                Path(tempdir),
                catalog=_catalog(
                    shared_mount_path=False,
                    spark_publication={"aliases": [{"path": "/flink/"}]},
                ),
            )
            result = run_evaluation(
                request=EvaluationRequest(mode=EvaluationMode.BUILD),
                planning=planning,
            )

        self.assertFalse(result.stage_gate.allowed)
        self.assertTrue(any(diagnostic.code == "publication-route-collision" for diagnostic in result.diagnostics))

    def test_unknown_internal_redirect_target_blocks_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            planning = _planning_eval(
                Path(tempdir),
                catalog=_catalog(
                    shared_mount_path=False,
                    spark_publication={
                        "redirects": [{"fromPath": "/spark/development/docs/", "target": "route:/spark/missing/"}],
                    },
                ),
            )
            result = run_evaluation(
                request=EvaluationRequest(mode=EvaluationMode.BUILD),
                planning=planning,
            )

        self.assertFalse(result.stage_gate.allowed)
        self.assertTrue(any(diagnostic.code == "redirect-target-unknown" for diagnostic in result.diagnostics))

    def test_redirect_loop_blocks_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            planning = _planning_eval(
                Path(tempdir),
                catalog=_catalog(
                    shared_mount_path=False,
                    spark_publication={
                        "redirects": [
                            {"fromPath": "/spark/development/docs/", "target": "route:/spark/archive/"},
                            {"fromPath": "/spark/archive/", "target": "route:/spark/development/docs/"},
                        ],
                    },
                ),
            )
            result = run_evaluation(
                request=EvaluationRequest(mode=EvaluationMode.BUILD),
                planning=planning,
            )

        self.assertFalse(result.stage_gate.allowed)
        self.assertTrue(any(diagnostic.code == "redirect-loop" for diagnostic in result.diagnostics))

    def test_invalid_canonical_path_blocks_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            planning = _planning_eval(
                Path(tempdir),
                catalog=_catalog(
                    shared_mount_path=False,
                    spark_publication={"canonicalPath": "/spark/missing/"},
                ),
            )
            result = run_evaluation(
                request=EvaluationRequest(mode=EvaluationMode.BUILD),
                planning=planning,
            )

        self.assertFalse(result.stage_gate.allowed)
        self.assertTrue(any(diagnostic.code == "publication-canonical-invalid" for diagnostic in result.diagnostics))

    def test_release_redirect_target_resolves_and_allows_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            planning = _planning_eval(
                Path(tempdir),
                catalog=_catalog(
                    shared_mount_path=False,
                    spark_publication={
                        "redirects": [
                            {
                                "fromPath": "/spark/development/docs/",
                                "target": "release:spark/runtime@4.0.0",
                            }
                        ],
                    },
                ),
            )
            result = run_evaluation(
                request=EvaluationRequest(mode=EvaluationMode.BUILD),
                planning=planning,
            )

        self.assertTrue(result.stage_gate.allowed)
        self.assertFalse(any(diagnostic.code.startswith("redirect-") for diagnostic in result.diagnostics))

    def test_malformed_front_matter_blocks_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            _prepare_workspace(workspace_root)
            (workspace_root / "components/runtime/docs/releases/4.0.0/bad.md").write_text(
                "---\ntitle: broken\n",
                encoding="utf-8",
            )
            planning = evaluate_planning(
                target=PlanningTarget.BUILD,
                catalog=_catalog(shared_mount_path=False),
                provider_snapshot=_provider_snapshot(),
                workspace_root=workspace_root,
            )
            result = run_evaluation(
                request=EvaluationRequest(mode=EvaluationMode.BUILD),
                planning=planning,
            )

        self.assertFalse(result.stage_gate.allowed)
        self.assertTrue(any(diagnostic.code == "page-front-matter-invalid" for diagnostic in result.diagnostics))

    def test_reserved_pipeline_namespace_blocks_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            _prepare_workspace(workspace_root)
            (workspace_root / "components/runtime/docs/releases/4.0.0/bad.md").write_text(
                "---\npipeline:\n  page:\n    title: nope\n---\nbody\n",
                encoding="utf-8",
            )
            planning = evaluate_planning(
                target=PlanningTarget.BUILD,
                catalog=_catalog(shared_mount_path=False),
                provider_snapshot=_provider_snapshot(),
                workspace_root=workspace_root,
            )
            result = run_evaluation(
                request=EvaluationRequest(mode=EvaluationMode.BUILD),
                planning=planning,
            )

        self.assertFalse(result.stage_gate.allowed)
        self.assertTrue(any(diagnostic.code == "page-reserved-namespace" for diagnostic in result.diagnostics))

    def test_symlink_escape_path_diagnostic_omits_absolute_path(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            _prepare_workspace(workspace_root)
            external_root = workspace_root / "external"
            _mkdir(external_root)
            (external_root / "escape.md").write_text("body\n", encoding="utf-8")
            (workspace_root / "components/runtime/docs/releases/4.0.0/outside").symlink_to(external_root, target_is_directory=True)
            planning = evaluate_planning(
                target=PlanningTarget.BUILD,
                catalog=_catalog(shared_mount_path=False),
                provider_snapshot=_provider_snapshot(),
                workspace_root=workspace_root,
            )
            result = run_evaluation(
                request=EvaluationRequest(mode=EvaluationMode.BUILD),
                planning=planning,
            )

        path_diagnostic = next(diagnostic for diagnostic in result.diagnostics if diagnostic.code == "page-path-outside-root")
        self.assertFalse(result.stage_gate.allowed)
        self.assertNotIn(tempdir, path_diagnostic.message)
        self.assertNotIn(tempdir, json.dumps(path_diagnostic.details))

    def test_duplicate_locale_translation_blocks_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            _prepare_workspace(workspace_root)
            release_root = workspace_root / "components/runtime/docs/releases/4.0.0"
            _mkdir(release_root / "en")
            _mkdir(release_root / "de")
            (release_root / "en/guide.md").write_text("---\ntranslationKey: guide\n---\nbody\n", encoding="utf-8")
            (release_root / "en/guide-copy.md").write_text("---\ntranslationKey: guide\n---\nbody\n", encoding="utf-8")
            planning = evaluate_planning(
                target=PlanningTarget.BUILD,
                catalog=_catalog(
                    shared_mount_path=False,
                    spark_localization={
                        "supportedLocales": ["en", "de"],
                        "defaultLocale": "en",
                        "routeMode": "prefixAll",
                    },
                ),
                provider_snapshot=_provider_snapshot(),
                workspace_root=workspace_root,
            )
            result = run_evaluation(
                request=EvaluationRequest(mode=EvaluationMode.BUILD),
                planning=planning,
            )

        self.assertFalse(result.stage_gate.allowed)
        self.assertTrue(any(diagnostic.code == "translation-locale-duplicate" for diagnostic in result.diagnostics))

    def test_translation_linkage_conflict_blocks_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            _prepare_workspace(workspace_root)
            release_root = workspace_root / "components/runtime/docs/releases/4.0.0"
            _mkdir(release_root / "en")
            _mkdir(release_root / "de")
            (release_root / "en/guide.md").write_text("---\ntranslationKey: guide\n---\nbody\n", encoding="utf-8")
            (release_root / "de/guide.md").write_text("---\ntranslationKey: handbuch\n---\nbody\n", encoding="utf-8")
            planning = evaluate_planning(
                target=PlanningTarget.BUILD,
                catalog=_catalog(
                    shared_mount_path=False,
                    spark_localization={
                        "supportedLocales": ["en", "de"],
                        "defaultLocale": "en",
                        "routeMode": "prefixAll",
                    },
                ),
                provider_snapshot=_provider_snapshot(),
                workspace_root=workspace_root,
            )
            result = run_evaluation(
                request=EvaluationRequest(mode=EvaluationMode.BUILD),
                planning=planning,
            )

        self.assertFalse(result.stage_gate.allowed)
        self.assertTrue(any(diagnostic.code == "translation-linkage-conflict" for diagnostic in result.diagnostics))

    def test_translation_route_inconsistency_blocks_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            _prepare_workspace(workspace_root)
            release_root = workspace_root / "components/runtime/docs/releases/4.0.0"
            _mkdir(release_root / "en")
            _mkdir(release_root / "de")
            (release_root / "en/guide.md").write_text("---\ntranslationKey: guide\n---\nbody\n", encoding="utf-8")
            (release_root / "de/uebersicht.md").write_text("---\ntranslationKey: guide\n---\nbody\n", encoding="utf-8")
            planning = evaluate_planning(
                target=PlanningTarget.BUILD,
                catalog=_catalog(
                    shared_mount_path=False,
                    spark_localization={
                        "supportedLocales": ["en", "de"],
                        "defaultLocale": "en",
                        "routeMode": "prefixAll",
                    },
                ),
                provider_snapshot=_provider_snapshot(),
                workspace_root=workspace_root,
            )
            result = run_evaluation(
                request=EvaluationRequest(mode=EvaluationMode.BUILD),
                planning=planning,
            )

        self.assertFalse(result.stage_gate.allowed)
        self.assertTrue(any(diagnostic.code == "translation-route-inconsistent" for diagnostic in result.diagnostics))

    def test_unknown_exact_release_reference_blocks_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            planning = _planning_eval(
                Path(tempdir),
                catalog=_catalog(
                    shared_mount_path=False,
                    spark_artifact={
                        "publicationSelection": {
                            "releases": {"mode": "explicit", "versions": ["9.9.9"]},
                        },
                    },
                ),
            )
            result = run_evaluation(
                request=EvaluationRequest(mode=EvaluationMode.BUILD),
                planning=planning,
            )

        self.assertFalse(result.stage_gate.allowed)
        self.assertTrue(any(diagnostic.code == "reference-configuration-invalid" for diagnostic in result.diagnostics))

    def test_unknown_compatibility_reference_blocks_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            planning = _planning_eval(
                Path(tempdir),
                catalog=_catalog(
                    shared_mount_path=False,
                    spark_artifact={
                        "compatibility": [
                            {
                                "subjectRef": "artifact:spark/runtime",
                                "targetRef": "artifact:spark/missing",
                                "relation": "supports",
                            }
                        ],
                    },
                ),
            )
            result = run_evaluation(
                request=EvaluationRequest(mode=EvaluationMode.BUILD),
                planning=planning,
            )

        self.assertFalse(result.stage_gate.allowed)
        self.assertTrue(any(diagnostic.code == "compatibility-reference-unknown" for diagnostic in result.diagnostics))

    def test_named_ref_provider_ambiguity_blocks_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            planning = _planning_eval(
                Path(tempdir),
                catalog=_catalog(
                    shared_mount_path=False,
                    spark_artifact={
                        "versioning": {
                            "developmentRef": "main",
                            "tagPattern": "^v.*$",
                            "namedRefs": [{"key": "stable", "ref": "refs/heads/stable", "maturity": "stable"}],
                        },
                        "publicationSelection": {
                            "namedRefs": ["stable"],
                        },
                    },
                ),
                provider_snapshot=_provider_snapshot(
                    extra_records=[
                        {
                            "provider": "github",
                            "kind": "namedRef",
                            "componentSlug": "spark",
                            "artifactKey": "runtime",
                            "namedRefKey": "stable",
                            "ref": "refs/heads/stable",
                            "externalId": "stable-1",
                        },
                        {
                            "provider": "github",
                            "kind": "namedRef",
                            "componentSlug": "spark",
                            "artifactKey": "runtime",
                            "namedRefKey": "stable",
                            "ref": "refs/heads/stable",
                            "externalId": "stable-2",
                        },
                    ]
                ),
            )
            result = run_evaluation(
                request=EvaluationRequest(mode=EvaluationMode.BUILD),
                planning=planning,
            )

        self.assertFalse(result.stage_gate.allowed)
        self.assertTrue(any(diagnostic.code == "provider-context-ambiguous" for diagnostic in result.diagnostics))

    def test_route_inventory_limit_blocks_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            with patch("apache_buildish_site_pipeline.evaluation.limits._ROUTE_INVENTORY_LIMIT", 1):
                planning = _planning_eval(Path(tempdir))
                result = run_evaluation(
                    request=EvaluationRequest(mode=EvaluationMode.BUILD),
                    planning=planning,
                )

        limit_diagnostic = next(diagnostic for diagnostic in result.diagnostics if diagnostic.code == "operational-limit-exceeded")
        self.assertFalse(result.stage_gate.allowed)
        self.assertEqual(limit_diagnostic.details["metric"], "routeInventoryCount")

    def test_selected_version_context_limit_blocks_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            with patch("apache_buildish_site_pipeline.evaluation.limits._SELECTED_VERSION_CONTEXT_LIMIT", 1):
                planning = _planning_eval(Path(tempdir))
                result = run_evaluation(
                    request=EvaluationRequest(mode=EvaluationMode.BUILD),
                    planning=planning,
                )

        limit_diagnostic = next(diagnostic for diagnostic in result.diagnostics if diagnostic.code == "operational-limit-exceeded")
        self.assertFalse(result.stage_gate.allowed)
        self.assertEqual(limit_diagnostic.details["metric"], "selectedVersionContextCount")

    def test_provider_snapshot_size_limit_blocks_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            with patch("apache_buildish_site_pipeline.evaluation.limits._PROVIDER_SNAPSHOT_BYTES_LIMIT", 1):
                planning = _planning_eval(Path(tempdir))
                result = run_evaluation(
                    request=EvaluationRequest(mode=EvaluationMode.BUILD),
                    planning=planning,
                )

        limit_diagnostic = next(diagnostic for diagnostic in result.diagnostics if diagnostic.code == "operational-limit-exceeded")
        self.assertFalse(result.stage_gate.allowed)
        self.assertEqual(limit_diagnostic.details["metric"], "providerSnapshotBytes")

    def test_watch_filesystem_entry_limit_blocks_watch_stage(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            _prepare_workspace(workspace_root)
            (workspace_root / "components/runtime/docs/releases/4.0.0/one.md").write_text("body\n", encoding="utf-8")
            (workspace_root / "components/runtime/docs/releases/4.0.0/two.md").write_text("body\n", encoding="utf-8")
            with patch("apache_buildish_site_pipeline.evaluation.limits._WATCH_FILESYSTEM_ENTRY_LIMIT", 1):
                planning = evaluate_planning(
                    target=PlanningTarget.WATCH,
                    catalog=_catalog(shared_mount_path=False),
                    provider_snapshot=_provider_snapshot(),
                    workspace_root=workspace_root,
                )
                result = run_evaluation(
                    request=EvaluationRequest(mode=EvaluationMode.WATCH),
                    planning=planning,
                )

        limit_diagnostic = next(diagnostic for diagnostic in result.diagnostics if diagnostic.code == "operational-limit-exceeded")
        self.assertFalse(result.stage_gate.allowed)
        self.assertEqual(limit_diagnostic.details["metric"], "watchFilesystemEntryCount")


def _planning_eval(
    workspace_root: Path,
    *,
    stale_release: bool = False,
    catalog: CatalogDocumentV1 | None = None,
    provider_snapshot: ProviderSnapshotV1 | None = None,
):
    catalog = _catalog(shared_mount_path=False) if catalog is None else catalog
    provider_snapshot = _provider_snapshot() if provider_snapshot is None else provider_snapshot
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


def _catalog(
    *,
    shared_mount_path: bool,
    spark_publication: dict[str, object] | None = None,
    flink_publication: dict[str, object] | None = None,
    spark_localization: dict[str, object] | None = None,
    spark_artifact: dict[str, object] | None = None,
    flink_artifact: dict[str, object] | None = None,
) -> CatalogDocumentV1:
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
                    "publication": {"mountPath": "/spark/", **(spark_publication or {})},
                    **({"localization": spark_localization} if spark_localization is not None else {}),
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
                            **(spark_artifact or {}),
                        }
                    ],
                },
                {
                    "slug": "flink",
                    "content": {"source": "runtime-two"},
                    "publication": {"mountPath": runtime_two_mount_path, **(flink_publication or {})},
                    "artifacts": [
                        {
                            "key": "runtime",
                            "source": "runtime-two",
                            "versioning": {"developmentRef": "main", "tagPattern": "^v.*$"},
                            **(flink_artifact or {}),
                        }
                    ],
                },
            ],
        },
        by_alias=True,
        by_name=False,
    )


def _provider_snapshot(*, extra_records: list[dict[str, object]] | None = None) -> ProviderSnapshotV1:
    return ProviderSnapshotV1.model_validate(
        {
            "schemaVersion": 1,
            "providers": [{"key": "github", "type": "githubReleases", "fetchedAt": "2026-04-03T00:00:00Z"}],
            "records": [
                {"provider": "github", "kind": "development", "componentSlug": "spark", "artifactKey": "runtime", "ref": "main"},
                {"provider": "github", "kind": "lineHead", "componentSlug": "spark", "artifactKey": "runtime", "releaseLine": "4.0", "ref": "maintenance/4.0"},
                {"provider": "github", "kind": "released", "componentSlug": "spark", "artifactKey": "runtime", "version": "4.0.0", "tag": "v4.0.0"},
                {"provider": "github", "kind": "development", "componentSlug": "flink", "artifactKey": "runtime", "ref": "main"},
                *(extra_records or []),
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