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

"""Generated release-notes pages: staging, claims, provenance and emitted metadata."""

from __future__ import annotations

import collections
import json
import os
import unittest
from pathlib import Path
from unittest import mock

import frontmatter

from buildish_site_pipeline.cli.errors import StageIntegrityError
from buildish_site_pipeline.staging.ownership import build_owned_units
from buildish_site_pipeline.staging.page_provenance import (
    build_page_source_index,
    page_source_provenance,
)
from buildish_site_pipeline.staging import aggregates, coordinator, destination_claims
from buildish_site_pipeline.staging.spec_builder import build_context_wire
from buildish_site_pipeline.staging.worker_protocol import StagedPageContributionWire
from tests.evaluation.test_release_notes import RELEASES, codes, declare, write_notes
from tests.planning.test_release_notes import NOTES, edit_json, edit_yaml, with_notes
from tests.planning.test_version_ownership import planning
from tests.staging.test_component_publication import run
from tests.support.workspace import _workspace

NOTES_ROUTE = "/spark/releases/4.0.0/release-notes"


def stage(root: Path) -> Path:
    return root / "site/.stage"


def data(root: Path, name: str) -> list[dict]:
    return json.loads((stage(root) / "data" / name).read_text())["items"]


def build(test: unittest.TestCase, root: Path) -> dict:
    code, report, errors = run(root)
    test.assertEqual(code, 0, (report, errors))
    return report


def notes_pages(root: Path) -> list[Path]:
    return sorted(stage(root).glob("content/**/release-notes/index.md"))


