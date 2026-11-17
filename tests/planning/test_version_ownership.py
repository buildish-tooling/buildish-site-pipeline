# Copyright 2026 The Buildish Authors
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

"""Component-owned release decisions without a catalog version registry."""

import copy
import json
import shutil
import unittest

import yaml
from pydantic import ValidationError

from buildish_site_pipeline.cli.errors import InputDiagnosticError
from buildish_site_pipeline.commands.shared import load_workspace_inputs
from buildish_site_pipeline.models.authored.component_metadata import (
    ComponentMetadataDocumentV1,
)
from buildish_site_pipeline.models.enums import PlanningTarget, RecordKind
from buildish_site_pipeline.planning import evaluate_planning
from buildish_site_pipeline.planning.errors import PlanningInputFailure
from buildish_site_pipeline.staging.front_matter import (
    build_component_front_matter,
    build_version_context,
)
from tests.commands.test_component_snapshots import configure_snapshot
from tests.staging.test_component_publication import run
from tests.support.workspace import _workspace


def planning(root):
    loaded = load_workspace_inputs(root)
    return evaluate_planning(
        target=PlanningTarget.BUILD,
        workspace_root=root,
        catalog=loaded.catalog,
        provider_snapshot=loaded.provider_snapshot,
        component_documents=loaded.component_documents,
        snapshot_inputs=loaded.snapshot_inputs,
    )


def component_only(root):
    path, snapshot = configure_snapshot(root)
    catalog_path = root / "site/catalog.yaml"
    catalog = yaml.safe_load(catalog_path.read_text())
    catalog["components"][0].pop("artifacts")
    catalog_path.write_text(yaml.safe_dump(catalog, sort_keys=False))
    snapshot["records"] = [r for r in snapshot["records"] if r["kind"] != "lineHead"]
    artifact = snapshot["artifacts"][0]
    artifact["latestStable"] = "4.0.0"
    artifact["releaseLines"][0].pop("maintenanceRef")
    path.write_text(json.dumps(snapshot))
    return path, snapshot


