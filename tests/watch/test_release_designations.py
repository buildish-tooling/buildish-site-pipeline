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

"""Current designation output, watch/clean parity and last-good recovery."""

import json
import shutil
import unittest

from buildish_site_pipeline.cli.main import parse_invocation
from buildish_site_pipeline.commands.watch import _run_watch_cycle
from tests.staging.test_component_publication import configure_release
from tests.staging.test_release_designations import (
    add_recommendation,
    artifact_rows,
    pin,
)
from tests.support.workspace import _workspace, _cwd
from tests.watch.test_incremental import (
    _run_clean_build_snapshot,
    _stage_snapshot_without_manifest,
)


class ReleaseDesignationWatchTests(unittest.TestCase):
    def test_pin_state_inventory_root_and_retained_output_match_clean_build(self):
        with _workspace(with_content_file=True) as root:
            path, snapshot = configure_release(root, requirement="optional")
            add_recommendation(snapshot)
            path.write_text(json.dumps(snapshot))
            pin(root, ["4.0.0"], development=True)
            with _cwd(root):
                invocation = parse_invocation(["watch"])
            prior = None

            def cycle(dirty=()):
                nonlocal prior
                prior = _run_watch_cycle(
                    invocation=invocation,
                    cycle_number=1 if prior is None else prior.report.cycle + 1,
                    trusted_stage=prior.trusted_stage if prior else None,
                    prior_watch_roots=prior.watch_roots if prior else (),
                    dirty_paths=dirty,
                )
                self.assertTrue(prior.report.summary.succeeded, prior.report)
                clean_stage = root / "site/.stage-clean"
                if clean_stage.exists():
                    shutil.rmtree(clean_stage)
                code, clean = _run_clean_build_snapshot(root)
                self.assertEqual(code, 0)
                self.assertEqual(
                    _stage_snapshot_without_manifest(root / "site/.stage"), clean
                )
                return artifact_rows(root)[0]["releaseDesignations"]

            self.assertFalse(cycle()["latestStable"]["selected"])
            self.assertFalse(
                (root / "site/.stage/content/spark/releases/4.0.1").exists()
            )
            snapshot["artifacts"][0]["latestStable"] = "4.0.0"
            path.write_text(json.dumps(snapshot))
            self.assertEqual(
                cycle((path,))["latestStable"]["availability"]["kind"], "docs"
            )
            # Dirty an independent site unit; component pages are retained.
            site_page = root / "site/content/retained-check.md"
            site_page.parent.mkdir(parents=True, exist_ok=True)
            site_page.write_text("independent site page")
            self.assertEqual(
                cycle((site_page,))["latestStable"]["availability"]["kind"], "docs"
            )
            release = snapshot["artifacts"][0]["releases"][0]
            record = next(
                item
                for item in snapshot["records"]
                if item["kind"] == "released" and item["version"] == "4.0.0"
            )
            for state, behavior, expected in (
                ("hidden", None, "unavailable"),
                ("withdrawn", "notice", "notice"),
                ("tombstoned", "redirect", "redirect"),
                ("published", None, "docs"),
            ):
                record["publicationState"] = state
                release["publicationState"] = state
                release.pop("withdrawalBehavior", None)
                release.pop("redirectTarget", None)
                if behavior:
                    release["withdrawalBehavior"] = behavior
                if behavior == "redirect":
                    release["redirectTarget"] = "component:spark"
                path.write_text(json.dumps(snapshot))
                self.assertEqual(
                    cycle((path,))["latestStable"]["availability"]["kind"], expected
                )
                self.assertEqual(
                    (
                        root / "site/.stage/content/spark/releases/4.0.0/index.md"
                    ).exists(),
                    expected in {"notice", "docs"},
                )
            path.unlink()
            self.assertEqual(cycle((path,)), {"snapshotStatus": "missing", "lines": []})
            path.write_text(json.dumps(snapshot))
            self.assertEqual(
                cycle((path,))["latestStable"]["availability"]["kind"], "docs"
            )
            landing = path.parent / "4.0.0/index.md"
            (landing.parent / "child.md").write_text("descendant remains")
            landing.unlink()
            snapshot["providers"][0]["fetchedAt"] = "2026-11-17T00:00:00Z"
            path.write_text(json.dumps(snapshot))
            self.assertEqual(
                cycle((path,))["latestStable"]["availability"],
                {"kind": "unavailable", "reason": "no-landing-page"},
            )

    def test_duplicate_conflict_and_missing_docs_preserve_last_good_then_recover(self):
        for failure in ("duplicate", "conflict", "docs"):
            with (
                self.subTest(failure=failure),
                _workspace(with_content_file=True) as root,
            ):
                path, snapshot = configure_release(root)
                add_recommendation(snapshot)
                path.write_text(json.dumps(snapshot))
                pin(root, ["4.0.0"], development=True)
                with _cwd(root):
                    invocation = parse_invocation(["watch"])

                def cycle(number, prior=None, invocation=invocation, path=path):
                    return _run_watch_cycle(
                        invocation=invocation,
                        cycle_number=number,
                        trusted_stage=prior.trusted_stage if prior else None,
                        prior_watch_roots=prior.watch_roots if prior else (),
                        dirty_paths=(path,) if prior else (),
                    )

                first = cycle(1)
                self.assertTrue(first.report.summary.succeeded, first.report)
                before = _stage_snapshot_without_manifest(root / "site/.stage")
                if failure == "duplicate":
                    snapshot["records"].append(
                        dict(snapshot["records"][-1], externalId="duplicate")
                    )
                elif failure == "conflict":
                    snapshot["artifacts"][0]["releases"][-1]["publicationState"] = (
                        "hidden"
                    )
                else:
                    (path.parent / "4.0.0").rename(path.parent / "saved-docs")
                path.write_text(json.dumps(snapshot))
                failed = cycle(2, first)
                self.assertFalse(failed.report.summary.succeeded)
                self.assertTrue(failed.report.summary.stage_usable)
                self.assertEqual(
                    _stage_snapshot_without_manifest(root / "site/.stage"), before
                )
                if failure == "duplicate":
                    snapshot["records"].pop()
                elif failure == "conflict":
                    snapshot["artifacts"][0]["releases"][-1].pop("publicationState")
                else:
                    (path.parent / "saved-docs").rename(path.parent / "4.0.0")
                path.write_text(json.dumps(snapshot))
                recovered = cycle(3, failed)
                self.assertTrue(recovered.report.summary.succeeded, recovered.report)
                self.assertEqual(
                    _stage_snapshot_without_manifest(root / "site/.stage"), before
                )