class ReleaseNotesStagingTests(unittest.TestCase):
    def test_staged_page_releases_entry_and_content_index(self):
        with _workspace(with_content_file=True) as root:
            write_notes(root, "# Spark 4.0.0\n\nFixed things.\n")
            declare(root)
            build(self, root)
            [page] = notes_pages(root)
            self.assertEqual(page.relative_to(stage(root)).as_posix(), "content/spark/releases/4.0.0/release-notes/index.md")
            post = frontmatter.load(page)
            self.assertEqual(post["title"], "Release Notes for 4.0.0")
            self.assertEqual(post["pipeline"]["page"]["kind"], "release-notes")
            self.assertEqual(post["pipeline"]["page"]["section"], "release")
            self.assertNotIn("source", post["pipeline"])
            self.assertIn("# Spark 4.0.0\n\nFixed things.", post.content)
            [release] = data(root, "releases.json")
            self.assertEqual(
                release["releaseNotes"],
                {"path": NOTES_ROUTE, "url": f"https://docs.example.org{NOTES_ROUTE}"},
            )
            entries = {item["path"]: item for item in data(root, "content-index.json")}
            self.assertEqual(entries[NOTES_ROUTE]["pageKind"], "release-notes")
            self.assertEqual(entries[NOTES_ROUTE]["url"], release["releaseNotes"]["url"])
            self.assertNotIn("source", entries[NOTES_ROUTE])
            self.assertFalse([path for path in entries if path.startswith("/spark/development/") and "release-notes" in path])

    def test_no_declaration_no_page_and_no_availability(self):
        with _workspace(with_content_file=True) as root:
            write_notes(root)
            build(self, root)
            self.assertEqual(notes_pages(root), [])
            self.assertNotIn("releaseNotes", data(root, "releases.json")[0])

    def test_withdrawn_notice_and_hidden_versions_stage_no_notes(self):
        for state, behavior in (("withdrawn", "notice"), ("hidden", None), ("tombstoned", None)):
            with self.subTest(state=state), _workspace(with_content_file=True) as root:
                write_notes(root)
                declare(root)

                def change(document, state=state, behavior=behavior):
                    release = document["artifacts"][0]["releases"][0]
                    release["publicationState"] = state
                    if behavior:
                        release["withdrawalBehavior"] = behavior

                edit_json(root / "site/provider-snapshot.json", change)
                build(self, root)
                self.assertEqual(notes_pages(root), [])
                for release in data(root, "releases.json") if (stage(root) / "data/releases.json").exists() else ():
                    self.assertNotIn("releaseNotes", release)

    def test_segment_override_and_title_mode(self):
        with _workspace(with_content_file=True) as root:
            write_notes(root)
            declare(root)

            def change(document):
                document["components"][0]["publication"].update(
                    releaseNotesSegment="notes", releaseNotesTitle="version-only"
                )

            edit_yaml(root / "site/catalog.yaml", change)
            build(self, root)
            [page] = sorted(stage(root).glob("content/**/notes/index.md"))
            self.assertEqual(frontmatter.load(page)["title"], "4.0.0")
            self.assertEqual(data(root, "releases.json")[0]["releaseNotes"]["path"], "/spark/releases/4.0.0/notes")

    def test_docs_or_assets_at_or_beneath_the_segment_conflict(self):
        for path in ("release-notes.md", "release-notes/old.md", "release-notes/diagram.png", "release-notes/_index.md"):
            with self.subTest(path=path), _workspace(with_content_file=True) as root:
                write_notes(root, path="notes/4.0.0.md")
                declare(root, "notes/4.0.0.md")
                target = root / RELEASES / "4.0.0" / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("# clash\n")
                code, report, _ = run(root, "check")
                self.assertNotEqual(code, 0)
                self.assertIn("publication-output-collision", codes(report))
        with _workspace(with_content_file=True) as root:
            write_notes(root)
            declare(root)
            (root / RELEASES / "4.0.0/release-notes-overview.md").write_text("# sibling\n")
            code, report, _ = run(root, "check")
            self.assertEqual(code, 0, report)

    def test_shared_routing_one_declaring_artifact_owns_the_page(self):
        with _workspace(topology="two_artifacts", with_content_file=True) as root:
            notes = root / "components/api/docs/releases" / NOTES
            notes.parent.mkdir(parents=True)
            notes.write_text("# API 4.0.0\n")
            edit_json(root / "site/provider-snapshot.json", lambda document: with_notes(document, artifact="api"))
            build(self, root)
            self.assertEqual(len(notes_pages(root)), 1)
            rows = {item["artifactKey"]: item for item in data(root, "releases.json")}
            self.assertIn("releaseNotes", rows["api"])
            self.assertNotIn("releaseNotes", rows["runtime"])

    def test_namespaced_routing_places_notes_under_each_artifact(self):
        with _workspace(topology="two_artifacts", with_content_file=True) as root:
            for component in ("runtime/docs/runtime", "api/docs"):
                notes = root / "components" / component / "releases" / NOTES
                notes.parent.mkdir(parents=True)
                notes.write_text("# Notes\n")
            edit_json(root / "site/provider-snapshot.json", with_notes)
            edit_yaml(
                root / "site/catalog.yaml",
                lambda document: document["components"][0]["publication"].update(artifactRouting="namespaced"),
            )
            build(self, root)
            paths = sorted(item["releaseNotes"]["path"] for item in data(root, "releases.json"))
            self.assertEqual(len(set(paths)), 2)
            self.assertEqual(len(notes_pages(root)), 2)

    def test_localized_site_stages_one_default_locale_page(self):
        with _workspace(with_content_file=True) as root:
            write_notes(root)
            declare(root)
            edit_yaml(
                root / "site/catalog.yaml",
                lambda document: document["components"][0].update(
                    localization={"defaultLocale": "en", "supportedLocales": ["en", "de"]}
                ),
            )
            build(self, root)
            self.assertEqual(len(notes_pages(root)), 1)
            [entry] = [item for item in data(root, "content-index.json") if item["pageKind"] == "release-notes"]
            self.assertEqual(entry.get("locale"), "en")

    def test_forged_source_path_never_yields_provenance(self):
        with _workspace(with_content_file=True) as root:
            write_notes(root)
            declare(root)
            plan = planning(root).build_plan_result.candidate
            self.assertIsNotNone(plan)
            sources = build_page_source_index(plan, build_owned_units(plan))["component:spark"]
            for page_kind in ("release-notes", "release-page"):
                forged = StagedPageContributionWire(
                    stage_relative_path="content/spark/releases/4.0.0/release-notes/index.md",
                    component_slug="spark",
                    artifact_key="runtime",
                    section="release",
                    page_kind=page_kind,
                    public_path=NOTES_ROUTE,
                    public_url=f"https://docs.example.org{NOTES_ROUTE}",
                    component_path="/spark/",
                    component_url="https://docs.example.org/spark/",
                    origin_key="docs",
                    source_path=f"components/runtime/docs/releases/{NOTES}",
                    canonical_url=f"https://docs.example.org{NOTES_ROUTE}",
                )
                with self.subTest(page_kind=page_kind):
                    self.assertIsNone(
                        page_source_provenance(build_plan=plan, sources=sources, contribution=forged)
                    )


    def test_each_notes_file_is_read_once_and_claim_checks_stay_linear(self):
        versions = tuple(f"4.0.{patch}" for patch in range(12))
        with _workspace(with_content_file=True) as root:

            def change(document):
                base = next(item for item in document["records"] if item["kind"] == "released")
                document["records"] = [item for item in document["records"] if item["kind"] != "released"]
                for version in versions:
                    document["records"].append(
                        dict(base, version=version, tag=f"v{version}", releaseNotes={"path": f"release-notes/{version}.md"})
                    )
                artifact = document["artifacts"][0]
                artifact["releases"] = [{"version": version, "releaseLine": "4.0"} for version in versions]
                artifact["releaseLines"][0]["latest"] = versions[-1]

            edit_json(root / "site/provider-snapshot.json", change)
            edit_yaml(
                root / "site/catalog.yaml",
                lambda document: document["components"][0]["artifacts"][0]["publicationSelection"].update(
                    releases={"mode": "allKnown"}
                ),
            )
            for version in versions:
                for page in ("index.md", "guide.md", "reference/index.md", "reference/api.md"):
                    (root / RELEASES / version / page).parent.mkdir(parents=True, exist_ok=True)
                    (root / RELEASES / version / page).write_text("docs\n")
                write_notes(root, f"# {version}\n", path=f"release-notes/{version}.md")
            reads: collections.Counter[str] = collections.Counter()
            scans: collections.Counter[str] = collections.Counter()
            read_bytes, scandir = Path.read_bytes, os.scandir

            def counting_read(path, *args, **kwargs):
                if "release-notes" in path.parts:
                    reads[path.name] += 1
                return read_bytes(path, *args, **kwargs)

            source_directory = (root / RELEASES / "release-notes").resolve()

            def counting_scandir(path=".", *args, **kwargs):
                if isinstance(path, (str, os.PathLike)) and Path(path).resolve() == source_directory:
                    scans[str(path)] += 1
                return scandir(path, *args, **kwargs)

            normalize = destination_claims.normalize_public_path
            validate = destination_claims.validate_destination_claims
            normalized = 0
            ratios: list[float] = []

            def counting_normalize(*args, **kwargs):
                nonlocal normalized
                normalized += 1
                return normalize(*args, **kwargs)

            def counting_validate(claims):
                nonlocal normalized
                claims = tuple(claims)
                normalized = 0
                validate(claims)
                ratios.append(normalized / len(claims))

            with (
                mock.patch.object(Path, "read_bytes", counting_read),
                mock.patch("os.scandir", counting_scandir),
                mock.patch.object(destination_claims, "normalize_public_path", counting_normalize),
                mock.patch.object(destination_claims, "validate_destination_claims", counting_validate),
                mock.patch.object(coordinator, "validate_destination_claims", counting_validate),
                mock.patch.object(aggregates, "validate_destination_claims", counting_validate),
            ):
                build(self, root)
            # Plan-time validation reads every file once; workers get the validated text.
            self.assertEqual(dict(reads), {f"{version}.md": 1 for version in versions})
            self.assertEqual(scans, collections.Counter())
            self.assertEqual(len(notes_pages(root)), len(versions))
            # Route normalization per claim stays constant as versions with notes are added.
            self.assertGreaterEqual(len(ratios), 2)
            self.assertLessEqual(max(ratios), 3, ratios)

    def test_staged_page_uses_the_validated_text_even_if_the_file_changes(self):
        with _workspace(with_content_file=True) as root:
            notes = write_notes(root, "# Checked\n")
            declare(root)
            original = coordinator.run_build

            def edit_then_build(request):
                notes.write_text("# Unchecked [link](https://example.invalid/)\n")
                return original(request)

            with mock.patch.object(coordinator, "run_build", edit_then_build):
                build(self, root)
            [page] = notes_pages(root)
            self.assertEqual(frontmatter.load(page).content, "# Checked")

    def test_spec_builder_rejects_notes_missing_from_the_validated_set(self):
        with _workspace(with_content_file=True) as root:
            write_notes(root)
            declare(root)
            plan = planning(root).build_plan_result.candidate
            self.assertIsNotNone(plan)
            layout = mock.Mock(next_stage_root=root / "stage")
            [unit] = [unit for unit in build_owned_units(plan) if unit.unit_id == "component:spark"]
            [owned] = [item for item in unit.contexts if item.context.release_notes is not None]
            component = next(item for item in plan.site.components if item.slug == "spark")
            with self.assertRaises(StageIntegrityError):
                build_context_wire(component=component, owned_context=owned, layout=layout, release_notes_texts={})
            wire = build_context_wire(
                component=component,
                owned_context=owned,
                layout=layout,
                release_notes_texts={owned.context.release_notes.source_path: "# Notes\n"},
            )
            self.assertEqual(wire.release_notes_text, "# Notes\n")

if __name__ == "__main__":
    unittest.main()
