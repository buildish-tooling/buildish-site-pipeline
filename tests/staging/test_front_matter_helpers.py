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

"""Direct coverage for front-matter staging helpers."""

from __future__ import annotations

from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from apache_buildish_site_pipeline.cli.errors import StageIntegrityError
from apache_buildish_site_pipeline.models.authored.site_catalog import (
    ArtifactLifecycleConfig,
    ExactReleaseConfig,
    ReleaseLineConfig,
)
from apache_buildish_site_pipeline.models.enums import RecordKind, RouteMode
from apache_buildish_site_pipeline.models.emitted.staged_front_matter import (
    TranslationLinkSummary,
)
from apache_buildish_site_pipeline.planning.types import ResolvedLocalizationPolicy
from apache_buildish_site_pipeline.staging.front_matter import (
    _artifact_lifecycle,
    _exact_release_config,
    _join_public_path,
    _provider_provenance,
    _release_line_config,
    _release_line_summaries,
    authored_link_title,
    authored_title,
    build_component_front_matter,
    build_page_front_matter,
    build_translation_link,
    detect_locale,
    extract_page_translation_key,
    is_page_path,
    public_page_path,
    public_page_url,
    stage_authored_page,
)
from apache_buildish_site_pipeline.staging.worker_protocol import StagedPageContributionWire


