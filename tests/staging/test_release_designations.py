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

"""Literal recommendation, stage evidence and renderer adoption regressions."""

import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

from pydantic import ValidationError
import yaml

from buildish_site_pipeline.cli.errors import StageIntegrityError
from buildish_site_pipeline.commands.shared import load_workspace_inputs
from buildish_site_pipeline.models.enums import PlanningTarget
from buildish_site_pipeline.models.emitted.release_designations import (
    ReleaseDesignationTarget,
)
from buildish_site_pipeline.planning import evaluate_planning
from buildish_site_pipeline.planning.errors import PlanningInputFailure
from buildish_site_pipeline.staging.aggregates import _build_redirect_entries
from buildish_site_pipeline.staging.destination_claims import collect_destination_claims
from buildish_site_pipeline.staging.incremental_metadata import (
    PersistedUnitContributionsV1,
)
from buildish_site_pipeline.staging.release_designations import (
    build_release_designations,
)
from buildish_site_pipeline.staging.worker_entrypoint import execute_worker_spec
from tests.planning.test_version_ownership import planning
from tests.staging.test_artifact_routes import configure_routes
from tests.staging.test_component_publication import configure_release, run
from tests.support.workspace import _workspace


def artifact_rows(root):
    return json.loads((root / "site/.stage/data/artifacts.json").read_text())["items"]


def pin(root, versions, *, development=False):
    path = root / "site/catalog.yaml"
    catalog = yaml.safe_load(path.read_text())
    catalog["components"][0]["publicationSelection"] = {
        "development": development,
        "lineHeads": {"mode": "none"},
        "releases": {"mode": "explicit", "versions": versions}
        if versions
        else {"mode": "none"},
    }
    catalog["components"][0]["artifacts"][0].pop("publicationSelection", None)
    path.write_text(yaml.safe_dump(catalog))


def add_recommendation(snapshot, version="4.0.1"):
    artifact = snapshot["artifacts"][0]
    artifact["latestStable"] = version
    artifact["releaseLines"][0]["latest"] = version
    artifact["releases"].append({"version": version, "releaseLine": "4.0"})
    record = next(
        record for record in snapshot["records"] if record["kind"] == "released"
    )
    snapshot["records"].append(
        dict(
            record,
            version=version,
            externalId="new-release",
            publicationState="published",
        )
    )


def consumer_view(rows, component, *, explicit=None, page_artifact=None):
    """Fixture for the documented link, summary and recommendation-navigation recipe."""
    candidates = [row for row in rows if row["componentSlug"] == component["slug"]]
    key = explicit or page_artifact or component["publication"].get("defaultArtifact")
    if key is None and len(candidates) == 1:
        key = candidates[0]["key"]
    matches = [row for row in candidates if row["key"] == key]
    if len(matches) != 1:
        raise ValueError("Explicit artifact required")
    view = matches[0]["releaseDesignations"]
    pointers = ([view["latestStable"]] if "latestStable" in view else []) + [
        line["target"] for line in view["lines"]
    ]
    return {
        "versions": [target["version"] for target in pointers],
        "docsLinks": list(
            dict.fromkeys(
                target["availability"]["url"]
                for target in pointers
                if target["availability"]["kind"] == "docs"
            )
        ),
        "kinds": [target["availability"]["kind"] for target in pointers],
    }


def exact_docs_link(stage, *, slug, artifact, version):
    """Fixture for an exact-version request using existing public aggregates."""
    routes = json.loads((stage / "data/routes.json").read_text())["items"]
    roots = {
        (row["originKey"], row["path"].rstrip("/"))
        for row in routes
        if row["componentSlug"] == slug
        and row.get("artifactKey") == artifact
        and row.get("section") == "released"
        and row.get("routeKind") == "context"
    }
    index_path = stage / "data/content-index.json"
    pages = json.loads(index_path.read_text())["items"] if index_path.exists() else []
    matches = [
        page
        for page in pages
        if page["componentSlug"] == slug
        and page.get("artifactKey") == artifact
        and page.get("versionLabel") == version
        and page.get("versionKind") == "released"
        and page["pageKind"] == "release-page"
        and (page["originKey"], page["path"].rstrip("/")) in roots
        and (not page.get("locale") or page.get("defaultLocale"))
    ]
    return matches[0]["url"] if len(matches) == 1 else None


