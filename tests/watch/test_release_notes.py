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

"""Watch treats release-notes files like released trees for component-bound snapshots."""

from __future__ import annotations

import json
import unittest

from buildish_site_pipeline.cli.main import parse_invocation
from buildish_site_pipeline.commands.shared import load_workspace_inputs
from buildish_site_pipeline.commands.watch import _dirty_unit_ids_for_paths, _run_watch_cycle
from buildish_site_pipeline.models.enums import PlanningTarget
from buildish_site_pipeline.planning import evaluate_planning
from buildish_site_pipeline.staging.ownership import build_owned_units
from tests.evaluation.test_release_notes import declare, write_notes
from tests.planning.test_release_notes import NOTES, with_notes
from tests.staging.test_component_publication import configure_release
from tests.support.workspace import _cwd, _workspace


def dirty_units(root, paths):
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
    if plan is None:
        raise AssertionError("expected a build plan")
    return _dirty_unit_ids_for_paths(
        dirty_paths=paths,
        build_plan=plan,
        units=build_owned_units(plan),
        workspace_root=root,
        site_root=root / "site",
        catalog_path=root / "site/catalog.yaml",
        provider_snapshot_path=loaded.provider_snapshot_path,
    )


class ReleaseNotesWatchTests(unittest.TestCase):
    def test_component_bound_notes_edits_are_immutable_until_the_snapshot_changes(self):
        with _workspace(with_content_file=True) as root:
            path, snapshot = configure_release(root)
            with_notes(snapshot)
            path.write_text(json.dumps(snapshot))
            notes = path.parent / NOTES
            notes.parent.mkdir(parents=True)
            notes.write_text("# v1\n")
            self.assertEqual(dirty_units(root, (notes,)), frozenset())
            staged = root / "site/.stage/content/spark/releases/4.0.0/release-notes/index.md"
            releases = root / "site/.stage/data/releases.json"
            with _cwd(root):
                invocation = parse_invocation(["watch"])
            prior = None

            def cycle(number, *dirty):
                nonlocal prior
                prior = _run_watch_cycle(
                    invocation=invocation,
                    cycle_number=number,
                    trusted_stage=prior.trusted_stage if prior else None,
                    prior_watch_roots=prior.watch_roots if prior else (root / "site",),
                    dirty_paths=dirty,
                )
                return prior.report

            self.assertTrue(cycle(1).summary.succeeded)
            self.assertIn("# v1", staged.read_text())
            notes.write_text("# v2\n")
            self.assertTrue(cycle(2, notes).summary.succeeded)
            self.assertIn("# v1", staged.read_text())
            path.write_text(json.dumps(snapshot))
            self.assertTrue(cycle(3, path).summary.succeeded)
            self.assertIn("# v2", staged.read_text())

            # Every cycle re-evaluates, so deletion fails at once and keeps the last good stage.
            notes.unlink()
            report = cycle(4, notes)
            self.assertFalse(report.summary.succeeded)
            self.assertIn("input-missing", [item.code for item in report.diagnostics])
            self.assertIn("# v2", staged.read_text())
            notes.write_text("# v3\n")
            self.assertTrue(cycle(5, notes).summary.succeeded)
            self.assertIn("# v2", staged.read_text())
            path.write_text(json.dumps(snapshot))
            self.assertTrue(cycle(6, path).summary.succeeded)
            self.assertIn("# v3", staged.read_text())

            for record in snapshot["records"]:
                record.pop("releaseNotes", None)
            path.write_text(json.dumps(snapshot))
            self.assertTrue(cycle(7, path).summary.succeeded)
            self.assertFalse(staged.exists())
            self.assertNotIn("releaseNotes", json.loads(releases.read_text())["items"][0])

    def test_site_level_snapshot_notes_edits_dirty_the_component_unit(self):
        with _workspace(with_content_file=True) as root:
            notes = write_notes(root)
            declare(root)
            self.assertEqual(dirty_units(root, (notes,)), frozenset({"component:spark"}))


if __name__ == "__main__":
    unittest.main()
