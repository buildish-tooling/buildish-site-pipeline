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

"""Tests for staged front matter and page metadata models."""

from __future__ import annotations

import json
import unittest

from pydantic import ValidationError

from apache_buildish_site_pipeline.models.authored.page_metadata import (
    PageTranslationMetadata,
)
from apache_buildish_site_pipeline.models.emitted.staged_front_matter import (
    PipelineFrontMatterNamespace,
    PipelinePageFrontMatter,
    ResolvedOrigin,
    VersionContext,
)


class StagedFrontMatterTests(unittest.TestCase):
    """Validate staged front matter output models."""

    def test_serializes_front_matter_in_camel_case(self) -> None:
        front_matter = PipelineFrontMatterNamespace.model_validate(
            {
                "component": {
                    "slug": "spark",
                    "publication": {
                        "origin": {
                            "key": "docs",
                            "baseUrl": "https://docs.example.org",
                            "hostname": "docs.example.org",
                        },
                        "paths": {
                            "component": "/spark/",
                            "development": "/spark/latest/",
                            "docs": "/spark/latest/",
                            "assets": "/spark/assets/",
                        },
                        "urls": {
                            "component": "https://docs.example.org/spark/",
                            "development": "https://docs.example.org/spark/latest/",
                            "docs": "https://docs.example.org/spark/latest/",
                            "assets": "https://docs.example.org/spark/assets/",
                        },
                    },
                },
                "page": {
                    "kind": "docsPage",
                    "artifactKey": "runtime",
                    "path": "/spark/latest/sql/",
                    "url": "https://docs.example.org/spark/latest/sql/",
                    "canonicalUrl": "https://docs.example.org/spark/latest/sql/",
                    "alternateUrls": ["https://docs.example.org/spark/archive/sql/"],
                    "translationKey": "runtime-sql-overview",
                    "translations": [
                        {
                            "locale": "de",
                            "url": "https://docs.example.org/de/spark/latest/sql/",
                        },
                    ],
                    "componentPath": "/spark/",
                    "componentUrl": "https://docs.example.org/spark/",
                    "version": {
                        "kind": "released",
                        "label": "4.0.0",
                        "path": "/spark/releases/4.0.0/",
                        "url": "https://docs.example.org/spark/releases/4.0.0/",
                        "docsPath": "/spark/releases/4.0.0/docs/",
                        "docsUrl": "https://docs.example.org/spark/releases/4.0.0/docs/",
                        "publicationState": "published",
                        "releaseLine": {"key": "4.x", "ancestors": ["3.x"]},
                    },
                },
            },
            by_alias=True,
            by_name=False,
        )

        payload = front_matter.model_dump(by_alias=True, exclude_none=True)
        self.assertIn("canonicalUrl", payload["page"])
        self.assertIn("componentUrl", payload["page"])
        self.assertNotIn("component_url", json.dumps(payload))

    def test_rejects_mismatched_origin_hostname(self) -> None:
        with self.assertRaises(ValidationError):
            ResolvedOrigin.model_validate(
                {
                    "key": "docs",
                    "baseUrl": "https://docs.example.org",
                    "hostname": "downloads.example.org",
                },
                by_alias=True,
                by_name=False,
            )

    def test_rejects_duplicate_translation_locales_and_alternate_urls(self) -> None:
        with self.assertRaises(ValidationError):
            PipelinePageFrontMatter.model_validate(
                {
                    "kind": "docsPage",
                    "path": "/spark/docs/",
                    "url": "https://docs.example.org/spark/docs/",
                    "alternateUrls": [
                        "https://docs.example.org/spark/docs/",
                        "https://docs.example.org/spark/docs/",
                    ],
                    "translations": [
                        {"locale": "de", "url": "https://docs.example.org/de/spark/docs/"},
                        {"locale": "de", "url": "https://docs.example.org/de-alt/spark/docs/"},
                    ],
                    "componentPath": "/spark/",
                    "componentUrl": "https://docs.example.org/spark/",
                },
                by_alias=True,
                by_name=False,
            )

    def test_rejects_partial_version_context_route_pairs(self) -> None:
        with self.assertRaises(ValidationError):
            VersionContext.model_validate(
                {"kind": "released", "label": "4.0.0", "path": "/spark/releases/4.0.0/"},
                by_alias=True,
                by_name=False,
            )

    def test_accepts_page_translation_metadata(self) -> None:
        metadata = PageTranslationMetadata.model_validate(
            {"translationKey": "runtime-sql-overview"},
            by_alias=True,
            by_name=False,
        )

        self.assertEqual(metadata.translation_key, "runtime-sql-overview")