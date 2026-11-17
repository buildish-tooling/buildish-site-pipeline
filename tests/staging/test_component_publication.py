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

"""End-to-end release availability and publication-state regressions."""

import io
import json
import shutil
import unittest
import yaml
import frontmatter

from buildish_site_pipeline.cli import _run
from tests.commands.test_component_snapshots import configure_snapshot
from tests.support.workspace import _workspace, _cwd


def run(root, command="build", *options):
    output, errors = io.StringIO(), io.StringIO()
    with _cwd(root):
        code = _run(
            argv=[
                command,
                "--report-format",
                "json",
                "--report-schema-version",
                "1",
                *options,
            ],
            stdout=output,
            stderr=errors,
        )
    return (
        code,
        json.loads(output.getvalue()) if output.getvalue() else {},
        errors.getvalue(),
    )


def configure_release(
    root, *, state=None, behavior=None, requirement="publication", present=True
):
    path, snapshot = configure_snapshot(root, requirement)
    if state:
        snapshot["records"][0]["publicationState"] = state
    artifact = snapshot["artifacts"][0]
    artifact["latestStable"] = "4.0.0"
    if behavior:
        release = artifact["releases"][0]
        release.update(
            publicationState=state,
            withdrawalBehavior=behavior,
            reason="Recalled release",
        )
        if behavior == "redirect":
            release["redirectTarget"] = "component:spark"
    if present:
        path.write_text(json.dumps(snapshot))
    return path, snapshot


def configure_inherited_selection(root):
    path, snapshot = configure_release(root)
    # Retain the authored 4.0 line while publishing exact release 1.0.
    snapshot = json.loads(json.dumps(snapshot).replace("4.0.0", "1.0"))
    path.write_text(json.dumps(snapshot))
    docs = root / "components/runtime/docs"
    (docs / "releases/4.0.0").rename(docs / "releases/1.0")
    (docs / "index.md").write_text("development body\n")
    (docs / "maintenance/4.0/index.md").write_text("line head body\n")
    catalog_path = root / "site/catalog.yaml"
    catalog = yaml.safe_load(catalog_path.read_text())
    component = catalog["components"][0]
    component["publicationSelection"] = {
        "development": True, "lineHeads": {"mode": "allAuthored"},
        "releases": {"mode": "explicit", "versions": ["1.0"]},
    }
    component["artifacts"][0]["publicationSelection"] = {"namedRefs": []}
    catalog_path.write_text(yaml.safe_dump(catalog, sort_keys=False))
    return path, snapshot


