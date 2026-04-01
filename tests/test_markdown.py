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

from apache_buildish_site_pipeline.markdown import extract_title_and_summary
from apache_buildish_site_pipeline.markdown import humanized_stem
from apache_buildish_site_pipeline.markdown import normalize_markdown_doc
from apache_buildish_site_pipeline.markdown import split_paragraphs
from apache_buildish_site_pipeline.markdown import update_markdown_front_matter
import yaml


class MarkdownNormalizationTest(unittest.TestCase):
    def test_extract_title_and_summary_ignores_leading_html_comments(self) -> None:
        title, summary = extract_title_and_summary(
            "<!-- keep hidden -->\n# Overview\n\nShort summary.\n\nMore detail.\n",
            "Fallback",
        )

        self.assertEqual("Overview", title)
        self.assertEqual("Short summary.", summary)

    def test_update_markdown_front_matter_rejects_non_mapping_front_matter(self) -> None:
        markdown = "---\n[]\n---\n\nBody\n"

        with self.assertRaisesRegex(ValueError, "Expected markdown front matter to be a mapping"):
            update_markdown_front_matter(markdown, title="Body")

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


class MarkdownUtilityTest(unittest.TestCase):
    def test_humanized_stem_converts_slug_like_names(self) -> None:
        self.assertEqual("Getting Started Guide", humanized_stem(Path("getting-started_guide.md")))

    def test_split_paragraphs_normalizes_line_wrapping(self) -> None:
        self.assertEqual(
            ["One two", "Three four"],
            split_paragraphs(" One\n two \n\n Three\nfour\n"),
        )