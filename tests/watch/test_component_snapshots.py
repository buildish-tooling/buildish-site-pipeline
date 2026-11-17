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

"""Watch transitions for component-owned release inventory and checkout changes."""

import json
import shutil
import unittest
import yaml

from buildish_site_pipeline.cli.main import parse_invocation
from buildish_site_pipeline.commands.watch import (
    _run_watch_cycle,
    _snapshot_watch_roots,
    _dirty_unit_ids_for_paths,
)
from buildish_site_pipeline.staging.ownership import build_owned_units
from buildish_site_pipeline.commands.shared import load_workspace_inputs
from buildish_site_pipeline.planning import evaluate_planning
from buildish_site_pipeline.models.enums import PlanningTarget
from tests.staging.test_component_publication import configure_release
from tests.support.workspace import _workspace, _cwd
from tests.watch.test_incremental import _run_clean_build_snapshot, _stage_snapshot_without_manifest


class ComponentSnapshotWatchTests(unittest.TestCase):
    def test_original_source_mapping_updates_removal_and_validation_recovery(self):
        with _workspace(with_content_file=True) as root:
            path, snapshot = configure_release(root)
            with _cwd(root):
                invocation = parse_invocation(["watch"])

            def cycle(number, prior=None):
                return _run_watch_cycle(
                    invocation=invocation, cycle_number=number,
                    trusted_stage=prior.trusted_stage if prior else None,
                    prior_watch_roots=prior.watch_roots if prior else (),
                    dirty_paths=(path,) if prior else (),
                )

            prior = cycle(1)
            self.assertTrue(prior.report.summary.succeeded, prior.report)
            for number, mapping in enumerate((
                {"repository": "https://github.com/example/original", "root": "manual", "ref": "v4.0.0"},
                {"repository": "https://github.com/example/original", "root": "manual", "ref": "releases/4.0"},
                {"repository": "https://github.com/example/original", "root": ".", "ref": "releases/4.0"},
                {"repository": "https://github.com/example/replacement", "root": ".", "ref": "releases/4.0"},
                None,
            ), 2):
                with self.subTest(mapping=mapping):
                    record = snapshot["records"][0]
                    record.pop("docsSource", None)
                    if mapping is not None:
                        record["docsSource"] = mapping
                    path.write_text(json.dumps(snapshot))
                    prior = cycle(number, prior)
                    self.assertTrue(prior.report.summary.succeeded, prior.report)
                    watch_output = _stage_snapshot_without_manifest(root / "site/.stage")
                    clean_stage = root / "site/.stage-clean"
                    if clean_stage.exists():
                        shutil.rmtree(clean_stage)
                    code, clean = _run_clean_build_snapshot(root)
                    self.assertEqual(code, 0)
                    self.assertEqual(watch_output, clean)

            stable = _stage_snapshot_without_manifest(root / "site/.stage")
            snapshot["records"][0]["docsSource"] = {"root": "docs"}
            path.write_text(json.dumps(snapshot))
            failed = cycle(7, prior)
            self.assertFalse(failed.report.summary.succeeded)
            self.assertTrue(failed.report.summary.stage_usable)
            self.assertEqual(_stage_snapshot_without_manifest(root / "site/.stage"), stable)
            snapshot["records"][0].pop("docsSource")
            path.write_text(json.dumps(snapshot))
            recovered = cycle(8, failed)
            self.assertTrue(recovered.report.summary.succeeded, recovered.report)

    def test_watch_creation_removal_invalid_update_and_recovery(self):
        with _workspace(with_content_file=True) as root:
            path, snapshot = configure_release(root, present=False)
            shutil.rmtree(path.parent)
            with _cwd(root):
                invocation = parse_invocation(["watch"])

            def cycle(number, prior=None):
                return _run_watch_cycle(
                    invocation=invocation,
                    cycle_number=number,
                    trusted_stage=prior.trusted_stage if prior else None,
                    prior_watch_roots=prior.watch_roots if prior else (root / "site",),
                    dirty_paths=(path,) if prior else (),
                )

            initial = cycle(1)
            self.assertTrue(initial.report.summary.succeeded, initial.report)
            self.assertTrue(
                any(path.is_relative_to(watched) for watched in initial.watch_roots)
            )
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps(snapshot))
            release = path.parent / "4.0.0"
            release.mkdir()
            (release / "index.md").write_text("released docs")
            created = cycle(2, initial)
            self.assertTrue(created.report.summary.succeeded, created.report)
            staged = root / "site/.stage/content/spark/releases/4.0.0/index.md"
            self.assertTrue(staged.is_file())
            path.write_text("{")
            invalid = cycle(3, created)
            self.assertFalse(invalid.report.summary.succeeded)
            self.assertTrue(invalid.report.summary.stage_usable)
            self.assertTrue(staged.is_file())
            shutil.rmtree(path.parent)
            removed = cycle(4, invalid)
            self.assertTrue(removed.report.summary.succeeded, removed.report)
            self.assertFalse(staged.exists())

    def test_absent_dependency_uses_existing_workspace_ancestor(self):
        with _workspace() as root:
            path = root / "missing/source/docs/releases/provider.json"
            self.assertEqual(_snapshot_watch_roots((path,), root), (root,))

    def test_historical_page_edits_do_not_dirty_development_owner(self):
        with _workspace(with_content_file=True) as root:
            path, _ = configure_release(root)
            loaded = load_workspace_inputs(root)
            planning = evaluate_planning(
                target=PlanningTarget.WATCH,
                workspace_root=root,
                catalog=loaded.catalog,
                provider_snapshot=loaded.provider_snapshot,
                component_documents=loaded.component_documents,
                snapshot_inputs=loaded.snapshot_inputs,
            )
            plan = planning.build_plan_result.candidate
            args = dict(
                build_plan=plan,
                units=build_owned_units(plan),
                workspace_root=root,
                site_root=root / "site",
                catalog_path=root / "site/catalog.yaml",
                provider_snapshot_path=loaded.provider_snapshot_path,
            )
            self.assertEqual(
                _dirty_unit_ids_for_paths(
                    dirty_paths=(path.parent / "4.0.0/index.md",), **args
                ),
                frozenset(),
            )
            self.assertTrue(_dirty_unit_ids_for_paths(dirty_paths=(path,), **args))

    def test_artifactless_authored_release_section_remains_live(self):
        with _workspace(
            with_content_file=True, topology="component_only_development"
        ) as root:
            catalog_path = root / "site/catalog.yaml"
            catalog = yaml.safe_load(catalog_path.read_text())
            catalog["components"][0]["providerSnapshot"] = {
                "source": "site-pipeline",
                "path": "inventory.json",
                "requirement": "optional",
            }
            catalog_path.write_text(yaml.safe_dump(catalog, sort_keys=False))
            source = root / "components/site-pipeline/docs/releases/guide.md"
            source.parent.mkdir()
            source.write_text("OLD CONTENT")
            with _cwd(root):
                invocation = parse_invocation(["watch"])
            first = _run_watch_cycle(
                invocation=invocation,
                cycle_number=1,
                trusted_stage=None,
                prior_watch_roots=(),
                dirty_paths=(),
            )
            self.assertTrue(first.report.summary.succeeded, first.report)
            source.write_text("NEW CONTENT")
            second = _run_watch_cycle(
                invocation=invocation,
                cycle_number=2,
                trusted_stage=first.trusted_stage,
                prior_watch_roots=first.watch_roots,
                dirty_paths=(source,),
            )
            self.assertTrue(second.report.summary.succeeded, second.report)
            staged = (
                root
                / "site/.stage/content/components/site-pipeline/development/releases/guide.md"
            )
            self.assertIn("NEW CONTENT", staged.read_text())

    def test_invalid_inventory_at_new_binding_retains_recovery_watch(self):
        with _workspace(with_content_file=True) as root:
            configure_release(root)
            with _cwd(root):
                invocation = parse_invocation(["watch"])
            first = _run_watch_cycle(
                invocation=invocation,
                cycle_number=1,
                trusted_stage=None,
                prior_watch_roots=(),
                dirty_paths=(),
            )
            self.assertTrue(first.report.summary.succeeded)
            catalog_path = root / "site/catalog.yaml"
            catalog = yaml.safe_load(catalog_path.read_text())
            catalog["sources"]["inventory"] = {"localDir": "new-inventory"}
            catalog["components"][0]["providerSnapshot"] = {
                "source": "inventory",
                "path": "provider.json",
            }
            catalog_path.write_text(yaml.safe_dump(catalog, sort_keys=False))
            path = root / "new-inventory/provider.json"
            path.parent.mkdir()
            path.write_text("{")
            failed = _run_watch_cycle(
                invocation=invocation,
                cycle_number=2,
                trusted_stage=first.trusted_stage,
                prior_watch_roots=first.watch_roots,
                dirty_paths=(catalog_path,),
            )
            self.assertFalse(failed.report.summary.succeeded)
            self.assertTrue(failed.report.summary.stage_usable)
            self.assertTrue(
                any(path.is_relative_to(watched) for watched in failed.watch_roots)
            )

    def test_component_definition_and_snapshot_edits_reconcile_outputs(self):
        from tests.planning.test_version_ownership import component_only

        with _workspace(with_content_file=True) as root:
            snapshot_path, snapshot = component_only(root)
            catalog_path = root / "site/catalog.yaml"
            catalog = yaml.safe_load(catalog_path.read_text())
            catalog["components"][0]["publicationSelection"] = {
                "development": True,
                "lineHeads": {"mode": "none"},
                "releases": {"mode": "latestPerLine"},
            }
            catalog_path.write_text(yaml.safe_dump(catalog))
            catalog_bytes = catalog_path.read_bytes()
            metadata_path = root / "components/runtime/site/component.yaml"
            with _cwd(root):
                invocation = parse_invocation(["watch"])

            def cycle(number, prior=None, paths=()):
                result = _run_watch_cycle(
                    invocation=invocation, cycle_number=number,
                    trusted_stage=prior.trusted_stage if prior else None,
                    prior_watch_roots=prior.watch_roots if prior else (),
                    dirty_paths=paths,
                )
                self.assertTrue(result.report.summary.succeeded, result.report)
                return result

            first = cycle(1)
            stage = root / "site/.stage/content/spark/releases"
            self.assertTrue((stage / "4.0.0/index.md").exists())
            snapshot["artifacts"][0]["releaseLines"][0]["latest"] = "4.0.1"
            snapshot["artifacts"][0]["releases"].append({"version": "4.0.1", "releaseLine": "4.0"})
            release = snapshot_path.parent / "4.0.1"
            release.mkdir()
            (release / "index.md").write_text("latest release")
            snapshot_path.write_text(json.dumps(snapshot))
            second = cycle(2, first, (snapshot_path,))
            self.assertTrue((stage / "4.0.1/index.md").exists())
            self.assertFalse((stage / "4.0.0").exists())

            metadata = yaml.safe_load(metadata_path.read_text())
            metadata["artifacts"].append({"key": "api", "docsRoot": "api-docs"})
            metadata_path.write_text(yaml.safe_dump(metadata))
            snapshot["artifacts"].append({"componentSlug": "spark", "artifactKey": "api", "releaseLines": [{"key": "2", "latest": "2.0"}], "releases": [{"version": "2.0", "releaseLine": "2"}]})
            snapshot_path.write_text(json.dumps(snapshot))
            api_root = root / "components/runtime/api-docs/releases/2.0"
            api_root.mkdir(parents=True)
            (api_root / "index.md").write_text("api release")
            third = cycle(3, second, (metadata_path, snapshot_path))
            self.assertTrue((stage / "2.0/index.md").exists())
            metadata["artifacts"].pop()
            metadata_path.write_text(yaml.safe_dump(metadata))
            snapshot["artifacts"].pop()
            snapshot["artifacts"][0]["releaseLines"] = []
            for item in snapshot["artifacts"][0]["releases"]:
                item.pop("releaseLine", None)
            for item in snapshot["records"]:
                item.pop("releaseLine", None)
            snapshot_path.write_text(json.dumps(snapshot))
            cycle(4, third, (metadata_path, snapshot_path))
            self.assertFalse((stage / "2.0").exists())
            self.assertFalse((stage / "4.0.1").exists())
            self.assertEqual(catalog_path.read_bytes(), catalog_bytes)

    def test_invalid_new_component_definition_retains_source_recovery_watch(self):
        with _workspace(with_content_file=True) as root:
            configure_release(root)
            with _cwd(root):
                invocation = parse_invocation(["watch"])
            first = _run_watch_cycle(invocation=invocation, cycle_number=1, trusted_stage=None, prior_watch_roots=(), dirty_paths=())
            self.assertTrue(first.report.summary.succeeded)
            catalog_path = root / "site/catalog.yaml"
            catalog = yaml.safe_load(catalog_path.read_text())
            catalog["sources"]["runtime"]["localDir"] = "replacement"
            catalog_path.write_text(yaml.safe_dump(catalog))
            metadata_path = root / "replacement/site/component.yaml"
            metadata_path.parent.mkdir(parents=True)
            metadata_path.write_text("{")
            failed = _run_watch_cycle(invocation=invocation, cycle_number=2, trusted_stage=first.trusted_stage, prior_watch_roots=first.watch_roots, dirty_paths=(catalog_path,))
            self.assertFalse(failed.report.summary.succeeded)
            self.assertTrue(failed.report.summary.stage_usable)
            self.assertTrue(any(metadata_path.is_relative_to(path) for path in failed.watch_roots))
