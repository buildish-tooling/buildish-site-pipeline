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

"""Artifact route policy and concrete publication ownership regressions."""

from dataclasses import replace
import json
from pathlib import Path
import unittest

import frontmatter
from pydantic import ValidationError
import yaml

from buildish_site_pipeline.commands.shared import load_workspace_inputs
from buildish_site_pipeline.evaluation import (
    EvaluationMode,
    EvaluationRequest,
    run_evaluation,
)
from buildish_site_pipeline.models.authored.site_catalog import SiteCatalogDocumentV1
from buildish_site_pipeline.models.enums import PlanningTarget, RecordKind
from buildish_site_pipeline.planning import evaluate_planning
from buildish_site_pipeline.staging.publication_paths import public_path_for_context
from buildish_site_pipeline.cli.errors import StageIntegrityError
from tests.staging.test_component_publication import run, configure_release
from tests.support.workspace import _workspace


def configure_routes(root, **policy):
    path = root / "site/catalog.yaml"
    catalog = yaml.safe_load(path.read_text())
    catalog["components"][0]["publication"].update(policy)
    path.write_text(yaml.safe_dump(catalog, sort_keys=False))
    return catalog


def planning(root):
    loaded = load_workspace_inputs(root)
    return evaluate_planning(
        target=PlanningTarget.BUILD,
        catalog=loaded.catalog,
        provider_snapshot=loaded.provider_snapshot,
        workspace_root=root,
        component_documents=loaded.component_documents,
        snapshot_inputs=loaded.snapshot_inputs,
    )


