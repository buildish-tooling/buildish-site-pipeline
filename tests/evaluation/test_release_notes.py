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

"""Plan-time release-notes validation and link-check inventory."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.planning.test_release_notes import NOTES, edit_json, edit_yaml, with_notes
from tests.planning.test_version_ownership import planning
from tests.staging.test_component_publication import run
from tests.support.workspace import _workspace, _write_workspace_inputs

RELEASES = "components/runtime/docs/releases"


def write_notes(root: Path, text: str | bytes = "# Spark 4.0.0\n\nSee https://example.org/.\n", path=NOTES) -> Path:
    target = root / RELEASES / path
    target.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(text, bytes):
        target.write_bytes(text)
    else:
        target.write_text(text, encoding="utf-8")
    return target


def declare(root: Path, path=NOTES) -> None:
    def change(document):
        for record in document["records"]:
            if record["kind"] == "released":
                record["releaseNotes"] = {"path": path}

    edit_json(root / "site/provider-snapshot.json", change)


def codes(report) -> list[str]:
    return [item["code"] for item in report.get("diagnostics", [])]


def enable_link_checks(root: Path) -> None:
    edit_yaml(
        root / "site/catalog.yaml",
        lambda document: document.setdefault("validation", {}).update(
            linkChecks={"enabled": True, "mode": "directory"}
        ),
    )


class ReleaseNotesValidationTests(unittest.TestCase):
    def test_valid_notes_pass_check(self):
        with _workspace(with_content_file=True) as root:
            write_notes(root)
            declare(root)
            code, report, _ = run(root, "check")
            self.assertEqual(code, 0, report)
            self.assertFalse([item for item in codes(report) if item.startswith("release-notes")])

    def test_path_rejections(self):
        cases = (
            ("4.0.0/notes.md", "version directory"),
            ("4.0.1/notes.md", "version directory"),
        )
        for path, reason in cases:
            with self.subTest(path=path), _workspace(with_content_file=True) as root:

                def add_release(document):
                    document["artifacts"][0]["releases"].append({"version": "4.0.1", "releaseLine": "4.0"})

                edit_json(root / "site/provider-snapshot.json", add_release)
                write_notes(root, path=path)
                declare(root, path)
                code, report, _ = run(root, "check")
                self.assertNotEqual(code, 0)
                [entry] = [item for item in report["diagnostics"] if item["code"] == "release-notes-path-invalid"]
                self.assertIn(reason, entry["message"])

    def test_symlink_below_releases_and_non_regular_files_fail(self):
        with _workspace(with_content_file=True) as root:
            real = write_notes(root, path="elsewhere/4.0.0.md")
            link = root / RELEASES / "release-notes"
            link.symlink_to(real.parent, target_is_directory=True)
            declare(root)
            code, report, _ = run(root, "check")
            self.assertNotEqual(code, 0)
            self.assertIn("release-notes-path-invalid", codes(report))
        with _workspace(with_content_file=True) as root:
            (root / RELEASES / NOTES).mkdir(parents=True)
            declare(root)
            code, report, _ = run(root, "check")
            self.assertNotEqual(code, 0)
            self.assertIn("release-notes-path-invalid", codes(report))

    def test_workspace_under_symlinked_parent_passes(self):
        with tempfile.TemporaryDirectory() as tempdir:
            real = Path(tempdir) / "real"
            real.mkdir()
            alias = Path(tempdir) / "alias"
            alias.symlink_to(real, target_is_directory=True)
            _write_workspace_inputs(alias, with_content_file=True, topology="default")
            write_notes(alias)
            declare(alias)
            code, report, _ = run(alias, "check")
            self.assertEqual(code, 0, report)

    def test_content_rejections(self):
        for text in (b"\xff\xfe broken", "a\x00b", "  \n\t\n", "---\ntitle: x\n---\nbody\n", "---\n"):
            with self.subTest(text=text), _workspace(with_content_file=True) as root:
                write_notes(root, text)
                declare(root)
                code, report, _ = run(root, "check")
                self.assertNotEqual(code, 0)
                self.assertIn("release-notes-content-invalid", codes(report))

    def test_missing_file_is_input_missing_only_for_staged_contexts(self):
        with _workspace(with_content_file=True) as root:
            declare(root)
            code, report, _ = run(root, "check")
            self.assertNotEqual(code, 0)
            [entry] = [item for item in report["diagnostics"] if item["code"] == "input-missing"]
            self.assertEqual(entry["targetId"], "4.0.0")
            self.assertTrue(entry["details"]["expectedLocalPath"].endswith(NOTES))
            result = planning(root)
            self.assertTrue(result.build_plan_result.bridge.ready)
            self.assertEqual(result.build_plan_result.bridge.blocking_inputs, ())
        with _workspace(with_content_file=True) as root:
            declare(root)

            def hide(document):
                document["artifacts"][0]["releases"][0]["publicationState"] = "hidden"

            edit_json(root / "site/provider-snapshot.json", hide)
            opened = []
            original = Path.read_bytes

            def tracking(path, *args, **kwargs):
                opened.append(path)
                return original(path, *args, **kwargs)

            with mock.patch.object(Path, "read_bytes", tracking):
                code, report, _ = run(root, "check")
            self.assertEqual(code, 0, report)
            self.assertNotIn("input-missing", codes(report))
            self.assertFalse([path for path in opened if path.name == "4.0.0.md"])

    def test_shared_conflict_reports_one_dedicated_diagnostic(self):
        with _workspace(topology="two_artifacts", with_content_file=True) as root:
            edit_json(root / "site/provider-snapshot.json", with_notes)
            code, report, _ = run(root, "check")
            self.assertNotEqual(code, 0)
            self.assertEqual(codes(report).count("release-notes-shared-conflict"), 1)
            self.assertNotIn("publication-output-collision", codes(report))
            self.assertNotIn("input-missing", codes(report))

    def test_segment_equal_to_supported_locale_fails(self):
        with _workspace(with_content_file=True) as root:
            write_notes(root)
            declare(root)

            def change(document):
                component = document["components"][0]
                component["publication"]["releaseNotesSegment"] = "de"
                component["localization"] = {"defaultLocale": "en", "supportedLocales": ["en", "de"]}

            edit_yaml(root / "site/catalog.yaml", change)
            code, report, _ = run(root, "check")
            self.assertNotEqual(code, 0)
            self.assertIn("release-notes-segment-invalid", codes(report))


class ReleaseNotesLinkCheckTests(unittest.TestCase):
    def check(self, root: Path, notes: str, enabled=True):
        write_notes(root, notes)
        declare(root)
        if enabled:
            enable_link_checks(root)
        return run(root, "check")

    def missing_links(self, report):
        return [
            item for item in report["diagnostics"] if item["code"] == "page-link-target-missing"
        ]

    def test_unresolved_relative_page_link_warns(self):
        with _workspace(with_content_file=True) as root:
            code, report, _ = self.check(root, "# Notes\n\nSee [guide](../missing/).\n")
            self.assertEqual(code, 0, report)
            [entry] = self.missing_links(report)
            self.assertEqual(entry["severity"], "warning")

    def test_relative_link_into_version_docs_and_docs_link_to_notes_resolve(self):
        with _workspace(with_content_file=True) as root:
            (root / RELEASES / "4.0.0/index.md").write_text("See [notes](release-notes/).\n")
            code, report, _ = self.check(root, "# Notes\n\nBack to [docs](../).\n")
            self.assertEqual(code, 0, report)
            self.assertEqual(self.missing_links(report), [])

    def test_disabled_link_checks_report_nothing(self):
        with _workspace(with_content_file=True) as root:
            code, report, _ = self.check(root, "See [guide](../missing/).\n", enabled=False)
            self.assertEqual(code, 0, report)
            self.assertEqual(self.missing_links(report), [])


if __name__ == "__main__":
    unittest.main()
