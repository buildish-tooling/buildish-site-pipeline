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

"""Direct coverage for localization and page-scan helper modules."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import mock

from apache_buildish_site_pipeline.evaluation.collector import DiagnosticCollector
from apache_buildish_site_pipeline.evaluation.localization import validate_localization
from apache_buildish_site_pipeline.evaluation.page_scan import validate_page_scan
from apache_buildish_site_pipeline.evaluation.types import PageScanResult, ScannedPage
from apache_buildish_site_pipeline.models.enums import (
    MaterializationInputKind,
    MaterializationStatus,
    RouteMode,
)
from apache_buildish_site_pipeline.planning.types import (
    InputReadiness,
    LocalInputIdentity,
    MaterializationStatusReason,
    ResolvedLocalInput,
)


class LocalizationAndPageScanTests(unittest.TestCase):
    def test_validate_localization_reports_invalid_policy_combinations(self) -> None:
        collector = DiagnosticCollector()
        planning = SimpleNamespace(
            site=SimpleNamespace(
                components=(
                    self._component(
                        "spark",
                        default_locale=None,
                        supported_locales=None,
                        fallback_locale=None,
                        route_mode=RouteMode.PREFIX_ALL,
                    ),
                    self._component(
                        "flink",
                        default_locale="en",
                        supported_locales=("de", "fr"),
                        fallback_locale="es",
                        route_mode=RouteMode.NONE,
                    ),
                )
            )
        )

        validate_localization(
            planning=planning,
            page_scan=PageScanResult(pages=()),
            collector=collector,
        )

        self.assertEqual(
            [entry.code for entry in collector.build()],
            [
                "localization-policy-invalid",
                "localization-policy-invalid",
                "localization-policy-invalid",
                "localization-policy-invalid",
            ],
        )

    def test_validate_localization_reports_unresolved_duplicate_and_conflicting_translations(self) -> None:
        collector = DiagnosticCollector()
        planning = SimpleNamespace(
            site=SimpleNamespace(components=(self._component("spark"),))
        )
        page_scan = PageScanResult(
            pages=(
                self._page("guide.md", "guide"),
                self._page("en/guide.md", "guide"),
                self._page("en/guide-copy.md", "guide"),
                self._page("de/guide.md", "handbuch"),
                self._page("fr/uebersicht.md", "guide"),
            )
        )

        validate_localization(
            planning=planning,
            page_scan=page_scan,
            collector=collector,
        )

        self.assertEqual(
            {entry.code for entry in collector.build()},
            {
                "translation-locale-unresolved",
                "translation-locale-duplicate",
                "translation-linkage-conflict",
                "translation-route-inconsistent",
            },
        )

    def test_validate_localization_ignores_non_prefixed_components_and_incomplete_page_records(self) -> None:
        collector = DiagnosticCollector()
        planning = SimpleNamespace(
            site=SimpleNamespace(
                components=(
                    self._component("spark", route_mode=RouteMode.NONE),
                    self._component("flink"),
                )
            )
        )
        page_scan = PageScanResult(
            pages=(
                self._page("guide.md", "guide", component_slug="spark"),
                self._page("en/guide.md", "guide", component_slug=None),
                self._page("en/guide.md", "guide", artifact_key=None),
            )
        )

        validate_localization(
            planning=planning,
            page_scan=page_scan,
            collector=collector,
        )

        self.assertEqual(collector.build(), ())

    def test_validate_page_scan_scans_only_present_page_inputs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            docs_root = root / "docs"
            docs_root.mkdir()
            (docs_root / "Guide.MDX").write_text("body\n", encoding="utf-8")
            (docs_root / "Install.adoc").write_text(
                "---\ntranslationKey: install\n---\n= Install\n",
                encoding="utf-8",
            )
            (docs_root / "Reference.asciidoc").write_text("= Reference\n", encoding="utf-8")
            (docs_root / "ignored.txt").write_text("body\n", encoding="utf-8")
            assets_root = root / "assets"
            assets_root.mkdir()
            (assets_root / "asset.md").write_text("body\n", encoding="utf-8")

            scanned = validate_page_scan(
                self._planning(
                    self._local_input(docs_root),
                    self._local_input(
                        assets_root,
                        input_kind=MaterializationInputKind.SITE_ASSETS,
                    ),
                    self._local_input(
                        root / "missing",
                        readiness=InputReadiness(
                            status=MaterializationStatus.MISSING,
                            reason=MaterializationStatusReason.PATH_MISSING,
                        ),
                    ),
                ),
                DiagnosticCollector(),
            )

        self.assertEqual(
            [(page.relative_path, page.translation_key) for page in scanned.pages],
            [
                ("Guide.MDX", None),
                ("Install.adoc", "install"),
                ("Reference.asciidoc", None),
            ],
        )
        self.assertEqual(scanned.pages[0].routed_relative_path, "Guide.MDX")
        self.assertEqual(scanned.pages[0].base_public_path, "/")
        self.assertEqual(scanned.pages[0].body_text, "body\n")

    def test_validate_page_scan_reports_root_escape_and_read_failures(self) -> None:
        collector = DiagnosticCollector()
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            docs_root = root / "docs"
            docs_root.mkdir()
            outside = root / "outside.md"
            outside.write_text("outside\n", encoding="utf-8")
            (docs_root / "escape.md").symlink_to(outside)
            (docs_root / "broken.md").write_bytes(b"\xff")

            scanned = validate_page_scan(
                self._planning(self._local_input(docs_root)),
                collector,
            )

        self.assertEqual(tuple(page.relative_path for page in scanned.pages), ("broken.md",))
        self.assertEqual(
            {entry.code for entry in collector.build()},
            {"page-path-outside-root", "page-read-failed"},
        )

    def test_validate_page_scan_reports_front_matter_failures_and_reserved_namespace(self) -> None:
        collector = DiagnosticCollector()
        with TemporaryDirectory() as temp_dir:
            docs_root = Path(temp_dir) / "docs"
            docs_root.mkdir()
            (docs_root / "unterminated.md").write_text("---\nkey: value\n", encoding="utf-8")
            (docs_root / "malformed.md").write_text("---\nkey: [\n---\n", encoding="utf-8")
            (docs_root / "reserved.md").write_text("---\npipeline: {}\n---\nbody\n", encoding="utf-8")
            (docs_root / "translation.md").write_text(
                "---\ntranslationKey: []\n---\nbody\n",
                encoding="utf-8",
            )

            scanned = validate_page_scan(
                self._planning(self._local_input(docs_root)),
                collector,
            )

        self.assertEqual(len(scanned.pages), 4)
        self.assertEqual(
            [entry.code for entry in collector.build()],
            [
                "page-front-matter-invalid",
                "page-front-matter-invalid",
                "page-front-matter-invalid",
                "page-reserved-namespace",
            ],
        )
        translation_page = next(page for page in scanned.pages if page.relative_path == "translation.md")
        self.assertIsNone(translation_page.translation_key)

    def test_validate_page_scan_skips_duplicate_real_directories(self) -> None:
        collector = DiagnosticCollector()
        with TemporaryDirectory() as temp_dir:
            docs_root = Path(temp_dir) / "docs"
            docs_root.mkdir()
            real_dir = docs_root / "real"
            real_dir.mkdir()
            (docs_root / "alias").symlink_to(real_dir, target_is_directory=True)

            scanned = validate_page_scan(
                self._planning(self._local_input(docs_root)),
                collector,
            )

        self.assertEqual(scanned.pages, ())
        self.assertEqual(collector.build(), ())

    def test_validate_page_scan_reports_directory_scan_failures(self) -> None:
        collector = DiagnosticCollector()
        with TemporaryDirectory() as temp_dir:
            docs_root = Path(temp_dir) / "docs"
            docs_root.mkdir()
            original_iterdir = type(docs_root).iterdir

            def _iterdir(path: Path):
                if path == docs_root:
                    raise OSError("permission denied")
                return original_iterdir(path)

            with mock.patch.object(type(docs_root), "iterdir", autospec=True, side_effect=_iterdir):
                scanned = validate_page_scan(
                    self._planning(self._local_input(docs_root)),
                    collector,
                )

        self.assertEqual(scanned.pages, ())
        self.assertEqual([entry.code for entry in collector.build()], ["page-read-failed"])

    def test_validate_page_scan_accepts_empty_front_matter_blocks(self) -> None:
        collector = DiagnosticCollector()
        with TemporaryDirectory() as temp_dir:
            docs_root = Path(temp_dir) / "docs"
            docs_root.mkdir()
            (docs_root / "empty.md").write_text("---\n\n---\nbody\n", encoding="utf-8")

            scanned = validate_page_scan(
                self._planning(self._local_input(docs_root)),
                collector,
            )

        self.assertEqual(tuple(page.relative_path for page in scanned.pages), ("empty.md",))
        self.assertEqual(collector.build(), ())

    def test_validate_page_scan_includes_component_pages_roots_in_shared_inventory(self) -> None:
        collector = DiagnosticCollector()
        with TemporaryDirectory() as temp_dir:
            pages_root = Path(temp_dir) / "pages"
            pages_root.mkdir()
            (pages_root / "guide.md").write_text("guide body\n", encoding="utf-8")

            scanned = validate_page_scan(
                self._planning(
                    components=(
                        self._component("spark", pages_root=pages_root, component_path="/spark"),
                    )
                ),
                collector,
            )

        self.assertEqual(len(scanned.pages), 1)
        self.assertEqual(scanned.pages[0].input_id, "componentPages:spark")
        self.assertEqual(scanned.pages[0].base_public_path, "/spark")
        self.assertEqual(scanned.pages[0].body_text, "guide body\n")

    @staticmethod
    def _component(
        slug: str,
        *,
        default_locale: str | None = "en",
        supported_locales: tuple[str, ...] | None = ("en", "de", "fr"),
        fallback_locale: str | None = None,
        route_mode: RouteMode | None = RouteMode.PREFIX_ALL,
        pages_root: Path | None = None,
        component_path: str = "/spark",
    ) -> SimpleNamespace:
        return SimpleNamespace(
            slug=slug,
            pages_root=pages_root,
            publication=SimpleNamespace(component_path=component_path),
            localization=SimpleNamespace(
                default_locale=default_locale,
                supported_locales=supported_locales,
                fallback_locale=fallback_locale,
                route_mode=route_mode,
            ),
        )

    @staticmethod
    def _page(
        relative_path: str,
        translation_key: str | None,
        *,
        input_id: str = "development:spark:runtime",
        component_slug: str | None = "spark",
        artifact_key: str | None = "runtime",
        routed_relative_path: str | None = None,
        base_public_path: str = "/",
        body_text: str | None = None,
    ) -> ScannedPage:
        return ScannedPage(
            input_id=input_id,
            component_slug=component_slug,
            artifact_key=artifact_key,
            relative_path=relative_path,
            routed_relative_path=routed_relative_path or relative_path,
            source_path=Path(relative_path),
            base_public_path=base_public_path,
            translation_key=translation_key,
            body_text=body_text,
        )

    @staticmethod
    def _planning(
        *local_inputs: ResolvedLocalInput,
        components: tuple[SimpleNamespace, ...] = (),
        selected_contexts: tuple[SimpleNamespace, ...] = (),
    ) -> SimpleNamespace:
        return SimpleNamespace(
            local_inputs=local_inputs,
            site=SimpleNamespace(components=components),
            selected_versions=SimpleNamespace(contexts=selected_contexts),
        )

    @staticmethod
    def _local_input(
        expected_local_path: Path,
        *,
        input_kind: MaterializationInputKind = MaterializationInputKind.DEVELOPMENT,
        readiness: InputReadiness | None = None,
    ) -> ResolvedLocalInput:
        return ResolvedLocalInput(
            identity=LocalInputIdentity(
                source_key="runtime",
                input_kind=input_kind,
                component_slug="spark",
                artifact_key="runtime",
            ),
            declared_root=expected_local_path.parent,
            expected_local_path=expected_local_path,
            provenance="component:spark",
            readiness=readiness or InputReadiness(status=MaterializationStatus.PRESENT),
            watch_eligible=True,
        )
