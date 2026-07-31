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

"""Contract tests for commands and schema names copied from documentation."""

from __future__ import annotations

import json
import re
import shlex
import unittest
from pathlib import Path

import yaml

from buildish_site_pipeline.cli import parse_invocation
from buildish_site_pipeline.cli.contract import WatchEventFormat, WatchInvocation
from buildish_site_pipeline.docs.schema_export import schema_exports
from buildish_site_pipeline.models import (
    ContentIndexEntry,
    PipelineFrontMatterNamespace,
)


_SCHEMA_GUIDE = Path("site/pages/how-to/use-json-schema-for-yaml-authoring.md")
_HUGO_GUIDE = Path("site/pages/how-to/integrate-with-hugo.md")
_ENHANCED_FRONT_MATTER_CONCEPT = Path(
    "site/pages/concepts/pipeline-enhanced-front-matter.md"
)
_STAGED_OUTPUT_CONCEPT = Path("site/pages/concepts/staged-output-and-consumers.md")
_STATIC_PROVENANCE_DOCS = (
    Path("site/pages/concepts/_index.md"),
    _ENHANCED_FRONT_MATTER_CONCEPT,
    _STAGED_OUTPUT_CONCEPT,
    Path("site/pages/how-to/inspect-staged-output-and-routes.md"),
    _SCHEMA_GUIDE,
)
_SCHEMA_BASE_URL = "https://buildish.org/components/site-pipeline/schemas/"
_SCHEMA_FILENAME_PATTERN = re.compile(r"([a-z0-9-]+-v[0-9]+\.schema\.json)")


def _marked_code_block(path: Path, marker: str, language: str) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(
        rf"<!-- test:{re.escape(marker)} -->\s*```{language}\n(.*?)\n```",
        text,
        flags=re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"Missing {marker!r} {language} example in {path}")
    return match.group(1)


class DocumentationContractTests(unittest.TestCase):
    """Keep hand-authored integration examples aligned with code contracts."""

    def test_schema_guide_uses_exporter_owned_filenames(self) -> None:
        guide_text = _SCHEMA_GUIDE.read_text(encoding="utf-8")
        exports_by_path = {
            export.documentation.file_path: export.filename
            for export in schema_exports()
            if export.documentation is not None
            and export.documentation.file_path is not None
        }
        documented_filenames = set(_SCHEMA_FILENAME_PATTERN.findall(guide_text))
        exported_filenames = {export.filename for export in schema_exports()}

        self.assertLessEqual(documented_filenames, exported_filenames)
        for file_path in (
            "site/catalog.yaml",
            "site/component.yaml",
            "site/provider-snapshot.json",
        ):
            expected_url = _SCHEMA_BASE_URL + exports_by_path[file_path]
            self.assertIn(f"`{file_path}`: `{expected_url}`", guide_text)

        self.assertIn("does not publish those files yet", guide_text)
        self.assertIn("not currently downloadable", guide_text)

    def test_repository_component_schema_hint_resolves_to_current_export(self) -> None:
        component_path = Path("site/component.yaml")
        first_line = component_path.read_text(encoding="utf-8").splitlines()[0]
        hint = first_line.removeprefix("# yaml-language-server: $schema=")
        component_export = next(
            export
            for export in schema_exports()
            if export.documentation is not None
            and export.documentation.file_path == "site/component.yaml"
        )
        resolved_hint = component_path.parent / hint

        self.assertNotIn("://", hint)
        self.assertEqual(resolved_hint.name, component_export.filename)
        self.assertTrue(resolved_hint.is_file())

    def test_documented_yaml_modelines_are_comments_relative_to_authored_files(self) -> None:
        examples = {
            "schema-catalog": (
                Path("/workspace/buildish-site/site/catalog.yaml"),
                Path("/workspace/buildish-site/site/schemas/catalog-v1.schema.json"),
            ),
            "schema-component": (
                Path("/workspace/components/runtime/site/component.yaml"),
                Path(
                    "/workspace/components/runtime/site/schemas/"
                    "component-v1.schema.json"
                ),
            ),
        }

        for marker, (authored_file, expected_schema) in examples.items():
            with self.subTest(marker=marker):
                example = _marked_code_block(_SCHEMA_GUIDE, marker, "yaml")
                first_line = example.splitlines()[0]
                hint = first_line.removeprefix(
                    "# yaml-language-server: $schema="
                )
                parsed_document = yaml.safe_load(example)

                self.assertNotEqual(hint, first_line)
                self.assertNotIn("$schema", parsed_document)
                self.assertEqual(authored_file.parent / hint, expected_schema)

    def test_enhanced_front_matter_example_matches_emitted_contract(self) -> None:
        example = yaml.safe_load(
            _marked_code_block(
                _ENHANCED_FRONT_MATTER_CONCEPT,
                "enhanced-front-matter",
                "yaml",
            )
        )
        namespace = PipelineFrontMatterNamespace.model_validate(
            example["pipeline"],
            by_alias=True,
            by_name=False,
        )

        self.assertEqual(example["title"], "Install the runtime")
        self.assertEqual(namespace.page.source.key, "runtime")
        self.assertEqual(
            namespace.page.source.path,
            "docs/releases/4.0.0/getting-started.md",
        )

    def test_content_index_example_matches_emitted_contract(self) -> None:
        example = json.loads(
            _marked_code_block(
                _STAGED_OUTPUT_CONCEPT,
                "content-index-entry",
                "json",
            )
        )
        entry = ContentIndexEntry.model_validate(
            example,
            by_alias=True,
            by_name=False,
        )

        self.assertEqual(entry.source.key, "runtime")
        self.assertEqual(entry.source.path, "docs/releases/4.0.0/index.md")

    def test_provenance_docs_use_current_shape_and_label_development_links(self) -> None:
        for path in _STATIC_PROVENANCE_DOCS:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn('"sourcePath"', text)
                for label, target in re.findall(r"\[([^]]+)]\(([^)]+)\)", text):
                    if "/development/" in target:
                        self.assertIn("unreleased development", label.lower())

    def test_documented_hugo_watch_command_is_a_valid_cli_invocation(self) -> None:
        guide_text = _HUGO_GUIDE.read_text(encoding="utf-8")
        command_match = re.search(
            r"^\s*(site-pipeline watch .+?)\s+&\s+\\$",
            guide_text,
            flags=re.MULTILINE,
        )

        if command_match is None:
            self.fail("Hugo guide must contain the background watch command")
        documented_command = command_match.group(1).replace(
            '"$$events_file"',
            "events.jsonl",
        )
        command_parts = shlex.split(documented_command)
        invocation = parse_invocation(command_parts[1:])

        if not isinstance(invocation, WatchInvocation):
            self.fail("Documented watch command must parse as a watch invocation")
        event_request = invocation.unstable_event_request
        if event_request is None:
            self.fail("Documented watch command must enable unstable events")
        self.assertEqual(
            event_request.event_format,
            WatchEventFormat.JSONL,
        )
        self.assertEqual(
            event_request.output_path,
            Path.cwd() / "events.jsonl",
        )


if __name__ == "__main__":
    unittest.main()