class ReleaseDesignationTests(unittest.TestCase):
    def build(self, root):
        code, report, errors = run(root)
        self.assertEqual(code, 0, (report, errors))
        return artifact_rows(root)

    def test_pin_preserves_recommendation_without_extra_staging(self):
        with _workspace(with_content_file=True) as root:
            path, snapshot = configure_release(root)
            add_recommendation(snapshot)
            path.write_text(json.dumps(snapshot))
            pin(root, ["4.0.0"])
            row = self.build(root)[0]
            target = {
                "version": "4.0.1",
                "selected": False,
                "publicationState": "published",
                "availability": {"kind": "unavailable", "reason": "not-selected"},
            }
            self.assertEqual(
                row["releaseDesignations"],
                {
                    "snapshotStatus": "present",
                    "latestStable": target,
                    "lines": [{"key": "4.0", "target": target}],
                },
            )
            self.assertEqual(row["latestStable"], "4.0.1")
            self.assertNotIn("latestRelease", row)
            self.assertFalse(
                (root / "site/.stage/content/spark/releases/4.0.1").exists()
            )
            component = {"slug": "spark", "publication": {}}
            self.assertEqual(
                consumer_view([row], component),
                {
                    "versions": ["4.0.1", "4.0.1"],
                    "docsLinks": [],
                    "kinds": ["unavailable", "unavailable"],
                },
            )

    def test_older_overall_line_only_and_parent_child_pointers(self):
        with _workspace(with_content_file=True) as root:
            path, snapshot = configure_release(root)
            add_recommendation(snapshot)
            snapshot["artifacts"][0]["latestStable"] = "4.0.0"
            snapshot["artifacts"][0]["releaseLines"].insert(
                0, {"key": "4", "latest": "4.0.1"}
            )
            snapshot["artifacts"][0]["releaseLines"][1]["parent"] = "4"
            path.write_text(json.dumps(snapshot))
            pin(root, ["4.0.0"])
            row = self.build(root)[0]
            self.assertEqual(
                row["releaseDesignations"]["latestStable"]["version"], "4.0.0"
            )
            self.assertEqual(
                [
                    line["target"]["version"]
                    for line in row["releaseDesignations"]["lines"]
                ],
                ["4.0.1", "4.0.1"],
            )
            snapshot["artifacts"][0].pop("latestStable")
            path.write_text(json.dumps(snapshot))
            shutil.rmtree(root / "site/.stage")
            self.assertNotIn("latestStable", self.build(root)[0]["releaseDesignations"])

    def test_states_and_destination_kinds_are_distinct(self):
        for state, behavior, kind in (
            ("hidden", None, "unavailable"),
            ("withdrawn", None, "unavailable"),
            ("tombstoned", "omit", "unavailable"),
            ("withdrawn", "notice", "notice"),
            ("tombstoned", "redirect", "redirect"),
            (None, None, "docs"),
        ):
            with (
                self.subTest(state=state, behavior=behavior),
                _workspace(with_content_file=True) as root,
            ):
                configure_release(root, state=state, behavior=behavior)
                row = self.build(root)[0]
                target = row["releaseDesignations"]["latestStable"]
                self.assertTrue(target["selected"])
                self.assertEqual(target["availability"]["kind"], kind)
                self.assertEqual(
                    target["action"], "omit" if kind == "unavailable" else kind
                )
                if state is None:
                    self.assertNotIn("publicationState", target)
                else:
                    self.assertEqual(target["publicationState"], state)
                if kind == "unavailable":
                    self.assertEqual(
                        target["availability"], {"kind": kind, "reason": state}
                    )
                else:
                    self.assertEqual(
                        target["availability"]["path"], "/spark/releases/4.0.0/"
                    )
                if kind == "redirect":
                    self.assertEqual(
                        target["availability"]["toUrl"],
                        "https://docs.example.org/spark/",
                    )
                view = consumer_view([row], {"slug": "spark", "publication": {}})
                self.assertEqual(bool(view["docsLinks"]), kind == "docs")
                self.assertEqual(
                    bool(
                        exact_docs_link(
                            root / "site/.stage",
                            slug="spark",
                            artifact="runtime",
                            version="4.0.0",
                        )
                    ),
                    kind == "docs",
                )

    def test_unselected_hidden_retains_state_without_action(self):
        with _workspace(with_content_file=True) as root:
            configure_release(root, state="hidden")
            pin(root, [])
            target = self.build(root)[0]["releaseDesignations"]["latestStable"]
            self.assertEqual(
                target,
                {
                    "version": "4.0.0",
                    "selected": False,
                    "publicationState": "hidden",
                    "availability": {"kind": "unavailable", "reason": "not-selected"},
                },
            )

    def test_optional_missing_empty_present_and_curated_facts(self):
        with _workspace(with_content_file=True) as root:
            configure_release(root, present=False, requirement="optional")
            self.assertEqual(
                self.build(root)[0]["releaseDesignations"],
                {"snapshotStatus": "missing", "lines": []},
            )
        with _workspace(with_content_file=True) as root:
            path, snapshot = configure_release(root)
            snapshot.update(artifacts=[], records=[])
            path.write_text(json.dumps(snapshot))
            self.assertEqual(
                self.build(root)[0]["releaseDesignations"],
                {"snapshotStatus": "present", "lines": []},
            )

    def test_missing_required_or_selected_docs_does_not_replace_stage(self):
        for failure in ("inventory", "docs"):
            with (
                self.subTest(failure=failure),
                _workspace(with_content_file=True) as root,
            ):
                path, _ = configure_release(root, requirement="required")
                self.build(root)
                before = (root / "site/.stage/data/artifacts.json").read_bytes()
                if failure == "inventory":
                    path.unlink()
                else:
                    shutil.rmtree(path.parent / "4.0.0")
                self.assertNotEqual(run(root)[0], 0)
                self.assertEqual(
                    (root / "site/.stage/data/artifacts.json").read_bytes(), before
                )

    def test_direct_caller_must_supply_bound_snapshot_status(self):
        with _workspace(with_content_file=True) as root:
            configure_release(root)
            loaded = load_workspace_inputs(root)
            with self.assertRaisesRegex(
                PlanningInputFailure, "explicit snapshot input status"
            ):
                evaluate_planning(
                    target=PlanningTarget.BUILD,
                    workspace_root=root,
                    catalog=loaded.catalog,
                    provider_snapshot=loaded.provider_snapshot,
                    component_documents=loaded.component_documents,
                )

    def test_ambiguity_blocks_selected_hidden_and_unselected_designations_once(self):
        for selected, state, different in (
            (False, "published", False),
            (False, "published", True),
            (True, "published", False),
            (True, "hidden", False),
        ):
            with (
                self.subTest(selected=selected, state=state, different=different),
                _workspace(with_content_file=True) as root,
            ):
                path, snapshot = configure_release(root, state=state)
                released = next(
                    record
                    for record in snapshot["records"]
                    if record["kind"] == "released"
                )
                snapshot["records"].append(
                    dict(
                        released,
                        externalId="duplicate",
                        publicationState="hidden" if different else state,
                    )
                )
                path.write_text(json.dumps(snapshot))
                pin(root, ["4.0.0"] if selected else [])
                result = planning(root)
                self.assertFalse(result.build_plan_result.bridge.ready)
                self.assertIsNone(result.build_plan_result.candidate)
                code, report, errors = run(root)
                self.assertNotEqual(code, 0, (report, errors))
                self.assertEqual(
                    [entry["code"] for entry in report["diagnostics"]].count(
                        "provider-context-ambiguous"
                    ),
                    1,
                )

    def test_unselected_state_conflict_and_unrelated_ambiguity(self):
        with _workspace(with_content_file=True) as root:
            path, snapshot = configure_release(root, state="published")
            snapshot["artifacts"][0]["releases"][0]["publicationState"] = "hidden"
            path.write_text(json.dumps(snapshot))
            pin(root, [])
            code, report, _ = run(root)
            self.assertNotEqual(code, 0)
            self.assertEqual(
                [entry["code"] for entry in report["diagnostics"]].count(
                    "release-publication-state-conflict"
                ),
                1,
            )
            snapshot["artifacts"][0]["releases"][0].pop("publicationState")
            released = next(
                record for record in snapshot["records"] if record["kind"] == "released"
            )
            snapshot["records"] += [
                dict(released, version="3.0.0", externalId=f"old-{i}") for i in range(2)
            ]
            path.write_text(json.dumps(snapshot))
            self.build(root)

    def test_shared_and_namespaced_artifacts_never_borrow_root_ownership(self):
        for policy, expected in (
            ({}, "/spark/releases/4.0.0/"),
            (
                {"artifactRouting": "namespaced"},
                "/spark/artifacts/runtime/releases/4.0.0/",
            ),
            (
                {"artifactRouting": "namespaced", "defaultArtifact": "runtime"},
                "/spark/releases/4.0.0/",
            ),
        ):
            with (
                self.subTest(policy=policy),
                _workspace(with_content_file=True, topology="two_artifacts") as root,
            ):
                configure_routes(root, **policy)
                (
                    root / "components/runtime/docs/runtime/releases/4.0.0/index.md"
                ).write_text("runtime root")
                rows = self.build(root)
                rows_by_key = {row["key"]: row for row in rows}
                runtime = rows_by_key["runtime"]["releaseDesignations"]["lines"][0][
                    "target"
                ]
                api = rows_by_key["api"]["releaseDesignations"]["lines"][0]["target"]
                self.assertEqual(runtime["availability"]["path"], expected)
                self.assertEqual(
                    api["availability"],
                    {"kind": "unavailable", "reason": "no-landing-page"},
                )
                component = {"slug": "spark", "publication": policy}
                self.assertEqual(
                    consumer_view(rows, component, explicit="runtime")["docsLinks"],
                    ["https://docs.example.org" + expected],
                )
                self.assertEqual(
                    consumer_view(rows, component, page_artifact="api")["docsLinks"], []
                )
                if "defaultArtifact" in policy:
                    self.assertEqual(
                        consumer_view(rows, component)["docsLinks"],
                        ["https://docs.example.org" + expected],
                    )
                else:
                    with self.assertRaises(ValueError):
                        consumer_view(rows, component)
                with self.assertRaises(ValueError):
                    consumer_view(
                        rows, component, explicit="absent", page_artifact="runtime"
                    )

    def test_root_locale_eligibility_uses_current_policy(self):
        for locale, kind in (
            (None, "docs"),
            ("en", "docs"),
            ("de", "unavailable"),
            ("nested", "unavailable"),
        ):
            with (
                self.subTest(locale=locale),
                _workspace(with_content_file=True) as root,
            ):
                configure_release(root)
                pin(root, ["4.0.0"])
                if locale:
                    catalog_path = root / "site/catalog.yaml"
                    catalog = yaml.safe_load(catalog_path.read_text())
                    catalog["components"][0]["localization"] = {
                        "defaultLocale": "en",
                        "supportedLocales": ["en", "de"],
                        "routeMode": "none",
                    }
                    catalog_path.write_text(yaml.safe_dump(catalog))
                    source = root / "components/runtime/docs/releases/4.0.0/index.md"
                    if locale != "en":
                        source.parent.joinpath(locale).mkdir()
                        source.rename(source.parent / locale / "index.md")
                target = self.build(root)[0]["releaseDesignations"]["latestStable"]
                self.assertEqual(target["availability"]["kind"], kind)
                if kind == "docs":
                    self.assertEqual(
                        target["availability"]["path"], "/spark/releases/4.0.0/"
                    )
                else:
                    self.assertEqual(
                        target["availability"],
                        {"kind": "unavailable", "reason": "no-landing-page"},
                    )

    def test_fresh_and_retained_stale_labels_cannot_attest_docs(self):
        mutations = {
            "originKey": "other",
            "version": "9.9.9",
            "pageKind": "withdrawal-notice",
            "locale": "de",
            "defaultLocale": True,
        }
        for retained in (False, True):
            for field, value in mutations.items():
                with (
                    self.subTest(retained=retained, field=field),
                    _workspace(with_content_file=True) as root,
                ):
                    configure_release(root)

                    def poison(spec, field=field, value=value):
                        result = execute_worker_spec(spec)
                        manifest_path = result.contribution_files.unit_manifest
                        if manifest_path:
                            data = json.loads(Path(manifest_path).read_text())
                            for page in data["pages"]:
                                if page.get("versionKind") == "released":
                                    page[field] = value
                            Path(manifest_path).write_text(json.dumps(data))
                        return result

                    if not retained:
                        with patch(
                            "buildish_site_pipeline.staging.coordinator.execute_worker_spec",
                            side_effect=poison,
                        ):
                            self.assertNotEqual(run(root)[0], 0)
                        self.assertFalse(
                            (root / "site/.stage/data/artifacts.json").exists()
                        )
                    else:
                        self.build(root)
                        plan = planning(root).build_plan_result.candidate
                        data = json.loads(
                            (
                                root
                                / "site/.stage/data/_pipeline/unit-contributions.json"
                            ).read_text()
                        )
                        for unit in data["units"]:
                            for page in unit["pages"]:
                                if page.get("versionKind") == "released":
                                    page[field] = value
                        manifests = PersistedUnitContributionsV1.model_validate(
                            data
                        ).units
                        claims = collect_destination_claims(
                            plan.site, plan.selected_versions, plan.snapshot_paths
                        )
                        with self.assertRaises(StageIntegrityError):
                            build_release_designations(
                                plan, manifests, claims, _build_redirect_entries(plan)
                            )

    def test_both_namespaced_artifacts_have_their_own_same_version_destination(self):
        with _workspace(with_content_file=True, topology="two_artifacts") as root:
            configure_routes(
                root, artifactRouting="namespaced", defaultArtifact="runtime"
            )
            (
                root / "components/runtime/docs/runtime/releases/4.0.0/index.md"
            ).write_text("runtime root")
            (root / "components/api/docs/releases/4.0.0/index.md").write_text(
                "api root"
            )
            rows = {row["key"]: row for row in self.build(root)}
            self.assertEqual(
                rows["runtime"]["releaseDesignations"]["lines"][0]["target"][
                    "availability"
                ]["path"],
                "/spark/releases/4.0.0/",
            )
            self.assertEqual(
                rows["api"]["releaseDesignations"]["lines"][0]["target"][
                    "availability"
                ]["path"],
                "/spark/artifacts/api/releases/4.0.0/",
            )
            self.assertEqual(
                exact_docs_link(
                    root / "site/.stage", slug="spark", artifact="api", version="4.0.0"
                ),
                "https://docs.example.org/spark/artifacts/api/releases/4.0.0/",
            )
            self.assertIsNone(
                exact_docs_link(
                    root / "site/.stage",
                    slug="spark",
                    artifact="other",
                    version="4.0.0",
                )
            )

    def test_retained_default_locale_flag_cannot_override_changed_policy(self):
        with _workspace(with_content_file=True) as root:
            configure_release(root)
            catalog_path = root / "site/catalog.yaml"
            catalog = yaml.safe_load(catalog_path.read_text())
            catalog["components"][0]["localization"] = {
                "defaultLocale": "en",
                "supportedLocales": ["en", "de"],
                "routeMode": "none",
            }
            catalog_path.write_text(yaml.safe_dump(catalog))
            self.build(root)
            data = (
                root / "site/.stage/data/_pipeline/unit-contributions.json"
            ).read_text()
            manifests = PersistedUnitContributionsV1.model_validate_json(data).units
            catalog["components"][0]["localization"]["defaultLocale"] = "de"
            catalog_path.write_text(yaml.safe_dump(catalog))
            plan = planning(root).build_plan_result.candidate
            claims = collect_destination_claims(
                plan.site, plan.selected_versions, plan.snapshot_paths
            )
            with self.assertRaisesRegex(StageIntegrityError, "current owned context"):
                build_release_designations(
                    plan, manifests, claims, _build_redirect_entries(plan)
                )

    def test_target_union_rejects_contradictory_destinations(self):
        valid = {
            "version": "4.0.0",
            "selected": True,
            "action": "docs",
            "availability": {
                "kind": "docs",
                "path": "/spark/releases/4.0.0/",
                "url": "https://docs.example.org/spark/releases/4.0.0/",
            },
        }
        ReleaseDesignationTarget.model_validate(valid)
        for mutation in (
            {"selected": False},
            {"publicationState": "hidden"},
            {"action": "notice"},
            {"availability": {"kind": "unavailable", "reason": "not-selected"}},
            {"availability": {"kind": "docs", "path": "/spark/"}},
            {
                "availability": {
                    "kind": "unavailable",
                    "reason": "no-landing-page",
                    "url": "https://docs.example.org/",
                }
            },
        ):
            with self.subTest(mutation=mutation), self.assertRaises(ValidationError):
                ReleaseDesignationTarget.model_validate(valid | mutation)
