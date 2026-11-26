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

"""Release-notes targets are resolved after dispositions for staged docs only."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import yaml

from buildish_site_pipeline.models.enums import ContextAction, RecordKind
from tests.commands.test_component_snapshots import configure_snapshot
from tests.planning.test_version_ownership import planning
from tests.support.workspace import _workspace

NOTES = "release-notes/4.0.0.md"


def edit_yaml(path: Path, change) -> None:
    document = yaml.safe_load(path.read_text())
    change(document)
    path.write_text(yaml.safe_dump(document, sort_keys=False))


def edit_json(path: Path, change) -> None:
    document = json.loads(path.read_text())
    change(document)
    path.write_text(json.dumps(document))


def released(document, version="4.0.0", artifact=None):
    return [
        record
        for record in document["records"]
        if record["kind"] == "released"
        and record["version"] == version
        and (artifact is None or record["artifactKey"] == artifact)
    ]


def with_notes(document, artifact=None):
    for record in released(document, artifact=artifact):
        record["releaseNotes"] = {"path": NOTES}


def released_contexts(result):
    return [item for item in result.selected_versions.contexts if item.kind is RecordKind.RELEASED]


class ReleaseNotesPlanningTests(unittest.TestCase):
    def test_site_level_snapshot_record_resolves_against_artifact_docs(self):
        with _workspace() as root:
            edit_json(root / "site/provider-snapshot.json", with_notes)
            result = planning(root)
            [context] = released_contexts(result)
            target = context.release_notes
            self.assertIsNotNone(target)
            self.assertEqual(target.releases_root, context.docs_root / "releases")
            self.assertEqual(
                target.source_path,
                (root / "components/runtime/docs/releases" / NOTES).resolve(),
            )
            self.assertEqual(target.segment, "release-notes")
            self.assertEqual(target.title, "Release Notes for 4.0.0")
            self.assertEqual(result.release_notes_conflicts, ())
            [desired] = [item for item in result.desired_versions if item.kind is RecordKind.RELEASED]
            self.assertEqual(desired.release_notes, target)

    def test_component_snapshot_in_docs_branch_resolves_the_same_way(self):
        with _workspace() as root:
            path, snapshot = configure_snapshot(root)
            with_notes(snapshot)
            path.write_text(json.dumps(snapshot))
            [context] = released_contexts(planning(root))
            self.assertIsNotNone(context.release_notes)
            self.assertEqual(
                context.release_notes.source_path,
                (root / "components/runtime/docs/releases" / NOTES).resolve(),
            )

    def test_no_target_without_declaration_or_for_unstaged_contexts(self):
        with _workspace() as root:
            [context] = released_contexts(planning(root))
            self.assertIsNone(context.release_notes)
        for state, behavior, action in (
            ("hidden", None, ContextAction.OMIT),
            ("withdrawn", "notice", ContextAction.NOTICE),
            ("tombstoned", None, ContextAction.OMIT),
        ):
            with self.subTest(state=state), _workspace() as root:

                def change(document, state=state, behavior=behavior):
                    with_notes(document)
                    release = document["artifacts"][0]["releases"][0]
                    release["publicationState"] = state
                    if behavior:
                        release["withdrawalBehavior"] = behavior

                edit_json(root / "site/provider-snapshot.json", change)
                result = planning(root)
                desired = [item for item in result.desired_versions if item.kind is RecordKind.RELEASED]
                self.assertEqual([item.action for item in desired], [action])
                self.assertIsNone(desired[0].release_notes)
                self.assertTrue(all(item.release_notes is None for item in released_contexts(result)))

    def test_site_excluded_version_has_no_context(self):
        with _workspace() as root:
            edit_json(root / "site/provider-snapshot.json", with_notes)

            def exclude(document):
                artifact = document["components"][0]["artifacts"][0]
                artifact["publicationSelection"]["releases"] = {"mode": "none"}

            edit_yaml(root / "site/catalog.yaml", exclude)
            self.assertEqual(released_contexts(planning(root)), [])

    def test_title_modes_display_version_and_segment_override(self):
        cases = (
            (None, None, "Release Notes for 4.0.0"),
            ("version-only", None, "4.0.0"),
            ("version-only", "v4.0.0", "v4.0.0"),
            ("release-notes", "v4.0.0", "Release Notes for v4.0.0"),
            ("component-name", None, "spark 4.0.0"),
        )
        for mode, display_version, title in cases:
            with self.subTest(mode=mode, display_version=display_version), _workspace() as root:

                def change_snapshot(document, display_version=display_version):
                    with_notes(document)
                    if display_version:
                        released(document)[0]["displayVersion"] = display_version

                def change_catalog(document, mode=mode):
                    publication = document["components"][0]["publication"]
                    publication["releaseNotesSegment"] = "notes"
                    if mode:
                        publication["releaseNotesTitle"] = mode

                edit_json(root / "site/provider-snapshot.json", change_snapshot)
                edit_yaml(root / "site/catalog.yaml", change_catalog)
                [context] = released_contexts(planning(root))
                self.assertIsNotNone(context.release_notes)
                self.assertEqual(context.release_notes.title, title)
                self.assertEqual(context.release_notes.segment, "notes")

    def test_component_name_title_prefers_catalog_then_metadata_display_name(self):
        for catalog_name, metadata_name, title in (
            ("Apache Spark", "Spark Metadata", "Apache Spark 4.0.0"),
            (None, "Spark Metadata", "Spark Metadata 4.0.0"),
        ):
            with self.subTest(catalog_name=catalog_name), _workspace() as root:

                def change_catalog(document, catalog_name=catalog_name):
                    component = document["components"][0]
                    component["publication"]["releaseNotesTitle"] = "component-name"
                    if catalog_name:
                        component["displayName"] = catalog_name

                edit_json(root / "site/provider-snapshot.json", with_notes)
                edit_yaml(root / "site/catalog.yaml", change_catalog)
                edit_yaml(
                    root / "components/runtime/site/component.yaml",
                    lambda document, name=metadata_name: document["component"].update(displayName=name),
                )
                [context] = released_contexts(planning(root))
                self.assertIsNotNone(context.release_notes)
                self.assertEqual(context.release_notes.title, title)

    def test_chosen_record_wins_with_several_matching_records(self):
        with _workspace() as root:

            def change(document):
                [record] = released(document)
                duplicate = dict(record, provider="mirror", releaseNotes={"path": "release-notes/mirror.md"})
                record["releaseNotes"] = {"path": NOTES}
                document["providers"].append(
                    {"key": "mirror", "type": "mirror", "fetchedAt": "2026-04-03T00:00:00Z"}
                )
                document["records"].append(duplicate)

            edit_json(root / "site/provider-snapshot.json", change)
            [context] = released_contexts(planning(root))
            self.assertIsNotNone(context.provider_record)
            self.assertIsNotNone(context.release_notes)
            self.assertEqual(context.release_notes.relative_path, context.provider_record.release_notes_path)

    def test_shared_route_conflict_yields_no_targets(self):
        with _workspace(topology="two_artifacts") as root:
            edit_json(root / "site/provider-snapshot.json", with_notes)
            result = planning(root)
            self.assertTrue(all(item.release_notes is None for item in released_contexts(result)))
            [conflict] = result.release_notes_conflicts
            self.assertEqual(
                (conflict.component_slug, conflict.version, conflict.artifact_keys),
                ("spark", "4.0.0", ("api", "runtime")),
            )

    def test_one_declaring_artifact_or_namespaced_routing_has_no_conflict(self):
        with _workspace(topology="two_artifacts") as root:
            edit_json(
                root / "site/provider-snapshot.json",
                lambda document: with_notes(document, artifact="api"),
            )
            result = planning(root)
            self.assertEqual(result.release_notes_conflicts, ())
            self.assertEqual(
                {item.artifact_key: item.release_notes is not None for item in released_contexts(result)},
                {"api": True, "runtime": False},
            )
        with _workspace(topology="two_artifacts") as root:
            edit_json(root / "site/provider-snapshot.json", with_notes)
            edit_yaml(
                root / "site/catalog.yaml",
                lambda document: document["components"][0]["publication"].update(artifactRouting="namespaced"),
            )
            result = planning(root)
            self.assertEqual(result.release_notes_conflicts, ())
            self.assertTrue(all(item.release_notes is not None for item in released_contexts(result)))


if __name__ == "__main__":
    unittest.main()