class VersionOwnershipTests(unittest.TestCase):
    def test_snapshot_only_release_update_changes_staged_latest_without_catalog_edit(
        self,
    ):
        with _workspace(with_content_file=True) as root:
            path, snapshot = component_only(root)
            catalog_bytes = (root / "site/catalog.yaml").read_bytes()
            self.assertEqual(run(root)[0], 0)
            shutil.rmtree(root / "site/.stage")
            artifact = snapshot["artifacts"][0]
            artifact["latestStable"] = "4.0.1"
            artifact["releaseLines"][0]["latest"] = "4.0.1"
            artifact["releases"].append({"version": "4.0.1", "releaseLine": "4.0"})
            release = path.parent / "4.0.1"
            release.mkdir()
            (release / "index.md").write_text("new released documentation")
            path.write_text(json.dumps(snapshot))
            code, report, errors = run(root)
            self.assertEqual(code, 0, (report, errors))
            stage = root / "site/.stage"
            self.assertTrue((stage / "content/spark/releases/4.0.1/index.md").is_file())
            self.assertFalse((stage / "content/spark/releases/4.0.0").exists())
            artifacts = json.loads((stage / "data/artifacts.json").read_text())["items"]
            self.assertEqual(artifacts[0]["latestStable"], "4.0.1")
            self.assertEqual(
                build_component_front_matter(
                    component=planning(root).site.components[0], selected_versions=()
                ).latest_stable,
                "4.0.1",
            )
            self.assertEqual((root / "site/catalog.yaml").read_bytes(), catalog_bytes)

    def test_older_designation_shared_target_and_derived_ancestry_are_order_independent(
        self,
    ):
        for reverse in (False, True):
            with self.subTest(reverse=reverse), _workspace() as root:
                path, snapshot = component_only(root)
                artifact = snapshot["artifacts"][0]
                artifact["releaseLines"] = [
                    {"key": "4", "latest": "4.0.0"},
                    {"key": "4.0", "parent": "4", "latest": "4.0.0"},
                ]
                if reverse:
                    artifact["releaseLines"].reverse()
                artifact["releases"].append({"version": "4.0.9", "releaseLine": "4.0"})
                path.write_text(json.dumps(snapshot))
                result = planning(root)
                released = [
                    c
                    for c in result.selected_versions.contexts
                    if c.kind is RecordKind.RELEASED
                ]
                self.assertEqual(
                    [(c.version, c.release_line) for c in released], [("4.0.0", "4.0")]
                )
                self.assertFalse(
                    any(
                        c.kind is RecordKind.LINE_HEAD
                        for c in result.selected_versions.contexts
                    )
                )
                indexed = result.provider_index.contexts_by_artifact[
                    ("spark", "runtime")
                ].released_by_version["4.0.0"][0]
                self.assertEqual(indexed.release_line_ancestors, ("4",))

    def test_invalid_latest_membership_and_ancestry_fail_before_selection(self):
        for mutation in (
            "unknown",
            "candidate",
            "unrelated",
            "missing-primary",
            "ancestry",
            "cycle",
            "stable-candidate",
        ):
            with self.subTest(mutation=mutation), _workspace() as root:
                path, snapshot = component_only(root)
                artifact = snapshot["artifacts"][0]
                if mutation in ("unknown", "candidate"):
                    artifact["releaseLines"][0]["latest"] = "9.0"
                if mutation in ("candidate", "stable-candidate"):
                    snapshot["records"].append(
                        dict(snapshot["records"][0], kind="candidate", version="9.0")
                    )
                if mutation == "stable-candidate":
                    artifact["latestStable"] = "9.0"
                if mutation == "unrelated":
                    artifact["releaseLines"].append({"key": "3", "latest": "4.0.0"})
                if mutation == "missing-primary":
                    artifact["releases"][0].pop("releaseLine")
                if mutation == "ancestry":
                    snapshot["records"][0]["releaseLineAncestors"] = ["wrong"]
                if mutation == "cycle":
                    artifact["releaseLines"][0]["parent"] = "4.0"
                path.write_text(json.dumps(snapshot))
                with self.assertRaises((PlanningInputFailure, InputDiagnosticError)):
                    planning(root)

    def test_pin_does_not_change_single_artifact_recommendation_and_absence_has_no_fallback(
        self,
    ):
        with _workspace() as root:
            path, snapshot = component_only(root)
            artifact = snapshot["artifacts"][0]
            artifact["latestStable"] = "4.0.9"
            artifact["releases"].append({"version": "4.0.9", "releaseLine": "4.0"})
            path.write_text(json.dumps(snapshot))
            catalog_path = root / "site/catalog.yaml"
            catalog = yaml.safe_load(catalog_path.read_text())
            catalog["components"][0]["publicationSelection"] = {
                "releases": {"mode": "explicit", "versions": ["4.0.0"]}
            }
            catalog_path.write_text(yaml.safe_dump(catalog))
            component = planning(root).site.components[0]
            self.assertEqual(
                build_component_front_matter(
                    component=component, selected_versions=()
                ).latest_stable,
                "4.0.9",
            )
            path.unlink()
            component = planning(root).site.components[0]
            self.assertIsNone(
                build_component_front_matter(
                    component=component, selected_versions=()
                ).latest_stable
            )

    def test_multiple_static_artifacts_never_project_arbitrary_component_latest(self):
        with _workspace() as root:
            path, snapshot = component_only(root)
            meta_path = root / "components/runtime/site/component.yaml"
            meta = yaml.safe_load(meta_path.read_text())
            meta["artifacts"].append({"key": "another"})
            meta_path.write_text(yaml.safe_dump(meta))
            snapshot["artifacts"].append(
                {
                    "componentSlug": "spark",
                    "artifactKey": "another",
                    "latestStable": "2.0",
                    "releases": [{"version": "2.0"}],
                }
            )
            path.write_text(json.dumps(snapshot))
            component = planning(root).site.components[0]
            self.assertEqual(
                [a.lifecycle.latest_stable for a in component.artifacts],
                ["4.0.0", "2.0"],
            )
            self.assertIsNone(
                build_component_front_matter(
                    component=component, selected_versions=()
                ).latest_stable
            )

    def test_bound_component_rejects_all_aggregate_claims_even_missing_or_empty(self):
        for state in ("present", "absent", "empty"):
            for claim in ("section", "release", "development", "candidate"):
                with self.subTest(state=state, claim=claim), _workspace() as root:
                    path, snapshot = component_only(root)
                    if state == "absent":
                        path.unlink()
                    elif state == "empty":
                        path.write_text(
                            json.dumps(
                                {"schemaVersion": 1, "providers": [], "records": []}
                            )
                        )
                    aggregate_path = root / "site/provider-snapshot.json"
                    aggregate = json.loads(aggregate_path.read_text())
                    if claim == "section":
                        aggregate["artifacts"] = [
                            {"componentSlug": "spark", "artifactKey": "runtime"}
                        ]
                    else:
                        aggregate["records"] = [
                            {
                                "provider": "github",
                                "componentSlug": "spark",
                                "artifactKey": "runtime",
                                "kind": "released" if claim == "release" else claim,
                                "version": "unrelated",
                            }
                        ]
                    aggregate_path.write_text(json.dumps(aggregate))
                    with self.assertRaisesRegex(
                        InputDiagnosticError, "must not claim this component"
                    ) as caught:
                        load_workspace_inputs(root)
                    self.assertIn(str(path), str(caught.exception))
                    self.assertIn(str(aggregate_path), str(caught.exception))

    def test_artifact_identity_and_static_latest_hint_are_validated(self):
        for value in (
            {"lifecycle": {"latestStable": "1.0"}},
            {"artifacts": [{"key": "runtime"}, {"key": "runtime"}]},
        ):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                ComponentMetadataDocumentV1.model_validate(
                    {"schemaVersion": 1, "component": {"slug": "spark"}, **value}
                )
        with _workspace() as root:
            path, snapshot = component_only(root)
            snapshot["artifacts"][0]["artifactKey"] = "unknown"
            path.write_text(json.dumps(snapshot))
            with self.assertRaises(InputDiagnosticError):
                planning(root)

    def test_unbound_aggregate_component_can_coexist_with_bound_component(self):
        with _workspace() as root:
            path, snapshot = component_only(root)
            catalog_path = root / "site/catalog.yaml"
            catalog = yaml.safe_load(catalog_path.read_text())
            other = copy.deepcopy(catalog["components"][0])
            other["slug"] = "other"
            other.pop("providerSnapshot")
            other["publication"]["mountPath"] = "/other/"
            catalog["components"].append(other)
            catalog_path.write_text(yaml.safe_dump(catalog))
            aggregate_path = root / "site/provider-snapshot.json"
            aggregate = json.loads(aggregate_path.read_text())
            aggregate["artifacts"] = [
                dict(snapshot["artifacts"][0], componentSlug="other")
            ]
            aggregate["records"] = [dict(snapshot["records"][0], componentSlug="other")]
            aggregate_path.write_text(json.dumps(aggregate))
            result = planning(root)
            self.assertEqual(len(result.site.components), 2)

    def test_curated_release_ancestry_reaches_emitted_metadata(self):
        with _workspace(with_content_file=True) as root:
            path, snapshot = component_only(root)
            snapshot["providers"] = []
            snapshot["records"] = []
            snapshot["artifacts"][0]["releaseLines"] = [
                {"key": "4", "latest": "4.0.0"},
                {"key": "4.0", "parent": "4", "latest": "4.0.0"},
            ]
            path.write_text(json.dumps(snapshot))
            code, report, errors = run(root)
            self.assertEqual(code, 0, (report, errors))
            releases = json.loads(
                (root / "site/.stage/data/releases.json").read_text()
            )["items"]
            self.assertEqual(releases[0]["releaseLineAncestors"], ["4"])
            self.assertIn(
                "ancestors:",
                (
                    root / "site/.stage/content/spark/releases/4.0.0/index.md"
                ).read_text(),
            )
            self.assertIsNone(releases[0].get("provider"))

    def test_explicit_normalized_line_head_needs_no_ref(self):
        with _workspace() as root:
            path, snapshot = component_only(root)
            snapshot["artifacts"][0]["releaseLines"] = [
                {"key": "4", "latest": "4.0.0"},
                {"key": "4.0", "parent": "4", "latest": "4.0.0"},
            ]
            snapshot["records"].append(
                {
                    "provider": "github",
                    "kind": "lineHead",
                    "componentSlug": "spark",
                    "artifactKey": "runtime",
                    "releaseLine": "4.0",
                    "externalId": "head",
                    "commitSha": "abc123",
                }
            )
            path.write_text(json.dumps(snapshot))
            result = planning(root)
            contexts = result.selected_versions.contexts
            heads = [c for c in contexts if c.kind is RecordKind.LINE_HEAD]
            self.assertEqual(len(heads), 1)
            self.assertEqual(heads[0].commit_sha, "abc123")

            self.assertEqual(
                build_version_context(
                    component=result.site.components[0], context=heads[0]
                ).release_line.ancestors,
                ["4"],
            )

    def test_explicit_head_selection_defers_absent_inventory_but_rejects_unknown_present_line(
        self,
    ):
        with _workspace() as root:
            path, snapshot = component_only(root)
            catalog_path = root / "site/catalog.yaml"
            catalog = yaml.safe_load(catalog_path.read_text())
            catalog["components"][0]["publicationSelection"] = {
                "lineHeads": {"mode": "explicit", "keys": ["unknown"]}
            }
            catalog_path.write_text(yaml.safe_dump(catalog))
            path.unlink()
            self.assertFalse(
                any(
                    c.kind is RecordKind.LINE_HEAD
                    for c in planning(root).selected_versions.contexts
                )
            )
            path.write_text(json.dumps(snapshot))
            with self.assertRaisesRegex(
                PlanningInputFailure, "Unknown selected release-line"
            ):
                planning(root)