class ComponentPublicationTests(unittest.TestCase):
    def test_partial_artifact_stages_inherited_contexts_without_changing_latest_facts(self):
        from buildish_site_pipeline.commands.shared import load_workspace_inputs
        from buildish_site_pipeline.models.enums import PlanningTarget
        from buildish_site_pipeline.planning import evaluate_planning

        with _workspace(with_content_file=True) as root:
            snapshot_path, snapshot = configure_inherited_selection(root)
            # The handoff case explicitly excludes line heads.
            catalog_path = root / "site/catalog.yaml"
            catalog = yaml.safe_load(catalog_path.read_text())
            catalog["components"][0]["publicationSelection"]["lineHeads"] = {"mode": "none"}
            catalog_path.write_text(yaml.safe_dump(catalog, sort_keys=False))
            loaded = load_workspace_inputs(root)
            result = evaluate_planning(
                target=PlanningTarget.BUILD, workspace_root=root, catalog=loaded.catalog,
                provider_snapshot=loaded.provider_snapshot, component_documents=loaded.component_documents,
                snapshot_inputs=loaded.snapshot_inputs,
            )
            expected = [("development", None), ("released", "1.0")]
            self.assertEqual([(c.kind.value, c.version) for c in result.selected_versions.contexts], expected)
            self.assertEqual([(c.kind.value, c.version) for c in result.desired_versions], expected)
            self.assertTrue(result.build_plan_result.bridge.ready)
            self.assertEqual(
                {item.expected_local_path.relative_to(root).as_posix() for item in result.local_inputs},
                {"components/runtime/docs", "components/runtime/docs/releases/1.0"},
            )
            code, report, errors = run(root)
            self.assertEqual(code, 0, (report, errors))
            stage = root / "site/.stage"
            self.assertEqual(frontmatter.load(stage / "content/spark/development/index.md").content, "development body")
            self.assertEqual(frontmatter.load(stage / "content/spark/releases/1.0/index.md").content, "hello")
            self.assertFalse((stage / "content/spark/development/4.0").exists())
            self.assertFalse((stage / "content/spark/candidates").exists())
            self.assertFalse((stage / "content/spark/refs").exists())
            artifact = result.site.components[0].artifacts[0]
            self.assertEqual(artifact.lifecycle.latest_stable, "1.0")
            self.assertEqual(artifact.lifecycle.release_lines[0].latest, "1.0")
            self.assertEqual(json.loads(snapshot_path.read_text()), snapshot)

    def test_inherited_exact_release_with_missing_inventory_preserves_requirement_rules(self):
        for requirement, expected_code in (("optional", 0), ("required", 1)):
            with self.subTest(requirement=requirement), _workspace(with_content_file=True) as root:
                configure_snapshot(root, requirement)
                catalog_path = root / "site/catalog.yaml"
                catalog = yaml.safe_load(catalog_path.read_text())
                component = catalog["components"][0]
                component["publicationSelection"] = {
                    "releases": {"mode": "explicit", "versions": ["1.0"]},
                    "lineHeads": {"mode": "explicit", "keys": ["missing"]},
                }
                component["artifacts"][0]["publicationSelection"] = {"namedRefs": []}
                catalog_path.write_text(yaml.safe_dump(catalog, sort_keys=False))
                code, report, errors = run(root, "check")
                self.assertEqual(code, expected_code, (report, errors))
                codes = [d["code"] for d in report["diagnostics"]]
                if requirement == "optional":
                    self.assertNotIn("reference-configuration-invalid", codes)
                self.assertIn("provider-snapshot-missing" if requirement == "optional" else "provider-snapshot-required", codes)


    def test_exported_docs_use_explicit_original_source_or_omit_links(self):
        with _workspace(with_content_file=True) as root:
            path, snapshot = configure_release(root)
            snapshot = json.loads(json.dumps(snapshot).replace('4.0.0', '0.1.3'))
            path.write_text(json.dumps(snapshot))
            physical = root / "components/runtime/docs/releases/0.1.3"
            (root / "components/runtime/docs/releases/4.0.0").rename(physical)
            (physical / "index.md").rename(physical / "_index.md")
            (physical / "guide").mkdir()
            (physical / "guide/setup.md").write_text("# Setup\n")
            (root / "components/runtime/docs/intro.md").write_text("# Intro\n")

            code, report, errors = run(root)
            self.assertEqual(code, 0, (report, errors))
            stage = root / "site/.stage"
            released = stage / "content/spark/releases/0.1.3/_index.md"
            self.assertNotIn("source", frontmatter.load(released)["pipeline"]["page"])
            before = {
                name: json.loads((stage / f"data/{name}.json").read_text())
                for name in ("routes", "artifacts", "releases")
            }

            snapshot["records"][0]["docsSource"] = {
                "repository": "https://github.com/example/original",
                "root": "docs",
                "ref": "b4542a195705c13c3806ca34fed8e821bedc20c8",
            }
            path.write_text(json.dumps(snapshot))
            shutil.rmtree(stage)
            code, report, errors = run(root)
            self.assertEqual(code, 0, (report, errors))
            expected = {
                "key": "runtime",
                "path": "docs/_index.md",
                "repository": "https://github.com/example/original",
                "viewRef": "b4542a195705c13c3806ca34fed8e821bedc20c8",
            }
            self.assertEqual(frontmatter.load(released)["pipeline"]["page"]["source"], expected)
            nested = stage / "content/spark/releases/0.1.3/guide/setup.md"
            self.assertEqual(
                frontmatter.load(nested)["pipeline"]["page"]["source"],
                dict(expected, path="docs/guide/setup.md"),
            )
            index = json.loads((stage / "data/content-index.json").read_text())["items"]
            self.assertIn(expected, [entry.get("source") for entry in index])
            development = stage / "content/spark/development/intro.md"
            self.assertEqual(
                frontmatter.load(development)["pipeline"]["page"]["source"],
                {
                    "key": "runtime", "path": "docs/intro.md",
                    "repository": "https://github.com/example/runtime",
                    "viewRef": "main", "editRef": "main",
                },
            )
            for name, value in before.items():
                self.assertEqual(json.loads((stage / f"data/{name}.json").read_text()), value)

    def test_local_absence_omits_release_but_keeps_development_and_reports(self):
        with _workspace(with_content_file=True) as root:
            configure_release(root, present=False)
            shutil.rmtree(root / "components/runtime/docs/releases")
            for command in ("plan", "check", "build"):
                with self.subTest(command=command):
                    code, report, errors = run(
                        root,
                        command,
                        *(["--fail-on", "warning"] if command == "check" else []),
                    )
                    self.assertEqual(code, 0, (report, errors))
                    self.assertEqual(report["contextDispositions"], [])
                    self.assertIn(
                        "provider-snapshot-missing",
                        [item["code"] for item in report["diagnostics"]],
                    )
            stage = root / "site/.stage"
            self.assertFalse((stage / "content/spark/releases/4.0.0").exists())
            self.assertTrue((stage / "data/diagnostics.json").is_file())
            artifacts = json.loads((stage / "data/artifacts.json").read_text())["items"]
            self.assertNotIn("latestStable", artifacts[0])
            code, report, errors = run(root, "check", "--profile", "publication")
            self.assertEqual(code, 1, (report, errors))
            self.assertIn(
                "provider-snapshot-required",
                [item["code"] for item in report["diagnostics"]],
            )
            self.assertEqual(run(root, "plan", "--profile", "publication")[0], 0)

    def test_snapshot_requirement_and_profile_matrix(self):
        for requirement in ("publication", "required", "optional"):
            for profile in ("local", "publication"):
                with (
                    self.subTest(requirement=requirement, profile=profile),
                    _workspace(with_content_file=True) as root,
                ):
                    configure_release(root, present=False, requirement=requirement)
                    shutil.rmtree(root / "components/runtime/docs/releases")
                    required = requirement == "required" or (
                        requirement == "publication" and profile == "publication"
                    )
                    code, report, errors = run(root, "check", "--profile", profile)
                    self.assertEqual(code, int(required), (report, errors))

    def test_present_inventory_missing_original_docs_fails(self):
        with _workspace(with_content_file=True) as root:
            configure_release(root)
            shutil.rmtree(root / "components/runtime/docs/releases/4.0.0")
            code, report, errors = run(root)
            self.assertEqual(code, 1, (report, errors))
            self.assertIn(
                "input-missing", [item["code"] for item in report["diagnostics"]]
            )

    def test_withdrawal_actions_do_not_require_or_publish_original_docs(self):
        for state, behavior, action in (
            ("hidden", None, "omit"),
            ("withdrawn", None, "omit"),
            ("withdrawn", "omit", "omit"),
            ("withdrawn", "notice", "notice"),
            ("tombstoned", "redirect", "redirect"),
        ):
            with (
                self.subTest(state=state, behavior=behavior),
                _workspace(with_content_file=True) as root,
            ):
                configure_release(root, state=state, behavior=behavior)
                shutil.rmtree(root / "components/runtime/docs/releases/4.0.0")
                code, report, errors = run(root)
                self.assertEqual(code, 0, (report, errors))
                self.assertEqual(report["contextDispositions"][0]["action"], action)
                stage = root / "site/.stage"
                notice = stage / "content/spark/releases/4.0.0/index.md"
                self.assertEqual(notice.is_file(), action == "notice")
                if action == "notice":
                    self.assertIn("Recalled release", notice.read_text())
                    self.assertNotIn("docsUrl:", notice.read_text())
                releases = json.loads((stage / "data/releases.json").read_text())[
                    "items"
                ]
                self.assertEqual(releases[0]["publicationState"], state)
                if action == "redirect":
                    redirects = json.loads((stage / "data/redirects.json").read_text())[
                        "items"
                    ]
                    self.assertEqual(redirects[0]["sourceKind"], "withdrawal")

    def test_withdrawn_original_content_and_assets_are_excluded(self):
        with _workspace(with_content_file=True) as root:
            configure_release(root, state="withdrawn", behavior="notice")
            original = root / "components/runtime/docs/releases/4.0.0"
            (original / "secret-old-page.md").write_text("ORIGINAL CONTENT")
            (original / "asset.bin").write_bytes(b"original asset")
            code, report, errors = run(root)
            self.assertEqual(code, 0, (report, errors))
            stage = root / "site/.stage"
            self.assertFalse(list(stage.rglob("secret-old-page.md")))
            self.assertFalse(list(stage.rglob("asset.bin")))

    def test_authored_state_fallback_conflict_and_providerless_staging(self):
        for provider_state in (None, "published"):
            with (
                self.subTest(provider_state=provider_state),
                _workspace(with_content_file=True) as root,
            ):
                path, snapshot = configure_release(
                    root, state="withdrawn", behavior="omit"
                )
                snapshot["records"][0].pop("publicationState")
                if provider_state:
                    snapshot["records"][0]["publicationState"] = provider_state
                path.write_text(json.dumps(snapshot))
                code, report, errors = run(root)
                self.assertEqual(
                    code, int(provider_state is not None), (report, errors)
                )
                if provider_state:
                    self.assertIn(
                        "release-publication-state-conflict",
                        [item["code"] for item in report["diagnostics"]],
                    )
        with _workspace(with_content_file=True) as root:
            path, snapshot = configure_release(root)
            snapshot["records"] = []
            snapshot["providers"] = []
            path.write_text(json.dumps(snapshot))
            code, report, errors = run(root)
            self.assertEqual(code, 0, (report, errors))
            self.assertEqual(report["contextDispositions"][0]["action"], "docs")
            releases = json.loads(
                (root / "site/.stage/data/releases.json").read_text()
            )["items"]
            self.assertIsNone(releases[0].get("provider"))

    def test_development_excludes_nested_selected_and_unselected_materializations(self):
        with _workspace(with_content_file=True) as root:
            path, _ = configure_release(root)
            (path.parent / ".git").write_text("gitdir: /outside/worktree")
            extra = path.parent / "9.9.9"
            extra.mkdir()
            (extra / "index.md").write_text("unselected historical content")
            code, report, errors = run(root)
            self.assertEqual(code, 0, (report, errors))
            stage = root / "site/.stage"
            self.assertFalse((stage / "content/spark/development/releases").exists())
            self.assertFalse(list(stage.rglob(".git")))
            self.assertFalse(list(stage.rglob("provider-snapshot.json")))
            self.assertFalse(list(stage.rglob("9.9.9")))
            self.assertTrue((stage / "content/spark/releases/4.0.0/index.md").exists())

    def test_component_snapshot_can_be_only_provider_inventory(self):
        for present in (True, False):
            with (
                self.subTest(present=present),
                _workspace(with_content_file=True) as root,
            ):
                configure_release(root, present=present)
                (root / "site/provider-snapshot.json").unlink()
                if not present:
                    shutil.rmtree(root / "components/runtime/docs/releases")
                code, report, errors = run(root)
                self.assertEqual(code, 0, (report, errors))

    def test_unknown_explicit_identity_deferred_only_for_absent_inventory(self):
        with _workspace(with_content_file=True) as root:
            path, snapshot = configure_release(root, present=False)
            catalog_path = root / "site/catalog.yaml"
            catalog = yaml.safe_load(catalog_path.read_text())
            artifact = catalog["components"][0]["artifacts"][0]
            artifact["publicationSelection"]["releases"] = {
                "mode": "explicit",
                "versions": ["9.9.9"],
            }
            catalog_path.write_text(yaml.safe_dump(catalog, sort_keys=False))
            code, report, errors = run(root, "check", "--fail-on", "warning")
            self.assertEqual(code, 0, (report, errors))
            self.assertIn(
                "release-identity-unverified",
                [item["code"] for item in report["diagnostics"]],
            )
            path.write_text(json.dumps(snapshot))
            code, report, errors = run(root, "check")
            self.assertEqual(code, 1, (report, errors))
            self.assertIn(
                "reference-configuration-invalid",
                [item["code"] for item in report["diagnostics"]],
            )

    def test_links_to_withdrawal_and_local_omission_roots_obey_strict_check(self):
        for mode in ("directory", "file-html"):
            for behavior in ("notice", "redirect", "absent"):
                with (
                    self.subTest(mode=mode, behavior=behavior),
                    _workspace(with_content_file=True) as root,
                ):
                    configure_release(
                        root,
                        state="withdrawn" if behavior != "absent" else None,
                        behavior=behavior if behavior != "absent" else None,
                        present=behavior != "absent",
                    )
                    if behavior == "absent":
                        shutil.rmtree(root / "components/runtime/docs/releases")
                    catalog_path = root / "site/catalog.yaml"
                    catalog = yaml.safe_load(catalog_path.read_text())
                    if behavior == "absent":
                        catalog["components"][0]["artifacts"][0][
                            "publicationSelection"
                        ]["releases"] = {"mode": "explicit", "versions": ["4.0.0"]}
                    catalog["validation"] = {
                        "linkChecks": {
                            "enabled": True,
                            "mode": mode,
                            "checkRootAbsolute": True,
                            "internalPrefixes": ["/spark/"],
                        }
                    }
                    catalog_path.write_text(yaml.safe_dump(catalog, sort_keys=False))
                    suffix = "index.html" if mode == "file-html" else ""
                    (root / "components/runtime/docs/index.md").write_text(
                        f"[Release](/spark/releases/4.0.0/{suffix})"
                    )
                    code, report, errors = run(root, "check", "--fail-on", "warning")
                    self.assertEqual(code, 0, (report, errors))

    def test_provider_file_inside_authored_tree_is_not_published(self):
        for location in ("docs/provider.json", "pages/provider.json"):
            with (
                self.subTest(location=location),
                _workspace(with_content_file=True) as root,
            ):
                path, snapshot = configure_snapshot(root, path=location)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(snapshot))
                catalog_path = root / "site/catalog.yaml"
                catalog = yaml.safe_load(catalog_path.read_text())
                catalog["defaults"]["pagesRoot"] = "pages"
                catalog_path.write_text(yaml.safe_dump(catalog, sort_keys=False))
                (root / "components/runtime/pages").mkdir(exist_ok=True)
                code, report, errors = run(root)
                self.assertEqual(code, 0, (report, errors))
                self.assertFalse(list((root / "site/.stage").rglob("provider.json")))

    def test_ordinary_maintenance_pages_remain_in_development(self):
        with _workspace(with_content_file=True) as root:
            configure_release(root)
            authored = root / "components/runtime/docs/maintenance/todos.md"
            authored.write_text("ordinary maintenance instructions")
            code, report, errors = run(root)
            self.assertEqual(code, 0, (report, errors))
            stage = root / "site/.stage"
            self.assertTrue(
                (stage / "content/spark/development/maintenance/todos.md").is_file()
            )
            self.assertFalse(
                (stage / "content/spark/development/maintenance/4.0").exists()
            )

    def test_provider_alias_and_target_are_both_excluded(self):
        with _workspace(with_content_file=True) as root:
            path, snapshot = configure_snapshot(root, path="docs/provider.json")
            target = path.parent / "inventory.json"
            target.write_text(json.dumps(snapshot))
            path.symlink_to(target.name)
            code, report, errors = run(root)
            self.assertEqual(code, 0, (report, errors))
            stage = root / "site/.stage"
            self.assertFalse(list(stage.rglob("provider.json")))
            self.assertFalse(list(stage.rglob("inventory.json")))

    def test_aggregate_candidate_cannot_fill_missing_component_snapshot(
        self,
    ):
        with _workspace(with_content_file=True) as root:
            configure_release(root, present=False)
            shutil.rmtree(root / "components/runtime/docs/releases")
            aggregate_path = root / "site/provider-snapshot.json"
            aggregate = json.loads(aggregate_path.read_text())
            aggregate["records"].append(
                {
                    "provider": "github",
                    "kind": "candidate",
                    "componentSlug": "spark",
                    "artifactKey": "runtime",
                    "version": "4.0.0",
                    "candidateSequence": 1,
                }
            )
            aggregate_path.write_text(json.dumps(aggregate))
            catalog_path = root / "site/catalog.yaml"
            catalog = yaml.safe_load(catalog_path.read_text())
            catalog["components"][0]["artifacts"][0]["publicationSelection"][
                "candidates"
            ] = {"mode": "explicit", "versions": ["4.0.0"]}
            catalog["validation"] = {
                "linkChecks": {
                    "enabled": True,
                    "checkRootAbsolute": True,
                    "internalPrefixes": ["/spark/"],
                }
            }
            catalog_path.write_text(yaml.safe_dump(catalog, sort_keys=False))
            candidate = root / "components/runtime/docs/candidates/4.0.0"
            candidate.mkdir(parents=True)
            (candidate / "index.md").write_text(
                "[Missing](/spark/development/candidates/4.0.0/missing/)"
            )
            code, report, errors = run(root, "check", "--fail-on", "warning")
            self.assertEqual(code, 1, (report, errors))
            self.assertEqual(report["kind"], "cliFailure")
            self.assertIn("must not claim this component", report["error"]["message"])
