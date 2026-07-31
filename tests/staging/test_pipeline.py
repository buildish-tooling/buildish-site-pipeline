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

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import frontmatter

from buildish_site_pipeline.cli.errors import StageIntegrityError
from buildish_site_pipeline.cli import _run
from buildish_site_pipeline.commands.shared import load_workspace_inputs
from buildish_site_pipeline.models.enums import PlanningTarget
from buildish_site_pipeline.planning import evaluate_planning
from buildish_site_pipeline.staging.aggregates import _build_redirect_entries
from buildish_site_pipeline.staging.file_writes import write_utf8_text_file
from buildish_site_pipeline.staging.ownership import OwnedUnit, OwnedUnitKind, _validate_output_ownership, build_owned_units
from tests.support.staging import _expand_workspace_for_multiple_owned_units
from tests.support.workspace import _cwd, _workspace


def _replace_file_text_once(path: Path, old_text: str, new_text: str) -> None:
    contents = path.read_text(encoding="utf-8")
    if old_text not in contents:
        raise AssertionError(f"Expected snippet not found in {path}: {old_text}")
    path.write_text(contents.replace(old_text, new_text, 1), encoding="utf-8")


class StagingPipelineTests(unittest.TestCase):
    def test_build_owned_units_group_contexts_under_component_owner(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            loaded_inputs = load_workspace_inputs(workspace_root)
            planning = evaluate_planning(
                target=PlanningTarget.BUILD,
                catalog=loaded_inputs.catalog,
                provider_snapshot=loaded_inputs.provider_snapshot,
                workspace_root=workspace_root,
                component_documents=loaded_inputs.component_documents,
                stage_root=workspace_root / "site/.stage",
                work_root=workspace_root / ".buildish/work",
            )

        self.assertIsNotNone(planning.build_plan_result.candidate)
        units = build_owned_units(planning.build_plan_result.candidate)
        self.assertEqual([unit.kind for unit in units], [OwnedUnitKind.COMPONENT])
        component_unit = units[0]
        self.assertEqual(component_unit.owner_id, "component:spark")
        self.assertEqual(component_unit.component_slug, "spark")
        self.assertEqual([context.context.kind.value for context in component_unit.contexts], ["development", "lineHead", "released"])
        self.assertEqual(
            [root.as_posix() for root in component_unit.content_stage_roots],
            [
                "content/spark",
                "content/spark/development",
                "content/spark/development/4.0",
                "content/spark/releases/4.0.0",
            ],
        )
        self.assertEqual(
            [root.as_posix() for root in component_unit.static_stage_roots],
            [
                "static/spark/assets",
                "static/spark/development",
                "static/spark/development/4.0",
                "static/spark/releases/4.0.0",
            ],
        )
        self.assertEqual(
            [context.content_stage_root.as_posix() for context in component_unit.contexts],
            [
                "content/spark/development",
                "content/spark/development/4.0",
                "content/spark/releases/4.0.0",
            ],
        )

    def test_build_owned_units_use_publication_paths_for_component_roots(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            _replace_file_text_once(
                workspace_root / "site/catalog.yaml",
                "    publication:\n      mountPath: /spark/\n",
                "    publication:\n      mountPath: /products/spark/\n",
            )
            loaded_inputs = load_workspace_inputs(workspace_root)
            planning = evaluate_planning(
                target=PlanningTarget.BUILD,
                catalog=loaded_inputs.catalog,
                provider_snapshot=loaded_inputs.provider_snapshot,
                workspace_root=workspace_root,
                component_documents=loaded_inputs.component_documents,
                stage_root=workspace_root / "site/.stage",
                work_root=workspace_root / ".buildish/work",
            )

        self.assertIsNotNone(planning.build_plan_result.candidate)
        units = build_owned_units(planning.build_plan_result.candidate)
        component_unit = units[0]
        self.assertEqual(
            [root.as_posix() for root in component_unit.content_stage_roots],
            [
                "content/products/spark",
                "content/products/spark/development",
                "content/products/spark/development/4.0",
                "content/products/spark/releases/4.0.0",
            ],
        )
        self.assertEqual(
            [root.as_posix() for root in component_unit.static_stage_roots],
            [
                "static/products/spark/assets",
                "static/products/spark/development",
                "static/products/spark/development/4.0",
                "static/products/spark/releases/4.0.0",
            ],
        )

    def test_build_manifest_references_written_aggregate_files(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(argv=["build", "--report-format", "json", "--report-schema-version", "1"], stdout=stdout, stderr=stderr)
            stage_root = workspace_root / "site/.stage"
            manifest = json.loads((stage_root / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(exit_code, 0)
            self.assertEqual(stderr.getvalue(), "")
            self.assertEqual(manifest["command"], "build")
            for key in [
                "components",
                "artifacts",
                "routes",
                "redirects",
                "providers",
                "releases",
                "refs",
                "contentIndex",
                "unitContributions",
                "outputOwnership",
                "aggregateDependencies",
            ]:
                relative_path = manifest["dataFiles"][key]
                self.assertIsNotNone(relative_path)
                self.assertTrue((stage_root / relative_path).is_file(), key)

    def test_finalized_stage_metadata_contains_no_absolute_workspace_paths(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            with _cwd(workspace_root):
                exit_code = _run(
                    argv=["build"],
                    stdout=io.StringIO(),
                    stderr=io.StringIO(),
                )
            stage_root = workspace_root / "site/.stage"
            metadata_documents = tuple(stage_root.rglob("*.json"))
            metadata_payloads = {
                metadata_path.relative_to(stage_root).as_posix(): metadata_path.read_text(
                    encoding="utf-8"
                )
                for metadata_path in metadata_documents
            }
            unit_contributions = json.loads(
                (stage_root / "data/_pipeline/unit-contributions.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(exit_code, 0)
        self.assertTrue(metadata_payloads)
        for relative_path, metadata_payload in metadata_payloads.items():
            self.assertNotIn(
                str(workspace_root),
                metadata_payload,
                relative_path,
            )
        source_paths = [
            page["sourcePath"]
            for unit in unit_contributions["units"]
            for page in unit["pages"]
            if page.get("sourcePath") is not None
        ]
        self.assertTrue(source_paths)
        self.assertTrue(all(not Path(path).is_absolute() for path in source_paths))
        self.assertTrue(all(".." not in Path(path).parts for path in source_paths))

    def test_build_stages_site_and_vendor_static_assets(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            _expand_workspace_for_multiple_owned_units(workspace_root)
            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(argv=["build"], stdout=stdout, stderr=stderr)
            stage_root = workspace_root / "site/.stage"
            site_css = (stage_root / "static/site/site.css").read_text(encoding="utf-8")
            vendor_logo = (stage_root / "static/site/vendor/vendorAssets:0/logo.svg").read_text(
                encoding="utf-8"
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(site_css, "body {}\n")
        self.assertEqual(vendor_logo, "<svg/>")

    def test_output_ownership_rejects_case_only_stage_path_collisions(self) -> None:
        with self.assertRaises(StageIntegrityError) as raised:
            _validate_output_ownership(
                (
                    OwnedUnit(
                        unit_id="component:upper",
                        owner_id="component:upper",
                        kind=OwnedUnitKind.COMPONENT,
                        content_stage_roots=(Path("content/Docs"),),
                    ),
                    OwnedUnit(
                        unit_id="component:lower",
                        owner_id="component:lower",
                        kind=OwnedUnitKind.COMPONENT,
                        content_stage_roots=(Path("content/docs"),),
                    ),
                ),
            )

        self.assertIn("case-insensitive path collision", str(raised.exception))

    def test_build_emits_pipeline_front_matter_and_content_index(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            with _cwd(workspace_root):
                exit_code = _run(argv=["build"], stdout=io.StringIO(), stderr=io.StringIO())
            stage_root = workspace_root / "site/.stage"
            release_page = frontmatter.load(stage_root / "content/spark/releases/4.0.0/index.md")
            content_index = json.loads((stage_root / "data/content-index.json").read_text(encoding="utf-8"))["items"]
            release_entry = next(item for item in content_index if item["pageKind"] == "release-page")

        self.assertEqual(exit_code, 0)
        self.assertEqual(release_page.metadata["pipeline"]["component"]["slug"], "spark")
        self.assertEqual(release_page.metadata["pipeline"]["page"]["kind"], "release-page")
        self.assertEqual(release_page.metadata["pipeline"]["page"]["provider"]["key"], "github")
        self.assertEqual(release_page.metadata["pipeline"]["page"]["version"]["kind"], "released")
        self.assertEqual(release_entry["path"], "/spark/releases/4.0.0")
        self.assertEqual(
            release_entry["sourcePath"],
            "components/runtime/docs/releases/4.0.0/index.md",
        )
        self.assertEqual(release_entry["provider"], "github")
        self.assertEqual(release_entry["versionKind"], "released")

    def test_build_emits_component_weights_in_components_aggregate(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            with _cwd(workspace_root):
                exit_code = _run(argv=["build"], stdout=io.StringIO(), stderr=io.StringIO())
            stage_root = workspace_root / "site/.stage"
            components = json.loads((stage_root / "data/components.json").read_text(encoding="utf-8"))["items"]

        self.assertEqual(exit_code, 0)
        self.assertEqual(components[0]["slug"], "spark")
        self.assertEqual(components[0]["weight"], 100)

    def test_build_stages_component_owned_development_docs_without_artifacts(self) -> None:
        with _workspace(with_content_file=True, topology="component_only_development") as workspace_root:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(argv=["build"], stdout=stdout, stderr=stderr)
            stage_root = workspace_root / "site/.stage"
            routes = json.loads((stage_root / "data/routes.json").read_text(encoding="utf-8"))["items"]
            content_index = json.loads((stage_root / "data/content-index.json").read_text(encoding="utf-8"))["items"]
            staged_development_exists = (
                stage_root / "content/components/site-pipeline/development/index.md"
            ).is_file()
            development_route = next(
                entry
                for entry in routes
                if entry["targetId"] == "development:site-pipeline:component"
            )
            development_entry = next(
                entry
                for entry in content_index
                if entry["path"] == "/components/site-pipeline/development"
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(development_route["path"], "/components/site-pipeline/development/")
        self.assertEqual(development_route["section"], "development")
        self.assertTrue(staged_development_exists)
        self.assertEqual(development_entry["sourcePath"], "components/site-pipeline/docs/index.md")
        self.assertEqual(development_entry["pageKind"], "development-page")

    def test_build_stages_component_owned_pages_and_assets_under_publication_paths(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            components_path = workspace_root / "site/catalog.yaml"
            _replace_file_text_once(
                components_path,
                "defaults:\n  docsRoot: docs\n  publication:\n    origin: docs\n",
                "defaults:\n  pagesRoot: pages\n  docsRoot: docs\n  assetsRoot: assets\n  publication:\n    origin: docs\n",
            )
            _replace_file_text_once(
                components_path,
                "    publication:\n      mountPath: /spark/\n",
                "    publication:\n      mountPath: /products/spark/\n",
            )
            (workspace_root / "components/runtime/pages").mkdir(parents=True, exist_ok=True)
            (workspace_root / "components/runtime/pages/index.md").write_text(
                "---\ntitle: Spark Landing\n---\nbody\n",
                encoding="utf-8",
            )
            (workspace_root / "components/runtime/assets").mkdir(parents=True, exist_ok=True)
            (workspace_root / "components/runtime/assets/logo.svg").write_text(
                "<svg/>\n",
                encoding="utf-8",
            )

            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(argv=["build"], stdout=stdout, stderr=stderr)
            stage_root = workspace_root / "site/.stage"
            routes = json.loads((stage_root / "data/routes.json").read_text(encoding="utf-8"))["items"]
            component_route = next(
                entry for entry in routes if entry["targetId"] == "component:spark"
            )
            staged_component_page_exists = (stage_root / "content/products/spark/index.md").is_file()
            staged_component_asset_exists = (
                stage_root / "static/products/spark/assets/logo.svg"
            ).is_file()
            legacy_component_page_exists = (stage_root / "content/components/spark/index.md").exists()
            legacy_component_asset_exists = (
                stage_root / "static/components/spark/assets/logo.svg"
            ).exists()

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(component_route["path"], "/products/spark/")
        self.assertTrue(staged_component_page_exists)
        self.assertTrue(staged_component_asset_exists)
        self.assertFalse(legacy_component_page_exists)
        self.assertFalse(legacy_component_asset_exists)

    def test_build_stages_two_artifact_component_through_shared_component_routes(self) -> None:
        with _workspace(with_content_file=True, topology="two_artifacts") as workspace_root:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(argv=["build"], stdout=stdout, stderr=stderr)
            stage_root = workspace_root / "site/.stage"
            routes = json.loads((stage_root / "data/routes.json").read_text(encoding="utf-8"))["items"]
            content_paths = {
                entry["path"]: entry["sourcePath"]
                for entry in json.loads(
                    (stage_root / "data/content-index.json").read_text(encoding="utf-8")
                )["items"]
            }
            released_target_ids = {
                entry["targetId"]
                for entry in routes
                if entry["path"] == "/spark/releases/4.0.0/"
            }
            development_target_ids = {
                entry["targetId"]
                for entry in routes
                if entry["path"] == "/spark/development/"
            }
            staged_development_guide_exists = (
                stage_root / "content/spark/development/guide/index.md"
            ).is_file()
            staged_development_reference_exists = (
                stage_root / "content/spark/development/reference/index.md"
            ).is_file()
            staged_release_guide_exists = (
                stage_root / "content/spark/releases/4.0.0/guide/index.md"
            ).is_file()
            staged_release_reference_exists = (
                stage_root / "content/spark/releases/4.0.0/reference/index.md"
            ).is_file()

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(
            released_target_ids,
            {"released:spark:api:4.0.0", "released:spark:runtime:4.0.0"},
        )
        self.assertEqual(
            development_target_ids,
            {"development:spark", "development:spark:api", "development:spark:runtime"},
        )
        self.assertEqual(
            content_paths["/spark/development/guide"],
            "components/runtime/docs/runtime/guide/index.md",
        )
        self.assertEqual(
            content_paths["/spark/development/reference"],
            "components/api/docs/reference/index.md",
        )
        self.assertEqual(
            content_paths["/spark/releases/4.0.0/guide"],
            "components/runtime/docs/runtime/releases/4.0.0/guide/index.md",
        )
        self.assertEqual(
            content_paths["/spark/releases/4.0.0/reference"],
            "components/api/docs/releases/4.0.0/reference/index.md",
        )
        self.assertTrue(staged_development_guide_exists)
        self.assertTrue(staged_development_reference_exists)
        self.assertTrue(staged_release_guide_exists)
        self.assertTrue(staged_release_reference_exists)

    def test_build_stages_rich_lifecycle_matrix_into_routes_and_aggregates(self) -> None:
        with _workspace(with_content_file=True, topology="rich_lifecycle") as workspace_root:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(argv=["build"], stdout=stdout, stderr=stderr)
            stage_root = workspace_root / "site/.stage"
            routes = json.loads((stage_root / "data/routes.json").read_text(encoding="utf-8"))["items"]
            artifacts = json.loads((stage_root / "data/artifacts.json").read_text(encoding="utf-8"))["items"]
            candidates = json.loads((stage_root / "data/candidates.json").read_text(encoding="utf-8"))["items"]
            route_paths = {entry["targetId"]: entry["path"] for entry in routes}
            artifact_entry = artifacts[0]

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(route_paths["development:spark:runtime"], "/spark/development/")
        self.assertEqual(route_paths["line-head:spark:runtime:4.0"], "/spark/development/4.0/")
        self.assertEqual(route_paths["line-head:spark:runtime:4.1"], "/spark/development/4.1/")
        self.assertEqual(
            route_paths["candidate:spark:runtime:4.2.0-rc2"],
            "/spark/development/candidates/4.2.0-rc2/",
        )
        self.assertEqual(route_paths["released:spark:runtime:4.0.2"], "/spark/releases/4.0.2/")
        self.assertEqual(route_paths["released:spark:runtime:4.1.0"], "/spark/releases/4.1.0/")
        self.assertEqual([entry["version"] for entry in candidates], ["4.2.0-rc2"])
        self.assertEqual(artifact_entry["latestRelease"]["version"], "4.1.0")
        self.assertEqual(artifact_entry["latestCandidate"]["version"], "4.2.0-rc2")
        self.assertEqual(
            [(entry["key"], entry["latest"]) for entry in artifact_entry["releaseLines"]],
            [("4.1", "4.1.0"), ("4.0", "4.0.2")],
        )

    def test_build_resolves_internal_and_withdrawn_redirects_in_redirect_inventory(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            components_path = workspace_root / "site/catalog.yaml"
            provider_snapshot_path = workspace_root / "site/provider-snapshot.json"
            _replace_file_text_once(
                components_path,
                "    publication:\n      mountPath: /spark/\n",
                "    publication:\n      mountPath: /spark/\n      redirects:\n        - fromPath: /spark/development/docs/\n          target: release:spark/runtime@4.0.0\n          reason: Current docs live on the latest release route.\n",
            )
            _replace_file_text_once(
                components_path,
                "          releases:\n            - version: '4.0.0'\n",
                "          releases:\n            - version: '4.0.0'\n              publicationState: withdrawn\n              withdrawalBehavior: redirect\n              redirectTarget: route:/spark/\n",
            )
            provider_snapshot = json.loads(provider_snapshot_path.read_text(encoding="utf-8"))
            provider_snapshot["records"][2]["publicationState"] = "withdrawn"
            provider_snapshot_path.write_text(
                json.dumps(provider_snapshot) + "\n", encoding="utf-8"
            )

            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(argv=["build"], stdout=stdout, stderr=stderr)
            stage_root = workspace_root / "site/.stage"
            redirects = json.loads((stage_root / "data/redirects.json").read_text(encoding="utf-8"))["items"]
            redirects_by_source = {entry["fromUrl"]: entry for entry in redirects}

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(
            redirects_by_source["https://docs.example.org/spark/development/docs/"]["toUrl"],
            "https://docs.example.org/spark/releases/4.0.0/",
        )
        self.assertEqual(
            redirects_by_source["https://docs.example.org/spark/development/docs/"]["sourceKind"],
            "catalog",
        )
        self.assertEqual(
            redirects_by_source["https://docs.example.org/spark/development/docs/"]["reason"],
            "Current docs live on the latest release route.",
        )
        self.assertEqual(
            redirects_by_source["https://docs.example.org/spark/releases/4.0.0/"]["toUrl"],
            "https://docs.example.org/spark/",
        )
        self.assertEqual(
            redirects_by_source["https://docs.example.org/spark/releases/4.0.0/"]["sourceKind"],
            "withdrawal",
        )

    def test_check_reports_missing_internal_page_link_and_build_preserves_authored_page_links(
        self,
    ) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            components_path = workspace_root / "site/catalog.yaml"
            release_root = workspace_root / "components/runtime/docs/releases/4.0.0"
            _replace_file_text_once(
                components_path,
                "site: {}\n",
                "site: {}\nvalidation:\n  linkChecks:\n    enabled: true\n    checkRootAbsolute: true\n    internalPrefixes:\n      - /spark/\n",
            )
            (release_root / "guide.md").write_text("guide page\n", encoding="utf-8")
            (release_root / "index.md").write_text(
                "[Guide](/spark/releases/4.0.0/guide/) [Missing](/spark/releases/4.0.0/missing/)\n",
                encoding="utf-8",
            )

            check_stdout = io.StringIO()
            check_stderr = io.StringIO()
            with _cwd(workspace_root):
                check_exit_code = _run(
                    argv=["check", "--report-format", "json", "--report-schema-version", "1"],
                    stdout=check_stdout,
                    stderr=check_stderr,
                )
            check_report = json.loads(check_stdout.getvalue())
            missing_diagnostic = next(
                diagnostic
                for diagnostic in check_report["diagnostics"]
                if diagnostic["code"] == "page-link-target-missing"
            )

            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                build_exit_code = _run(argv=["build"], stdout=stdout, stderr=stderr)
            stage_root = workspace_root / "site/.stage"
            staged_development_index = (
                stage_root / "content/spark/development/releases/4.0.0/index.md"
            ).read_text(encoding="utf-8")
            staged_release_index = (stage_root / "content/spark/releases/4.0.0/index.md").read_text(
                encoding="utf-8"
            )
            staged_development_guide_exists = (
                stage_root / "content/spark/development/releases/4.0.0/guide.md"
            ).is_file()
            staged_release_guide_exists = (stage_root / "content/spark/releases/4.0.0/guide.md").is_file()

        self.assertEqual(check_exit_code, 0)
        self.assertEqual(check_stderr.getvalue(), "")
        self.assertTrue(check_report["summary"]["passed"])
        self.assertEqual(check_report["summary"]["warningCount"], 1)
        self.assertEqual(missing_diagnostic["details"]["sourceRelativePath"], "releases/4.0.0/index.md")
        self.assertEqual(missing_diagnostic["details"]["sourceLine"], 1)
        self.assertEqual(missing_diagnostic["details"]["sourceRoute"], "/spark/development/releases/4.0.0")
        self.assertEqual(missing_diagnostic["details"]["resolvedPath"], "/spark/releases/4.0.0/missing")
        self.assertEqual(build_exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertTrue(staged_development_guide_exists)
        self.assertTrue(staged_release_guide_exists)
        self.assertIn("[Guide](/spark/releases/4.0.0/guide/)", staged_development_index)
        self.assertIn("[Missing](/spark/releases/4.0.0/missing/)", staged_development_index)
        self.assertIn("[Guide](/spark/releases/4.0.0/guide/)", staged_release_index)
        self.assertIn("[Missing](/spark/releases/4.0.0/missing/)", staged_release_index)

    def test_build_emits_multi_origin_alias_routes_and_origin_scoped_redirects(
        self,
    ) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            components_path = workspace_root / "site/catalog.yaml"
            _replace_file_text_once(
                components_path,
                "origins:\n  docs:\n    baseUrl: https://docs.example.org\n",
                "origins:\n  docs:\n    baseUrl: https://docs.example.org\n  archive:\n    baseUrl: https://archive.example.org\n",
            )
            _replace_file_text_once(
                components_path,
                "    publication:\n      mountPath: /spark/\n",
                "    publication:\n      mountPath: /spark/\n      aliases:\n        - path: /spark/archive/\n          origin: archive\n          label: archive\n      redirects:\n        - fromOrigin: archive\n          fromPath: /spark/archive/latest/\n          target: route:/spark/archive/\n",
            )

            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(argv=["build"], stdout=stdout, stderr=stderr)
            stage_root = workspace_root / "site/.stage"
            routes = json.loads(
                (stage_root / "data/routes.json").read_text(encoding="utf-8")
            )["items"]
            component_route = next(
                entry for entry in routes if entry["targetId"] == "component:spark"
            )
            released_route = next(
                entry
                for entry in routes
                if entry["targetId"] == "released:spark:runtime:4.0.0"
            )
            redirects = json.loads(
                (stage_root / "data/redirects.json").read_text(encoding="utf-8")
            )["items"]
            alias_route = next(
                entry
                for entry in routes
                if entry["originKey"] == "archive"
                and entry["path"] == "/spark/archive/"
            )
            redirect_entry = next(
                entry
                for entry in redirects
                if entry["fromUrl"]
                == "https://archive.example.org/spark/archive/latest/"
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(component_route["section"], "component")
        self.assertTrue(component_route["canonical"])
        self.assertEqual(component_route["routeKind"], "published")
        self.assertEqual(released_route["section"], "released")
        self.assertEqual(released_route["routeKind"], "context")
        self.assertEqual(alias_route["baseUrl"], "https://archive.example.org")
        self.assertEqual(alias_route["url"], "https://archive.example.org/spark/archive/")
        self.assertEqual(alias_route["label"], "archive")
        self.assertEqual(alias_route["routeKind"], "alias")
        self.assertEqual(
            redirect_entry["toUrl"], "https://archive.example.org/spark/archive/"
        )
        self.assertEqual(redirect_entry["sourceKind"], "catalog")

    def test_build_marks_alias_route_as_canonical_when_canonical_path_uses_alias(
        self,
    ) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            components_path = workspace_root / "site/catalog.yaml"
            _replace_file_text_once(
                components_path,
                "    publication:\n      mountPath: /spark/\n",
                "    publication:\n      mountPath: /spark/\n      canonicalPath: /spark/stable/\n      aliases:\n        - path: /spark/stable/\n          label: stable\n",
            )

            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(argv=["build"], stdout=stdout, stderr=stderr)
            stage_root = workspace_root / "site/.stage"
            routes = json.loads(
                (stage_root / "data/routes.json").read_text(encoding="utf-8")
            )["items"]
            component_route = next(
                entry for entry in routes if entry["targetId"] == "component:spark"
            )
            alias_route = next(entry for entry in routes if entry["path"] == "/spark/stable/")

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertFalse(component_route.get("canonical", False))
        self.assertTrue(alias_route["canonical"])
        self.assertEqual(alias_route["routeKind"], "alias")
        self.assertEqual(alias_route["label"], "stable")

    def test_component_redirect_uses_canonical_alias_route_when_present(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            components_path = workspace_root / "site/catalog.yaml"
            _replace_file_text_once(
                components_path,
                "    publication:\n      mountPath: /spark/\n",
                "    publication:\n      mountPath: /spark/\n      canonicalPath: /spark/stable/\n      aliases:\n        - path: /spark/stable/\n          label: stable\n      redirects:\n        - fromPath: /spark/landing/\n          target: component:spark\n",
            )

            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(argv=["build"], stdout=stdout, stderr=stderr)
            stage_root = workspace_root / "site/.stage"
            redirects = json.loads(
                (stage_root / "data/redirects.json").read_text(encoding="utf-8")
            )["items"]
            redirect_entry = next(
                entry
                for entry in redirects
                if entry["fromUrl"] == "https://docs.example.org/spark/landing/"
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(
            redirect_entry["toUrl"],
            "https://docs.example.org/spark/stable/",
        )

    def test_redirect_aggregate_rejects_line_reference_without_selected_line_head(
        self,
    ) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            components_path = workspace_root / "site/catalog.yaml"
            _replace_file_text_once(
                components_path,
                "    publication:\n      mountPath: /spark/\n",
                "    publication:\n      mountPath: /spark/\n      redirects:\n        - fromPath: /spark/docs/current/\n          target: line:spark/runtime@4.0\n",
            )
            _replace_file_text_once(
                components_path,
                "          lineHeads:\n            mode: allAuthored\n",
                "          lineHeads:\n            mode: none\n",
            )
            loaded_inputs = load_workspace_inputs(workspace_root)
            planning = evaluate_planning(
                target=PlanningTarget.BUILD,
                catalog=loaded_inputs.catalog,
                provider_snapshot=loaded_inputs.provider_snapshot,
                workspace_root=workspace_root,
                component_documents=loaded_inputs.component_documents,
                stage_root=workspace_root / "site/.stage",
                work_root=workspace_root / ".buildish/work",
            )

        self.assertIsNotNone(planning.build_plan_result.candidate)
        with self.assertRaises(StageIntegrityError):
            _build_redirect_entries(planning.build_plan_result.candidate)

    def test_write_utf8_text_file_preserves_mtime_for_identical_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            target_path = Path(tempdir) / "data.json"

            write_utf8_text_file(target_path, '{"items": []}\n')
            os.utime(target_path, ns=(1_234_567_890, 1_234_567_890))

            changed = write_utf8_text_file(target_path, '{"items": []}\n')

            self.assertFalse(changed)
            self.assertEqual(target_path.stat().st_mtime_ns, 1_234_567_890)

    def test_write_utf8_text_file_updates_mtime_when_bytes_change(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            target_path = Path(tempdir) / "data.json"

            write_utf8_text_file(target_path, '{"items": []}\n')
            os.utime(target_path, ns=(1_234_567_890, 1_234_567_890))

            changed = write_utf8_text_file(target_path, '{"items": [{"slug": "spark"}]}\n')

            self.assertTrue(changed)
            self.assertNotEqual(target_path.stat().st_mtime_ns, 1_234_567_890)

    def test_write_utf8_text_file_rejects_symlink_destination(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            real_target = workspace_root / "real.json"
            real_target.write_text('{"trusted": true}\n', encoding="utf-8")
            symlink_target = workspace_root / "data.json"
            symlink_target.symlink_to(real_target)

            with self.assertRaises(StageIntegrityError) as raised:
                write_utf8_text_file(symlink_target, '{"items": []}\n')

        self.assertIn("normal file", str(raised.exception))

    def test_write_utf8_text_file_cleans_temp_file_when_replace_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            target_path = workspace_root / "data.json"
            target_path.write_text('{"trusted": true}\n', encoding="utf-8")

            def _fail_replace(self: Path, target: Path) -> Path:
                del self, target
                raise OSError("replace blocked")

            with mock.patch("pathlib.Path.replace", new=_fail_replace), self.assertRaises(StageIntegrityError) as raised:
                write_utf8_text_file(target_path, '{"items": []}\n')

            self.assertIn("Could not write stage text file", str(raised.exception))
            self.assertEqual(target_path.read_text(encoding="utf-8"), '{"trusted": true}\n')
            self.assertEqual(list(target_path.parent.glob(".data.json.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
