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

"""Focused coverage for staged internal page-link validation."""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace

from apache_buildish_site_pipeline.evaluation.collector import DiagnosticCollector
from apache_buildish_site_pipeline.evaluation.link_references import extract_link_references
from apache_buildish_site_pipeline.evaluation.staged_links import validate_staged_links
from apache_buildish_site_pipeline.evaluation.types import InventoryPage, PageInventory
from apache_buildish_site_pipeline.models.enums import LinkCheckMode
from apache_buildish_site_pipeline.planning.types import ResolvedLinkCheckPolicy


class StagedLinksTests(unittest.TestCase):
    def test_directory_mode_warns_for_missing_relative_page_links(self) -> None:
        collector = DiagnosticCollector()
        planning = self._planning(
            mode=LinkCheckMode.DIRECTORY,
            check_root_absolute=False,
        )
        inventory = PageInventory(
            pages=(
                self._page(
                    "index.md",
                    "[Guide](guide/) [Missing](missing/) [Asset](./logo.png)",
                ),
                self._page("guide.md", "Guide body"),
            )
        )

        validate_staged_links(
            planning=planning,
            page_inventory=inventory,
            collector=collector,
        )

        diagnostics = collector.build()
        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(diagnostics[0].details["resolvedPath"], "/missing")
        self.assertEqual(diagnostics[0].code, "page-link-target-missing")
        self.assertEqual(diagnostics[0].details["sourceLine"], 1)
        self.assertEqual(diagnostics[0].details["occurrenceIndex"], 1)
        self.assertEqual(diagnostics[0].details["sourceColumn"], 27)
        self.assertFalse(diagnostics[0].details["approximateLineColumn"])
        self.assertEqual(
            diagnostics[0].message,
            "index.md:1:27: internal page link 'missing/' resolves to missing staged page /missing",
        )

    def test_file_html_mode_resolves_html_links(self) -> None:
        collector = DiagnosticCollector()
        planning = self._planning(
            mode=LinkCheckMode.FILE_HTML,
            check_root_absolute=False,
        )
        inventory = PageInventory(
            pages=(
                self._page("index.md", "[Guide](guide.html) [Missing](missing.html)"),
                self._page("guide.md", "Guide body"),
            )
        )

        validate_staged_links(
            planning=planning,
            page_inventory=inventory,
            collector=collector,
        )

        diagnostics = collector.build()
        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(diagnostics[0].details["resolvedPath"], "/missing.html")
        self.assertEqual(diagnostics[0].details["mode"], "file-html")

    def test_markdown_html_links_outside_code_blocks_are_checked(self) -> None:
        collector = DiagnosticCollector()
        planning = self._planning(
            mode=LinkCheckMode.DIRECTORY,
            check_root_absolute=False,
        )
        inventory = PageInventory(
            pages=(
                self._page(
                    "index.md",
                    '<a href="guide/">Guide</a> <a href="missing/">Missing</a>',
                ),
                self._page("guide.md", "Guide body"),
            )
        )

        validate_staged_links(
            planning=planning,
            page_inventory=inventory,
            collector=collector,
        )

        diagnostics = collector.build()
        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(diagnostics[0].details["resolvedPath"], "/missing")
        self.assertEqual(diagnostics[0].details["sourceColumn"], 37)

    def test_markdown_ignores_html_links_inside_code_blocks_and_inline_code(self) -> None:
        collector = DiagnosticCollector()
        planning = self._planning(
            mode=LinkCheckMode.DIRECTORY,
            check_root_absolute=False,
        )
        inventory = PageInventory(
            pages=(
                self._page(
                    "index.md",
                    """
Literal shortcode example:

```go-html-template
<li><a href="{{ index $entry \"path\" }}">{{ index $entry "title" }}</a></li>
```

Inline example: `<a href="missing/">Missing</a>`
""",
                ),
            )
        )

        validate_staged_links(
            planning=planning,
            page_inventory=inventory,
            collector=collector,
        )

        diagnostics = collector.build()
        self.assertEqual(diagnostics, ())

    def test_root_absolute_links_require_declared_internal_prefixes(self) -> None:
        collector = DiagnosticCollector()
        planning = self._planning(
            mode=LinkCheckMode.DIRECTORY,
            check_root_absolute=True,
            internal_prefixes=("/components/",),
        )
        inventory = PageInventory(
            pages=(
                self._page(
                    "index.md",
                    "[Spark](/components/spark/guide) [Ignored](/assets/logo.png) [Missing](/components/missing/guide)",
                    base_public_path="/components/spark",
                ),
                self._page(
                    "guide.md",
                    "Guide body",
                    base_public_path="/components/spark",
                ),
            )
        )

        validate_staged_links(
            planning=planning,
            page_inventory=inventory,
            collector=collector,
        )

        diagnostics = collector.build()
        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(diagnostics[0].details["resolvedPath"], "/components/missing/guide")

    def test_reports_each_missing_occurrence_instead_of_deduplicating_by_target(self) -> None:
        collector = DiagnosticCollector()
        planning = self._planning(
            mode=LinkCheckMode.DIRECTORY,
            check_root_absolute=False,
        )
        inventory = PageInventory(
            pages=(
                self._page(
                    "index.md",
                    "[Missing](missing/)\nAgain [Missing](missing/)",
                ),
            )
        )

        validate_staged_links(
            planning=planning,
            page_inventory=inventory,
            collector=collector,
        )

        diagnostics = collector.build()
        self.assertEqual(len(diagnostics), 2)
        self.assertEqual([entry.details["sourceLine"] for entry in diagnostics], [1, 2])
        self.assertEqual([entry.details["occurrenceIndex"] for entry in diagnostics], [0, 1])

    def test_reference_style_links_can_fall_back_to_approximate_line_only(self) -> None:
        collector = DiagnosticCollector()
        planning = self._planning(
            mode=LinkCheckMode.DIRECTORY,
            check_root_absolute=False,
        )
        inventory = PageInventory(
            pages=(
                self._page(
                    "index.md",
                    "[Missing][missing]\n\n[missing]: missing/\n",
                ),
            )
        )

        validate_staged_links(
            planning=planning,
            page_inventory=inventory,
            collector=collector,
        )

        diagnostics = collector.build()
        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(diagnostics[0].details["sourceLine"], 1)
        self.assertIsNone(diagnostics[0].details["sourceColumn"])
        self.assertTrue(diagnostics[0].details["approximateLineColumn"])
        self.assertEqual(
            diagnostics[0].message,
            "index.md:~1: internal page link 'missing/' resolves to missing staged page /missing",
        )

    def test_approximate_same_line_occurrences_are_not_collapsed(self) -> None:
        collector = DiagnosticCollector()
        planning = self._planning(
            mode=LinkCheckMode.DIRECTORY,
            check_root_absolute=False,
        )
        inventory = PageInventory(
            pages=(
                self._page(
                    "index.md",
                    "[First][missing] [Second][missing]\n\n[missing]: missing/\n",
                ),
            )
        )

        validate_staged_links(
            planning=planning,
            page_inventory=inventory,
            collector=collector,
        )

        diagnostics = collector.build()
        self.assertEqual(len(diagnostics), 2)
        self.assertEqual([entry.details["occurrenceIndex"] for entry in diagnostics], [0, 1])
        self.assertEqual([entry.details["sourceLine"] for entry in diagnostics], [1, 1])
        self.assertEqual([entry.details["sourceColumn"] for entry in diagnostics], [None, None])

    def test_duplicate_inventory_views_of_same_occurrence_are_collapsed(self) -> None:
        collector = DiagnosticCollector()
        planning = self._planning(
            mode=LinkCheckMode.DIRECTORY,
            check_root_absolute=False,
        )
        page = self._page("index.md", "[Missing](missing/)")
        inventory = PageInventory(pages=(page, page))

        validate_staged_links(
            planning=planning,
            page_inventory=inventory,
            collector=collector,
        )

        diagnostics = collector.build()
        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(diagnostics[0].details["occurrenceIndex"], 0)

    def test_section_index_pages_resolve_relative_targets_from_directory_root(self) -> None:
        collector = DiagnosticCollector()
        planning = self._planning(
            mode=LinkCheckMode.DIRECTORY,
            check_root_absolute=False,
        )
        inventory = PageInventory(
            pages=(
                self._page("guide/_index.md", "[Concepts](../concepts/)"),
                self._page("concepts/_index.md", "Section body"),
            )
        )

        validate_staged_links(
            planning=planning,
            page_inventory=inventory,
            collector=collector,
        )

        self.assertEqual(collector.build(), ())

    def test_file_html_mode_treats_section_index_pages_as_index_html(self) -> None:
        collector = DiagnosticCollector()
        planning = self._planning(
            mode=LinkCheckMode.FILE_HTML,
            check_root_absolute=False,
        )
        inventory = PageInventory(
            pages=(
                self._page("guide/_index.md", "[Concepts](../concepts/index.html)"),
                self._page("concepts/_index.md", "Section body"),
            )
        )

        validate_staged_links(
            planning=planning,
            page_inventory=inventory,
            collector=collector,
        )

        self.assertEqual(collector.build(), ())

    def test_asciidoc_link_syntax_is_checked(self) -> None:
        collector = DiagnosticCollector()
        planning = self._planning(mode=LinkCheckMode.FILE_HTML, check_root_absolute=False)
        inventory = PageInventory(
            pages=(
                self._page("guide.adoc", "link:missing.html[Missing]", suffix=".adoc"),
            )
        )

        validate_staged_links(
            planning=planning,
            page_inventory=inventory,
            collector=collector,
        )

        diagnostics = collector.build()
        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(diagnostics[0].details["resolvedPath"], "/missing.html")

    @staticmethod
    def _planning(
        *,
        mode: LinkCheckMode,
        check_root_absolute: bool,
        internal_prefixes: tuple[str, ...] = (),
    ) -> SimpleNamespace:
        return SimpleNamespace(
            site=SimpleNamespace(
                link_checks=ResolvedLinkCheckPolicy(
                    enabled=True,
                    mode=mode,
                    check_root_absolute=check_root_absolute,
                    internal_prefixes=internal_prefixes,
                )
            )
        )

    @staticmethod
    def _page(
        relative_path: str,
        body_text: str,
        *,
        base_public_path: str = "/",
        component_slug: str | None = "spark",
        artifact_key: str | None = "runtime",
        suffix: str | None = None,
    ) -> InventoryPage:
        source_path = Path(relative_path)
        if suffix is not None:
            source_path = source_path.with_suffix(suffix)
        return InventoryPage(
            input_id="development:spark:runtime",
            component_slug=component_slug,
            artifact_key=artifact_key,
            relative_path=source_path.as_posix(),
            routed_relative_path=source_path.as_posix(),
            source_path=source_path,
            base_public_path=base_public_path,
            translation_key=None,
            extracted_links=extract_link_references(source_path=source_path, text=body_text),
        )