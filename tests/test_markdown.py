# Copyright 2026 The Apache Software Foundation
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

"""Tests for markdown normalization helpers."""

from __future__ import annotations

from pathlib import Path
import unittest

from mistletoe import Document

from apache_buildish_site_pipeline.markdown import _analyze_markdown
from apache_buildish_site_pipeline.markdown import _remove_blocks
from apache_buildish_site_pipeline.markdown import extract_title_and_summary
from apache_buildish_site_pipeline.markdown import humanized_stem
from apache_buildish_site_pipeline.markdown import normalize_markdown_doc
from apache_buildish_site_pipeline.markdown import split_paragraphs
from apache_buildish_site_pipeline.markdown import update_markdown_front_matter
import yaml


class MarkdownNormalizationTest(unittest.TestCase):
    def test_extract_title_and_summary_preserves_inline_markdown_tokens(self) -> None:
        title, summary = extract_title_and_summary(
            (
                "# `Code` *Em* **Strong** ~~Gone~~ [Link](https://example.invalid) "
                "<https://autolink.invalid> ![Alt](image.png)\n\n"
                "Summary first line  \nnext line.\n"
            ),
            "Fallback",
        )

        self.assertIn("`Code`", title)
        self.assertIn("*Em*", title)
        self.assertIn("**Strong**", title)
        self.assertIn("~~Gone~~", title)
        self.assertIn("[Link](https://example.invalid)", title)
        self.assertIn("<https://autolink.invalid>", title)
        self.assertIn("![Alt](image.png)", title)
        self.assertEqual("Summary first line next line.", summary)

    def test_extract_title_and_summary_ignores_leading_html_comments(self) -> None:
        title, summary = extract_title_and_summary(
            "<!-- keep hidden -->\n# Overview\n\nShort summary.\n\nMore detail.\n",
            "Fallback",
        )

        self.assertEqual("Overview", title)
        self.assertEqual("Short summary.", summary)

    def test_extract_title_and_summary_falls_back_for_empty_and_non_heading_documents(self) -> None:
        for markdown in ("", "Overview first.\n\nStill body.\n"):
            with self.subTest(markdown=markdown):
                title, summary = extract_title_and_summary(markdown, "Fallback")

                self.assertEqual("Fallback", title)
                self.assertEqual("", summary)

    def test_extract_title_and_summary_stops_before_second_level_heading(self) -> None:
        title, summary = extract_title_and_summary(
            "# Overview\n\n## Docs\n\nBody paragraph.\n",
            "Fallback",
        )

        self.assertEqual("Overview", title)
        self.assertEqual("", summary)

    def test_extract_title_and_summary_skips_non_paragraph_blocks_before_summary(self) -> None:
        title, summary = extract_title_and_summary(
            "# Overview\n\n- bullet\n\nSummary paragraph.\n",
            "Fallback",
        )

        self.assertEqual("Overview", title)
        self.assertEqual("Summary paragraph.", summary)

    def test_extract_title_and_summary_returns_empty_summary_when_scan_exhausts(self) -> None:
        title, summary = extract_title_and_summary(
            "# Overview\n\n```text\nno paragraph summary here\n```\n",
            "Fallback",
        )

        self.assertEqual("Overview", title)
        self.assertEqual("", summary)

    def test_update_markdown_front_matter_rejects_non_mapping_front_matter(self) -> None:
        markdown = "---\n[]\n---\n\nBody\n"

        with self.assertRaisesRegex(ValueError, "Expected markdown front matter to be a mapping"):
            update_markdown_front_matter(markdown, title="Body")

    def test_update_markdown_front_matter_accepts_empty_front_matter_block(self) -> None:
        updated = update_markdown_front_matter("---\n---\n\nBody\n", title="Body")

        self.assertEqual("Body", yaml.safe_load(updated.split("---", 2)[1])["title"])

    def test_normalize_markdown_doc_promotes_title_and_summary_into_front_matter(self) -> None:
        markdown = "# Overview\n\nLanding page.\n\n## Docs\n\nMore detail.\n"

        normalized, title, summary = normalize_markdown_doc(
            markdown,
            "Fallback",
            kind="docs-home",
        )
        front_matter = yaml.safe_load(normalized.split("---", 2)[1])
        body = normalized.split("---", 2)[2]

        self.assertEqual("Overview", title)
        self.assertEqual("Landing page.", summary)
        self.assertEqual("Overview", front_matter["title"])
        self.assertEqual("Landing page.", front_matter["description"])
        self.assertEqual("docs-home", front_matter["kind"])
        self.assertNotIn("# Overview", body)
        self.assertNotIn("Landing page.", body)
        self.assertIn("## Docs", body)

    def test_normalize_markdown_doc_uses_existing_title_and_description_fallback(self) -> None:
        markdown = (
            "---\n"
            "title: Existing title\n"
            "description: Existing summary\n"
            "---\n\n"
            "Overview without a heading.\n\n"
            "## Docs\n\n"
            "More detail.\n"
        )

        normalized, title, summary = normalize_markdown_doc(markdown, "Fallback")
        front_matter = yaml.safe_load(normalized.split("---", 2)[1])
        body = normalized.split("---", 2)[2]

        self.assertEqual("Existing title", title)
        self.assertEqual("Existing summary", summary)
        self.assertEqual("Existing title", front_matter["title"])
        self.assertEqual("Existing summary", front_matter["description"])
        self.assertIn("Overview without a heading.", body)
        self.assertIn("## Docs", body)

    def test_normalize_markdown_doc_removes_empty_description_when_no_summary_exists(self) -> None:
        normalized, title, summary = normalize_markdown_doc(
            "---\ndescription: '   '\n---\n\n## Docs\n\nBody.\n",
            "Fallback",
        )
        front_matter = yaml.safe_load(normalized.split("---", 2)[1])

        self.assertEqual("Fallback", title)
        self.assertEqual("", summary)
        self.assertNotIn("description", front_matter)
        self.assertIn("## Docs", normalized)

    def test_remove_blocks_handles_empty_indexes_and_missing_line_numbers(self) -> None:
        markdown = "# Title\n\nBody.\n"
        blocks = list(Document(markdown).children or ())

        self.assertEqual(markdown, _remove_blocks(markdown, blocks, []))

        class _BlockWithoutLineNumber:
            line_number = None

        self.assertEqual(markdown, _remove_blocks(markdown, [_BlockWithoutLineNumber()], [0]))

    def test_remove_blocks_skips_non_numeric_following_block_line_numbers(self) -> None:
        markdown = "# Title\n\nSummary.\n\nTail.\n"

        class _Block:
            def __init__(self, line_number: int | None) -> None:
                self.line_number = line_number

        trimmed = _remove_blocks(markdown, [_Block(1), _Block(None), _Block(5)], [0])

        self.assertEqual("Tail.\n", trimmed)

    def test_analyze_markdown_marks_first_body_paragraph_summary(self) -> None:
        blocks = list(Document("# Title\n\nSummary.\n\nMore detail.\n").children or ())

        analysis = _analyze_markdown(blocks, "Fallback")

        self.assertTrue(analysis.summary_is_first_body_block)


class MarkdownUtilityTest(unittest.TestCase):
    def test_humanized_stem_converts_slug_like_names(self) -> None:
        self.assertEqual("Getting Started Guide", humanized_stem(Path("getting-started_guide.md")))

    def test_split_paragraphs_normalizes_line_wrapping(self) -> None:
        self.assertEqual(
            ["One two", "Three four"],
            split_paragraphs(" One\n two \n\n Three\nfour\n"),
        )