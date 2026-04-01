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

"""Navigation contracts for the user-facing documentation entry points."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


_GETTING_STARTED_INDEX = Path("site/pages/getting-started/_index.md")
_ARCHITECTURE_ROOT = Path("site/pages/architecture")
_ARCHITECTURE_INDEX = _ARCHITECTURE_ROOT / "_index.md"
_ARCHITECTURE_OVERVIEW = _ARCHITECTURE_ROOT / "architecture-overview.md"
_HOW_TO_ROOT = Path("site/pages/how-to")
_HOW_TO_INDEX = _HOW_TO_ROOT / "_index.md"
_MARKDOWN_LINK_PATTERN = re.compile(r"\[[^]]+\]\(([^)]+)\)")


class UserFacingDocNavigationTests(unittest.TestCase):
    """Keep the main reader journeys complete and renderer-safe."""

    def test_getting_started_leads_from_problem_to_first_success_to_adoption(self) -> None:
        page_text = _GETTING_STARTED_INDEX.read_text(encoding="utf-8")
        ordered_markers = (
            "Documentation sites often need",
            "```mermaid",
            "## Reach a first successful stage",
            "## Choose your adoption path",
        )

        positions = [page_text.index(marker) for marker in ordered_markers]

        self.assertEqual(positions, sorted(positions))
        self.assertEqual(page_text.count("```mermaid"), 1)
        self.assertIn("[Create a tiny site](../how-to/create-a-tiny-site/)", page_text)
        self.assertIn(
            "[Inspect the staged output and routes](../how-to/inspect-staged-output-and-routes/)",
            page_text,
        )
        self.assertIn(
            "[Unreleased development reference](../development/reference/)",
            page_text,
        )

    def test_architecture_index_links_every_architecture_page(self) -> None:
        index_text = _ARCHITECTURE_INDEX.read_text(encoding="utf-8")

        for page_path in sorted(_ARCHITECTURE_ROOT.glob("*.md")):
            if page_path == _ARCHITECTURE_INDEX:
                continue
            with self.subTest(page=page_path.name):
                self.assertIn(f"({page_path.stem}/)", index_text)

        self.assertIn("[Getting Started](../getting-started/)", index_text)
        self.assertIn("unreleased development", index_text)
        self.assertIn("(../development/reference/)", index_text)

    def test_architecture_overview_keeps_distinct_deep_design_diagrams(self) -> None:
        overview_text = _ARCHITECTURE_OVERVIEW.read_text(encoding="utf-8")

        self.assertEqual(overview_text.count("```mermaid"), 2)
        self.assertNotIn("## Progressive complexity by site weight", overview_text)
        self.assertIn(
            "[Getting Started adoption paths](../../getting-started/)",
            overview_text,
        )
        self.assertIn("For unreleased development contract details", overview_text)

    def test_how_to_index_links_every_guide_and_labels_status_pages(self) -> None:
        index_text = _HOW_TO_INDEX.read_text(encoding="utf-8")

        for page_path in sorted(_HOW_TO_ROOT.glob("*.md")):
            if page_path == _HOW_TO_INDEX:
                continue
            with self.subTest(page=page_path.name):
                self.assertIn(f"({page_path.stem}/)", index_text)

        self.assertEqual(index_text.count("planned-guide status page, not"), 2)
        self.assertEqual(index_text.count("a turnkey recipe"), 2)

    def test_entry_point_links_use_relative_pretty_routes(self) -> None:
        for page_path in (
            _GETTING_STARTED_INDEX,
            _ARCHITECTURE_INDEX,
            _ARCHITECTURE_OVERVIEW,
            _HOW_TO_INDEX,
        ):
            page_text = page_path.read_text(encoding="utf-8")
            for target in _MARKDOWN_LINK_PATTERN.findall(page_text):
                with self.subTest(page=page_path.as_posix(), target=target):
                    self.assertFalse(target.startswith("/"))
                    self.assertNotIn(".md", target)
                    self.assertNotIn("site/pages/", target)
                    self.assertNotEqual(target, "docs/")
                    self.assertFalse(target.startswith("docs/"))
                    self.assertNotIn("/docs/", target)


if __name__ == "__main__":
    unittest.main()