class FrontMatterHelpersTests(unittest.TestCase):
    def _contribution(self, **overrides) -> StagedPageContributionWire:
        payload = {
            "stage_relative_path": "content/spark/guide.md",
            "component_slug": "spark",
            "artifact_key": "runtime",
            "section": "docs",
            "page_kind": "docs-page",
            "public_path": "/spark/guide",
            "public_url": "https://docs.example.org/spark/guide",
            "component_path": "/spark/",
            "component_url": "https://docs.example.org/spark/",
            "origin_key": "docs",
            "source_path": "components/runtime/docs/guide.md",
            "canonical_url": "https://docs.example.org/spark/guide",
        }
        payload.update(overrides)
        return StagedPageContributionWire(**payload)

    def test_is_page_path_recognizes_supported_extensions_case_insensitively(self) -> None:
        self.assertTrue(is_page_path(Path("guide.MD")))
        self.assertTrue(is_page_path(Path("guide.htm")))
        self.assertFalse(is_page_path(Path("logo.svg")))

    def test_extract_page_translation_key_accepts_both_metadata_spellings(self) -> None:
        self.assertEqual(
            extract_page_translation_key({"translationKey": "guide.install"}),
            "guide.install",
        )
        self.assertEqual(
            extract_page_translation_key({"translation_key": "guide.upgrade"}),
            "guide.upgrade",
        )

    def test_authored_title_and_link_title_trim_strings(self) -> None:
        self.assertEqual(authored_title({"title": "  Guide  "}), "Guide")
        self.assertEqual(authored_title({"linkTitle": "  Quickstart  "}), "Quickstart")
        self.assertEqual(authored_link_title({"link_title": "  Install  "}), "Install")
        self.assertIsNone(authored_link_title({"title": "Guide"}))

    def test_detect_locale_strips_supported_locale_prefixes(self) -> None:
        locale, is_default, relative = detect_locale(
            Path("fr/guide/install.md"),
            ResolvedLocalizationPolicy(
                default_locale="en",
                supported_locales=("en", "fr"),
                fallback_locale=None,
                route_mode=None,
            ),
        )

        self.assertEqual(locale, "fr")
        self.assertFalse(is_default)
        self.assertEqual(relative, Path("guide/install.md"))

    def test_detect_locale_falls_back_to_default_locale_without_prefix(self) -> None:
        locale, is_default, relative = detect_locale(
            Path("guide/install.md"),
            ResolvedLocalizationPolicy(
                default_locale="en",
                supported_locales=("en", "fr"),
                fallback_locale=None,
                route_mode=None,
            ),
        )

        self.assertEqual((locale, is_default, relative), ("en", True, Path("guide/install.md")))

    def test_detect_locale_keeps_relative_path_for_non_path_routing(self) -> None:
        locale, is_default, relative = detect_locale(
            Path("guide/install.md"),
            ResolvedLocalizationPolicy(
                default_locale="en",
                supported_locales=("en", "fr"),
                fallback_locale=None,
                route_mode=RouteMode.NONE,
            ),
        )

        self.assertEqual((locale, is_default, relative), ("en", True, Path("guide/install.md")))

    def test_public_page_path_and_url_normalize_index_and_route_base(self) -> None:
        public_path = public_page_path("/spark/docs/", Path("guide/index.md"))

        self.assertEqual(public_path, "/spark/docs/guide")
        self.assertEqual(
            public_page_url(
                "https://docs.example.org/spark/docs/",
                public_path,
                route_base_path="/spark/docs/",
            ),
            "https://docs.example.org/spark/docs/guide",
        )

    def test_build_component_front_matter_ignores_selected_versions_from_other_components(self) -> None:
        lifecycle = ArtifactLifecycleConfig(
            latest_stable="4.0.0",
            release_lines=[ReleaseLineConfig(key="4.0", latest="4.0.0")],
            releases=[ExactReleaseConfig(version="4.0.0", release_line="4.0")],
        )
        component = SimpleNamespace(
            slug="spark",
            authored=SimpleNamespace(display_name="Spark"),
            artifacts=(
                SimpleNamespace(
                    key="runtime",
                    authored=SimpleNamespace(display_name="Runtime"),
                    lifecycle=lifecycle,
                ),
            ),
            publication=SimpleNamespace(
                origin=SimpleNamespace(
                    key="docs",
                    base_url="https://docs.example.org",
                    hostname="docs.example.org",
                ),
                component_path="/spark/",
                development_path="/spark/main/",
                docs_path="/spark/docs/",
                assets_path="/spark/assets/",
                component_url="https://docs.example.org/spark/",
                development_url="https://docs.example.org/spark/main/",
                docs_url="https://docs.example.org/spark/docs/",
                assets_url="https://docs.example.org/spark/assets/",
            ),
        )

        front_matter = build_component_front_matter(
            component=component,
            selected_versions=(
                SimpleNamespace(component_slug="flink", artifact_key="runtime"),
            ),
        )

        self.assertEqual(front_matter.slug, "spark")
        self.assertIsNone(front_matter.artifacts[0].release_lines[0].head_ref)

    def test_build_page_front_matter_populates_alternate_urls_and_provider_provenance(self) -> None:
        page = build_page_front_matter(
            contribution=self._contribution(
                locale="en",
                default_locale=True,
                translation_key="guide.install",
                version_context={
                    "kind": RecordKind.RELEASED,
                    "label": "4.0.0",
                    "path": "/spark/releases/4.0.0",
                    "url": "https://docs.example.org/spark/releases/4.0.0",
                    "docs_path": "/spark/releases/4.0.0",
                    "docs_url": "https://docs.example.org/spark/releases/4.0.0",
                    "provider": {
                        "key": "github",
                        "externalId": "123",
                        "externalUrl": "https://example.invalid/releases/123",
                    },
                },
            ),
            translations=[
                TranslationLinkSummary(
                    locale="en",
                    path="/spark/guide",
                    url="https://docs.example.org/spark/guide",
                    title="Guide",
                ),
                TranslationLinkSummary(
                    locale="de",
                    path="/de/spark/guide",
                    url="https://docs.example.org/de/spark/guide",
                    title="Anleitung",
                ),
                TranslationLinkSummary(
                    locale="fr",
                    path="/fr/spark/guide",
                    url="https://docs.example.org/fr/spark/guide",
                    title="Guide FR",
                ),
            ],
        )

        self.assertEqual(
            page.alternate_urls,
            [
                "https://docs.example.org/de/spark/guide",
                "https://docs.example.org/fr/spark/guide",
            ],
        )
        self.assertEqual(page.provider.key, "github")
        self.assertEqual(page.provider.external_id, "123")

    def test_build_page_front_matter_requires_public_url(self) -> None:
        with self.assertRaisesRegex(StageIntegrityError, "missing a public URL"):
            build_page_front_matter(
                contribution=self._contribution(public_url=None, canonical_url=None),
                translations=None,
            )

    def test_build_translation_link_requires_locale_and_public_url(self) -> None:
        with self.assertRaisesRegex(ValueError, "require a locale"):
            build_translation_link(self._contribution(locale=None))

        with self.assertRaisesRegex(ValueError, "require a public URL"):
            build_translation_link(self._contribution(locale="fr", public_url=None))

        link = build_translation_link(self._contribution(locale="fr", title="Guide FR"))

        self.assertEqual(link.locale, "fr")
        self.assertEqual(link.url, "https://docs.example.org/spark/guide")
        self.assertEqual(link.title, "Guide FR")

    def test_public_page_helpers_cover_non_markdown_paths_root_paths_and_missing_base_urls(self) -> None:
        self.assertEqual(public_page_path("/spark/assets/", Path("images/logo.svg")), "/spark/assets/images/logo.svg")
        self.assertEqual(public_page_path("/spark/docs/", Path("guide/install.md")), "/spark/docs/guide/install")
        self.assertIsNone(public_page_url(None, "/spark/guide"))
        self.assertEqual(
            public_page_url(
                "https://docs.example.org/spark/docs/",
                "/spark/other/guide",
                route_base_path="/spark/docs/",
            ),
            "https://docs.example.org/spark/docs/spark/other/guide",
        )
        self.assertEqual(_join_public_path("/", "guide"), "/guide")

    def test_stage_authored_page_rejects_reserved_pipeline_namespace(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            source_path = Path(tempdir) / "guide.md"
            destination_path = Path(tempdir) / "staged.md"
            source_path.write_text(
                "---\npipeline:\n  page: {}\ntitle: Guide\n---\nhello\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(StageIntegrityError, "reserved 'pipeline' namespace"):
                stage_authored_page(
                    source_path=source_path,
                    destination_path=destination_path,
                    namespace=None,
                )

    def test_release_and_provider_helper_functions_return_none_for_unknown_inputs(self) -> None:
        artifact = SimpleNamespace(key="runtime", lifecycle=None)
        component = SimpleNamespace(artifacts=(artifact,))
        lifecycle = ArtifactLifecycleConfig(
            release_lines=[ReleaseLineConfig(key="4.0", latest="4.0.0")],
            releases=[ExactReleaseConfig(version="4.0.0", release_line="4.0")],
        )

        self.assertIsNone(_artifact_lifecycle(component, artifact_key="missing"))
        self.assertEqual(_release_line_summaries(artifact, []), [])
        self.assertIsNone(_release_line_config(lifecycle, release_line_key="missing"))
        self.assertIsNone(_exact_release_config(lifecycle, version="9.9.9"))
        self.assertIsNone(_provider_provenance(self._contribution(version_context={"provider": "github"})))
        self.assertIsNone(_provider_provenance(self._contribution(version_context={"provider": {"key": 7}})))