class ArtifactRouteTests(unittest.TestCase):
    def test_static_ancestor_file_cannot_block_a_mount_subtree(self):
        with _workspace(with_content_file=True) as root:
            catalog = configure_routes(root)
            catalog["site"]["assetsRoot"] = "site/assets"
            catalog["components"][0]["mounts"] = [
                {
                    "source": "generated/api",
                    "mountPath": "/site/api/reference/",
                    "kind": "api",
                    "trustClass": "passive",
                }
            ]
            (root / "site/catalog.yaml").write_text(yaml.safe_dump(catalog))
            assets = root / "site/assets"
            assets.mkdir()
            (assets / "api").write_text("file blocking reserved descendants")
            for command in ("check", "build"):
                code, report, errors = run(root, command)
                self.assertNotEqual(code, 0, (report, errors))
                self.assertIn("Destination conflict", str(report))

    def test_shared_mode_rejects_development_release_root_conflation_before_any_copy(
        self,
    ):
        from buildish_site_pipeline.models.enums import StageCommand
        from buildish_site_pipeline.staging.coordinator import run_build
        from buildish_site_pipeline.staging.types import BuildRequest, StageDestination

        with _workspace(with_content_file=True) as root:
            configure_routes(
                root,
                developmentPath="/spark/manual/releases/4.0.0/",
                docsPath="/spark/manual/",
            )
            (root / "components/runtime/docs/dev-only.md").write_text(
                "development page with disjoint filename"
            )
            for command in ("check", "build"):
                code, report, errors = run(root, command)
                self.assertNotEqual(code, 0, (report, errors))
                self.assertIn("development:spark:runtime", str(report))
                self.assertIn("released:spark:runtime:4.0.0", str(report))
            result = planning(root)
            loaded = load_workspace_inputs(root)
            candidate = root / "private-candidate"
            with self.assertRaisesRegex(StageIntegrityError, "Destination conflict"):
                run_build(
                    BuildRequest(
                        command=StageCommand.BUILD,
                        build_plan=result.build_plan_result.candidate,
                        diagnostics=(),
                        provider_snapshot=loaded.provider_snapshot,
                        destination=StageDestination(stage_root=candidate),
                    )
                )
            self.assertFalse(candidate.exists())

    def test_alias_and_redirect_reservations_cover_rendered_static_index_and_ancestor_file(
        self,
    ):
        for kind in ("aliases", "redirects"):
            for relative in ("old/index.html", "old"):
                with (
                    self.subTest(kind=kind, relative=relative),
                    _workspace(with_content_file=True) as root,
                ):
                    catalog = configure_routes(root)
                    catalog["site"]["assetsRoot"] = "site/assets"
                    publication = catalog["components"][0]["publication"]
                    publication[kind] = (
                        [{"path": "/site/old/"}]
                        if kind == "aliases"
                        else [{"fromPath": "/site/old/", "target": "component:spark"}]
                    )
                    (root / "site/catalog.yaml").write_text(yaml.safe_dump(catalog))
                    asset = root / "site/assets" / relative
                    asset.parent.mkdir(parents=True, exist_ok=True)
                    asset.write_text("static source occupying the reservation")
                    for command in ("check", "build"):
                        code, report, errors = run(root, command)
                        self.assertNotEqual(code, 0, (report, errors))
                        self.assertIn("Destination conflict", str(report))

    def test_namespaced_exports_recompute_original_source_links_from_owned_contexts(
        self,
    ):
        from unittest.mock import patch
        from buildish_site_pipeline.staging.worker_entrypoint import execute_worker_spec

        with _workspace(with_content_file=True, topology="two_artifacts") as root:
            configure_routes(root, artifactRouting="namespaced")
            snapshot_path = root / "site/provider-snapshot.json"
            snapshot = json.loads(snapshot_path.read_text())
            for record in snapshot["records"]:
                if record["kind"] == "released":
                    key = record["artifactKey"]
                    record["docsSource"] = {
                        "repository": f"https://forge.example/original-{key}",
                        "root": f"original/{key}",
                        "ref": "v4.0.0",
                    }
            snapshot_path.write_text(json.dumps(snapshot))

            def poison_worker_source(spec):
                result = execute_worker_spec(spec)
                path = result.contribution_files.unit_manifest
                if path is not None:
                    manifest = json.loads(Path(path).read_text())
                    for page in manifest["pages"]:
                        page["source"] = {
                            "key": "forged",
                            "path": "wrong.md",
                            "repository": "https://forge.example/wrong",
                            "viewRef": "wrong",
                        }
                    Path(path).write_text(json.dumps(manifest))
                return result

            with patch(
                "buildish_site_pipeline.staging.coordinator.execute_worker_spec",
                side_effect=poison_worker_source,
            ):
                code, report, errors = run(root)
            self.assertEqual(code, 0, (report, errors))
            for key, suffix in (("runtime", "guide"), ("api", "reference")):
                page = frontmatter.load(
                    root
                    / f"site/.stage/content/spark/artifacts/{key}/releases/4.0.0/{suffix}/index.md"
                )
                source = page["pipeline"]["page"]["source"]
                self.assertEqual(source["path"], f"original/{key}/{suffix}/index.md")
                self.assertEqual(
                    source["repository"], f"https://forge.example/original-{key}"
                )
                self.assertEqual(source["viewRef"], "v4.0.0")
                self.assertNotIn("editRef", source)

    def test_namespace_without_catalog_artifact_bindings_publishes_ordinary_component(
        self,
    ):
        with _workspace(with_content_file=True) as root:
            (root / "components/runtime/docs/index.md").write_text("development")
            catalog = configure_routes(root, artifactRouting="namespaced")
            del catalog["components"][0]["artifacts"]
            (root / "site/catalog.yaml").write_text(
                yaml.safe_dump(catalog, sort_keys=False)
            )
            code, report, errors = run(root)
            self.assertEqual(code, 0, (report, errors))
            stage = root / "site/.stage"
            self.assertTrue(
                (
                    stage / "content/spark/artifacts/runtime/development/index.md"
                ).is_file()
            )
            self.assertTrue(
                (
                    stage / "content/spark/artifacts/runtime/releases/4.0.0/index.md"
                ).is_file()
            )
            routes = json.loads((stage / "data/routes.json").read_text())["items"]
            self.assertNotIn("/spark/development/", [row["path"] for row in routes])
            self.assertNotIn(
                "/spark/artifacts/runtime/", [row["path"] for row in routes]
            )
            page = frontmatter.load(
                stage / "content/spark/artifacts/runtime/development/index.md"
            )["pipeline"]
            self.assertEqual(page["page"]["componentPath"], "/spark/")
            self.assertEqual(
                page["component"]["publication"]["artifactRouting"], "namespaced"
            )

    def test_same_named_pages_and_assets_have_independent_literal_destinations(self):
        for default in (None, "runtime"):
            with (
                self.subTest(default=default),
                _workspace(with_content_file=True, topology="two_artifacts") as root,
            ):
                configure_routes(
                    root, artifactRouting="namespaced", defaultArtifact=default
                )
                for owner, docs in (
                    ("runtime", root / "components/runtime/docs/runtime"),
                    ("api", root / "components/api/docs"),
                ):
                    for prefix in (Path(), Path("releases/4.0.0")):
                        page = docs / prefix / "guide/index.md"
                        page.parent.mkdir(parents=True, exist_ok=True)
                        page.write_text(owner + " guide")
                        (docs / prefix / "diagram.svg").write_text(owner + " diagram")
                code, report, errors = run(root)
                self.assertEqual(code, 0, (report, errors))
                stage = root / "site/.stage"
                for owner, base in (
                    ("runtime", "spark" if default else "spark/artifacts/runtime"),
                    ("api", "spark/artifacts/api"),
                ):
                    for context in ("development", "releases/4.0.0"):
                        page = frontmatter.load(
                            stage / "content" / base / context / "guide/index.md"
                        )
                        self.assertEqual(page.content, owner + " guide")
                        self.assertEqual(
                            page["pipeline"]["page"]["componentPath"], "/spark/"
                        )
                        self.assertEqual(
                            (
                                stage / "content" / base / context / "diagram.svg"
                            ).read_text(),
                            owner + " diagram",
                        )
                self.assertFalse(
                    (stage / "content/spark/artifacts/runtime").exists()
                    if default
                    else (stage / "content/spark/development").exists()
                )

    def test_all_context_kinds_and_custom_bases_preserve_route_relationships(self):
        cases = [
            (
                {},
                [
                    "/spark/artifacts/runtime/development/",
                    "/spark/artifacts/runtime/development/4.0/",
                    "/spark/artifacts/runtime/development/refs/preview/",
                    "/spark/artifacts/runtime/development/candidates/1.0/",
                    "/spark/artifacts/runtime/releases/1.0/",
                ],
            ),
            (
                {
                    "mountPath": "/group/spark/",
                    "docsPath": "/group/spark/development/docs/",
                },
                [
                    "/group/spark/artifacts/runtime/development/",
                    "/group/spark/artifacts/runtime/development/docs/4.0/",
                    "/group/spark/artifacts/runtime/development/docs/refs/preview/",
                    "/group/spark/artifacts/runtime/development/docs/candidates/1.0/",
                    "/group/spark/artifacts/runtime/development/docs/releases/1.0/",
                ],
            ),
            (
                {"developmentPath": "/nightly/spark/", "docsPath": "/manual/spark/"},
                [
                    "/nightly/spark/artifacts/runtime/",
                    "/manual/spark/artifacts/runtime/4.0/",
                    "/manual/spark/artifacts/runtime/refs/preview/",
                    "/manual/spark/artifacts/runtime/candidates/1.0/",
                    "/manual/spark/artifacts/runtime/releases/1.0/",
                ],
            ),
            (
                {"mountPath": "/"},
                [
                    "/artifacts/runtime/development/",
                    "/artifacts/runtime/development/4.0/",
                    "/artifacts/runtime/development/refs/preview/",
                    "/artifacts/runtime/development/candidates/1.0/",
                    "/artifacts/runtime/releases/1.0/",
                ],
            ),
            (
                {
                    "mountPath": "/spark/",
                    "developmentPath": "/sparks/dev/",
                    "docsPath": "/sparks/dev/",
                },
                [
                    "/sparks/dev/artifacts/runtime/",
                    "/sparks/dev/artifacts/runtime/4.0/",
                    "/sparks/dev/artifacts/runtime/refs/preview/",
                    "/sparks/dev/artifacts/runtime/candidates/1.0/",
                    "/spark/artifacts/runtime/releases/1.0/",
                ],
            ),
        ]
        for overrides, expected in cases:
            with (
                self.subTest(overrides=overrides),
                _workspace(with_content_file=True) as root,
            ):
                configure_routes(root, artifactRouting="namespaced", **overrides)
                result = planning(root)
                component = result.site.components[0]
                context = result.selected_versions.contexts[0]
                actual = [
                    public_path_for_context(
                        component.publication,
                        replace(
                            context,
                            kind=kind,
                            version="1.0",
                            release_line="4.0",
                            named_ref_key="preview",
                        ),
                    )
                    for kind in (
                        RecordKind.DEVELOPMENT,
                        RecordKind.LINE_HEAD,
                        RecordKind.NAMED_REF,
                        RecordKind.CANDIDATE,
                        RecordKind.RELEASED,
                    )
                ]
                self.assertEqual(actual, expected)
                self.assertEqual(
                    component.artifacts[0].publication.development_path, expected[0]
                )

    def test_default_does_not_promote_another_artifact_when_development_is_disabled(
        self,
    ):
        with _workspace(with_content_file=True, topology="two_artifacts") as root:
            catalog = configure_routes(
                root,
                artifactRouting="namespaced",
                defaultArtifact="runtime",
                docsPath="/spark/manual/",
            )
            catalog["components"][0]["artifacts"][0]["publicationSelection"][
                "development"
            ] = False
            (root / "site/catalog.yaml").write_text(
                yaml.safe_dump(catalog, sort_keys=False)
            )
            code, report, errors = run(root)
            self.assertEqual(code, 0, (report, errors))
            rows = json.loads((root / "site/.stage/data/routes.json").read_text())[
                "items"
            ]
            paths = [row["path"] for row in rows]
            self.assertNotIn("/spark/development/", paths)
            self.assertNotIn("/spark/manual/", paths)
            self.assertIn("/spark/artifacts/api/development/", paths)
            self.assertIn("/spark/manual/releases/4.0.0/", paths)
            self.assertIn("/spark/artifacts/api/manual/releases/4.0.0/", paths)

    def test_catalog_validates_mode_default_and_component_only_location(self):
        for policy in (
            {"defaultArtifact": "runtime"},
            {"artifactRouting": "shared", "defaultArtifact": "runtime"},
            {"artifactRouting": "invalid"},
        ):
            with self.subTest(policy=policy), _workspace() as root:
                catalog = configure_routes(root, **policy)
                with self.assertRaises(ValidationError):
                    SiteCatalogDocumentV1.model_validate(catalog)
        with _workspace() as root:
            catalog = configure_routes(root, artifactRouting="namespaced")
            catalog["groups"] = {
                "g": {"publication": {"artifactRouting": "namespaced"}}
            }
            with self.assertRaises(ValidationError):
                SiteCatalogDocumentV1.model_validate(catalog)
        with _workspace() as root:
            configure_routes(
                root, artifactRouting="namespaced", defaultArtifact="unknown"
            )
            code, report, _ = run(root, "check")
            self.assertNotEqual(code, 0)
            self.assertIn("unknown", str(report))

    def test_artifactless_namespaced_component_preserves_development(self):
        with _workspace(
            with_content_file=True, topology="component_only_development"
        ) as root:
            configure_routes(root, artifactRouting="namespaced")
            code, report, errors = run(root)
            self.assertEqual(code, 0, (report, errors))
            self.assertTrue(
                (
                    root
                    / "site/.stage/content/components/site-pipeline/development/index.md"
                ).is_file()
            )

    def test_namespaced_withdrawal_keeps_notice_or_redirect_without_original_assets(
        self,
    ):
        for behavior in ("notice", "redirect"):
            with (
                self.subTest(behavior=behavior),
                _workspace(with_content_file=True) as root,
            ):
                configure_release(root, state="withdrawn", behavior=behavior)
                configure_routes(root, artifactRouting="namespaced")
                code, report, errors = run(root)
                self.assertEqual(code, 0, (report, errors))
                stage = root / "site/.stage"
                release = stage / "content/spark/artifacts/runtime/releases/4.0.0"
                if behavior == "notice":
                    page = frontmatter.load(release / "index.md")
                    self.assertNotIn("docsPath", page["pipeline"]["page"]["version"])
                else:
                    self.assertFalse(release.exists())
                    redirects = json.loads((stage / "data/redirects.json").read_text())[
                        "items"
                    ]
                    self.assertIn(
                        "https://docs.example.org/spark/artifacts/runtime/releases/4.0.0/",
                        [row["fromUrl"] for row in redirects],
                    )
                self.assertFalse(
                    (stage / "static/spark/artifacts/runtime/releases/4.0.0").exists()
                )

    def test_duplicate_shared_claims_fail_check_and_build_even_with_identical_bytes(
        self,
    ):
        for relative in ("guide/index.md", "guide.md", "Guide/index.md", "diagram.svg"):
            with (
                self.subTest(relative=relative),
                _workspace(with_content_file=True, topology="two_artifacts") as root,
            ):
                if relative == "diagram.svg":
                    (root / "components/runtime/docs/runtime/diagram.svg").write_text(
                        "same"
                    )
                target = root / "components/api/docs" / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("same")
                for command in ("check", "build"):
                    code, report, errors = run(root, command)
                    self.assertNotEqual(code, 0, (report, errors))
                    self.assertIn("Destination conflict", str(report))
                    self.assertIn("runtime", str(report))
                    self.assertIn("api", str(report))
                self.assertFalse((root / "site/.stage/manifest.json").exists())

    def test_component_assets_and_contextual_pretty_pages_cannot_share_rendered_output(
        self,
    ):
        with _workspace(with_content_file=True) as root:
            catalog = configure_routes(root, assetsPath="/spark/development/guide/")
            catalog["components"][0]["artifacts"][0]["assetsRoot"] = "context-assets"
            metadata = root / "components/runtime/site/component.yaml"
            authored = yaml.safe_load(metadata.read_text())
            authored.setdefault("content", {})["assetsRoot"] = "component-assets"
            metadata.write_text(yaml.safe_dump(authored))
            (root / "site/catalog.yaml").write_text(yaml.safe_dump(catalog))
            (root / "components/runtime/docs/guide.md").write_text("guide page")
            assets = root / "components/runtime/component-assets"
            assets.mkdir()
            (assets / "index.html").write_text("static page")
            (root / "components/runtime/context-assets").mkdir()
            code, report, _ = run(root, "check")
            self.assertNotEqual(code, 0)
            self.assertIn("Destination conflict", str(report))

    def test_mount_reservations_are_literal_subtrees_independent_of_context_selection(
        self,
    ):
        for artifact_mount in (False, True):
            with (
                self.subTest(artifact_mount=artifact_mount),
                _workspace(with_content_file=True) as root,
            ):
                catalog = configure_routes(root, artifactRouting="namespaced")
                owner = (
                    catalog["components"][0]["artifacts"][0]
                    if artifact_mount
                    else catalog["components"][0]
                )
                owner["mounts"] = [
                    {
                        "source": "generated/api",
                        "mountPath": "/spark/artifacts/runtime/development/",
                        "kind": "generatedApi",
                        "trustClass": "passive",
                    }
                ]
                (root / "site/catalog.yaml").write_text(yaml.safe_dump(catalog))
                code, report, _ = run(root, "check")
                self.assertNotEqual(code, 0)
                self.assertIn("Destination conflict", str(report))

    def test_worker_guard_still_rejects_same_unit_duplicates_if_evaluation_guard_is_bypassed(
        self,
    ):
        from tests.support.staging import _build_request
        from buildish_site_pipeline.staging.workdirs import (
            RunWorkspace,
            create_work_root_layout,
        )
        from buildish_site_pipeline.staging.ownership import build_owned_units
        from buildish_site_pipeline.staging.spec_builder import (
            build_worker_spec_for_unit,
        )
        from buildish_site_pipeline.staging.units.component import run_component_unit

        with _workspace(with_content_file=True, topology="two_artifacts") as root:
            request = _build_request(root, pool_size=1)
            units = build_owned_units(request.build_plan)
            layout = create_work_root_layout(next_stage_root=root / "candidate")
            spec = build_worker_spec_for_unit(
                unit=units[0],
                workspace_root=root,
                site_components=request.build_plan.site.components,
                run_workspace=RunWorkspace(root, layout),
            )
            target = root / "components/api/docs/guide/index.md"
            target.parent.mkdir(parents=True)
            target.write_text("conflict after planning")
            with self.assertRaisesRegex(StageIntegrityError, "Destination conflict"):
                run_component_unit(spec)
            self.assertFalse(
                (root / "candidate/content/spark/development/guide/index.md").exists()
            )

    def test_phantom_default_family_cannot_satisfy_redirect_reference(self):
        with _workspace(with_content_file=True) as root:
            catalog = configure_routes(
                root,
                artifactRouting="namespaced",
                defaultArtifact="runtime",
                docsPath="/spark/manual/",
            )
            catalog["components"][0]["publication"]["redirects"] = [
                {"fromPath": "/old/", "target": "route:/spark/manual/"}
            ]
            (root / "site/catalog.yaml").write_text(yaml.safe_dump(catalog))
            result = planning(root)
            evaluated = run_evaluation(
                request=EvaluationRequest(mode=EvaluationMode.CHECK), planning=result
            )
            self.assertIsNone(evaluated.build_plan)
            self.assertIn(
                "redirect-target-unknown", [d.code for d in evaluated.diagnostics]
            )
