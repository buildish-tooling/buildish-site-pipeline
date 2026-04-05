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
import unittest

from apache_buildish_site_pipeline.planning.types import ResolvedLocalizationPolicy
from apache_buildish_site_pipeline.staging.front_matter import (
    authored_link_title,
    authored_title,
    detect_locale,
    extract_page_translation_key,
    is_page_path,
    public_page_path,
    public_page_url,
)


class FrontMatterHelpersTests(unittest.TestCase):
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
