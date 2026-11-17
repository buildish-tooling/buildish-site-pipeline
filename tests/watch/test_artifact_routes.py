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

"""Clean/watch parity and last-good publication for artifact routing."""

import unittest

import yaml

from buildish_site_pipeline.cli.main import parse_invocation
from buildish_site_pipeline.commands.watch import _run_watch_cycle
from tests.staging.test_artifact_routes import configure_routes
from tests.support.staging import _stage_snapshot
from tests.support.workspace import _workspace, _cwd
from tests.watch.test_incremental import (
    _run_watch_then_snapshot,
    _run_clean_build_snapshot,
)


class ArtifactRouteWatchTests(unittest.TestCase):
    def test_mode_default_custom_path_and_artifact_metadata_changes_match_clean_build(
        self,
    ):
        with _workspace(with_content_file=True, topology="two_artifacts") as root:
            catalog_path = root / "site/catalog.yaml"
            metadata_path = root / "components/runtime/site/component.yaml"

            def change(**policy):
                def apply():
                    configure_routes(root, **policy)
                    return (catalog_path,)

                return apply

            def add_and_reorder():
                metadata = yaml.safe_load(metadata_path.read_text())
                metadata["artifacts"].reverse()
                metadata["artifacts"].append({"key": "manual", "docsRoot": "manual"})
                metadata_path.write_text(yaml.safe_dump(metadata))
                docs = root / "components/runtime/manual"
                docs.mkdir()
                (docs / "index.md").write_text("new independent artifact")
                return (metadata_path,)

            watched = _run_watch_then_snapshot(
                workspace_root=root,
                responses=[
                    (True, change(artifactRouting="namespaced")),
                    (False, ()),
                    (True, change(defaultArtifact="runtime")),
                    (False, ()),
                    (True, change(defaultArtifact="api")),
                    (False, ()),
                    (True, change(developmentPath="/nightly/", docsPath="/manual/")),
                    (False, ()),
                    (True, add_and_reorder),
                    (False, None),
                ],
            )
            code, clean = _run_clean_build_snapshot(root)
            self.assertEqual(code, 0)
            self.assertEqual(watched, clean)
            stage = root / "site/.stage/content"
            self.assertFalse((stage / "spark/development").exists())
            self.assertTrue(
                (stage / "nightly/artifacts/runtime/guide/index.md").is_file()
            )
            self.assertTrue((stage / "nightly/reference/index.md").is_file())
            self.assertTrue((stage / "nightly/artifacts/manual/index.md").is_file())

    def test_unknown_default_and_duplicate_claim_failures_keep_last_good_then_recover(
        self,
    ):
        for failure in ("default", "duplicate", "mount"):
            with (
                self.subTest(failure=failure),
                _workspace(with_content_file=True, topology="two_artifacts") as root,
            ):
                configure_routes(
                    root, artifactRouting="namespaced", defaultArtifact="runtime"
                )
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
                before = _stage_snapshot(root / "site/.stage")
                catalog_path = root / "site/catalog.yaml"
                if failure == "default":
                    configure_routes(root, defaultArtifact="absent")
                    dirty = catalog_path
                elif failure == "duplicate":
                    dirty = root / "components/runtime/docs/runtime/guide.md"
                    dirty.write_text("conflicting pretty-route page")
                else:
                    catalog = yaml.safe_load(catalog_path.read_text())
                    catalog["components"][0]["mounts"] = [
                        {
                            "source": "generated/api",
                            "mountPath": "/spark/development/guide/",
                            "kind": "api",
                            "trustClass": "passive",
                        }
                    ]
                    catalog_path.write_text(yaml.safe_dump(catalog))
                    dirty = catalog_path
                failed = _run_watch_cycle(
                    invocation=invocation,
                    cycle_number=2,
                    trusted_stage=first.trusted_stage,
                    prior_watch_roots=first.watch_roots,
                    dirty_paths=(dirty,),
                )
                self.assertFalse(failed.report.summary.succeeded)
                self.assertEqual(before, _stage_snapshot(root / "site/.stage"))
                if failure == "default":
                    configure_routes(root, defaultArtifact="api")
                elif failure == "duplicate":
                    dirty.unlink()
                else:
                    catalog = yaml.safe_load(catalog_path.read_text())
                    catalog["components"][0].pop("mounts")
                    catalog_path.write_text(yaml.safe_dump(catalog))
                recovered = _run_watch_cycle(
                    invocation=invocation,
                    cycle_number=3,
                    trusted_stage=first.trusted_stage,
                    prior_watch_roots=failed.watch_roots,
                    dirty_paths=(dirty,),
                )
                self.assertTrue(recovered.report.summary.succeeded, recovered.report)
                code, clean = _run_clean_build_snapshot(root)
                self.assertEqual(code, 0)
                from tests.watch.test_incremental import (
                    _stage_snapshot_without_manifest,
                )

                self.assertEqual(
                    _stage_snapshot_without_manifest(root / "site/.stage"), clean
                )

    def test_unmanifested_retained_static_file_rejects_candidate_and_rebuild_recovers(
        self,
    ):
        with _workspace(with_content_file=True, topology="grouped_large") as root:
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
            claims = first.trusted_stage.incremental_state.output_ownership.claims
            retained_root = next(
                root / "site/.stage" / str(claim.stage_relative_path)
                for claim in claims
                if claim.unit_id == "component:spark-operator"
                and str(claim.stage_relative_path).startswith("static/")
            )
            unexpected = retained_root / "guide/index.html"
            unexpected.parent.mkdir(parents=True, exist_ok=True)
            unexpected.write_text("unmanifested retained asset")
            before = _stage_snapshot(root / "site/.stage")
            dirty = root / "components/spark/docs/index.md"
            dirty.write_text("fresh component page")
            failed = _run_watch_cycle(
                invocation=invocation,
                cycle_number=2,
                trusted_stage=first.trusted_stage,
                prior_watch_roots=first.watch_roots,
                dirty_paths=(dirty,),
            )
            self.assertFalse(failed.report.summary.succeeded)
            self.assertIn("Unexpected candidate file", str(failed.report))
            self.assertEqual(before, _stage_snapshot(root / "site/.stage"))
            recovered = _run_watch_cycle(
                invocation=invocation,
                cycle_number=3,
                trusted_stage=first.trusted_stage,
                prior_watch_roots=failed.watch_roots,
                dirty_paths=(root / "site/catalog.yaml",),
            )
            self.assertTrue(recovered.report.summary.succeeded, recovered.report)
            self.assertFalse(unexpected.exists())
            code, clean = _run_clean_build_snapshot(root)
            self.assertEqual(code, 0)
            from tests.watch.test_incremental import _stage_snapshot_without_manifest

            self.assertEqual(
                _stage_snapshot_without_manifest(root / "site/.stage"), clean
            )
