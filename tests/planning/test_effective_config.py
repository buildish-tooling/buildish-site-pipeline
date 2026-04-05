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

"""Tests for effective planning configuration resolution."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from apache_buildish_site_pipeline.models import CatalogDocumentV1, ComponentRepositoryDocumentV1
from apache_buildish_site_pipeline.planning.effective_config import resolve_site_config


class EffectiveConfigResolutionTests(unittest.TestCase):
    def test_resolves_defaults_groups_and_component_documents(self) -> None:
        catalog = CatalogDocumentV1.model_validate(
            {
                "schemaVersion": 1,
                "defaults": {
                    "metadataFile": "site/component.yaml",
                    "pagesRoot": "site/pages",
                    "docsRoot": "site/docs",
                    "assetsRoot": "site/assets",
                    "publication": {"origin": "docs"},
                },
                "site": {
                    "pagesRoot": "site/root-pages",
                    "assetsRoot": "site/root-assets",
                    "vendorAssets": [{"source": "vendor/brand", "mountPath": "/assets/vendor/brand/"}],
                },
                "origins": {"docs": {"baseUrl": "https://docs.example.org"}},
                "sources": {"runtime": {"localDir": "components/runtime"}},
                "groups": {"streaming": {"pathPrefix": "/streaming/"}},
                "components": [
                    {
                        "slug": "spark",
                        "group": "streaming",
                        "content": {"source": "runtime"},
                        "publication": {"pathSegment": "spark"},
                        "artifacts": [
                            {
                                "key": "runtime",
                                "source": "runtime",
                                "versioning": {"developmentRef": "main", "tagPattern": "^v.*$"},
                            },
                        ],
                    },
                ],
            },
            by_alias=True,
            by_name=False,
        )
        component_document = ComponentRepositoryDocumentV1.model_validate(
            {
                "schemaVersion": 1,
                "component": {"slug": "spark"},
                "content": {"pagesRoot": "docs/pages", "docsRoot": "docs/rendered", "assetsRoot": "docs/assets"},
            },
            by_alias=True,
            by_name=False,
        )

        with tempfile.TemporaryDirectory() as tempdir:
            site = resolve_site_config(
                catalog=catalog,
                workspace_root=Path(tempdir),
                component_documents={"spark": component_document},
            )

        component = site.components[0]
        artifact = component.artifacts[0]
        self.assertEqual(component.publication.component_path, "/streaming/spark/")
        self.assertEqual(component.publication.development_url, "https://docs.example.org/streaming/spark/latest/")
        self.assertEqual(component.publication.docs_url, "https://docs.example.org/streaming/spark/latest/")
        self.assertEqual(component.publication.assets_url, "https://docs.example.org/streaming/spark/assets/")
        self.assertEqual(component.pages_root.name, "pages")
        self.assertEqual(component.docs_root.name, "rendered")
        self.assertEqual(artifact.docs_root.name, "rendered")

    def test_preserves_explicit_nested_publication_segments(self) -> None:
        catalog = CatalogDocumentV1.model_validate(
            {
                "schemaVersion": 1,
                "defaults": {
                    "publication": {
                        "origin": "docs",
                        "developmentSegment": "development",
                        "docsSegment": "docs",
                        "assetsSegment": "assets",
                    },
                },
                "site": {},
                "origins": {"docs": {"baseUrl": "https://docs.example.org"}},
                "sources": {"runtime": {"localDir": "components/runtime"}},
                "components": [
                    {
                        "slug": "spark",
                        "content": {"source": "runtime"},
                        "publication": {"mountPath": "/spark/"},
                        "artifacts": [],
                    },
                ],
            },
            by_alias=True,
            by_name=False,
        )

        with tempfile.TemporaryDirectory() as tempdir:
            site = resolve_site_config(catalog=catalog, workspace_root=Path(tempdir))

        publication = site.components[0].publication
        self.assertEqual(publication.development_path, "/spark/development/")
        self.assertEqual(publication.docs_path, "/spark/development/docs/")
        self.assertEqual(publication.assets_path, "/spark/assets/")

    def test_rejects_unresolvable_component_publication_path(self) -> None:
        catalog = CatalogDocumentV1.model_validate(
            {
                "schemaVersion": 1,
                "defaults": {"publication": {"origin": "docs"}},
                "site": {},
                "origins": {"docs": {"baseUrl": "https://docs.example.org"}},
                "sources": {"runtime": {"localDir": "components/runtime"}},
                "components": [{"slug": "spark", "artifacts": []}],
            },
            by_alias=True,
            by_name=False,
        )
        with tempfile.TemporaryDirectory() as tempdir, self.assertRaises(ValueError):
                resolve_site_config(catalog=catalog, workspace_root=Path(tempdir))

    def test_resolves_component_localization_from_defaults_and_overrides(self) -> None:
        catalog = CatalogDocumentV1.model_validate(
            {
                "schemaVersion": 1,
                "defaults": {
                    "publication": {"origin": "docs"},
                    "localization": {
                        "supportedLocales": ["en", "de"],
                        "defaultLocale": "en",
                        "fallbackLocale": "de",
                        "routeMode": "prefixAll",
                    },
                },
                "site": {},
                "origins": {"docs": {"baseUrl": "https://docs.example.org"}},
                "sources": {"runtime": {"localDir": "components/runtime"}},
                "components": [
                    {
                        "slug": "spark",
                        "content": {"source": "runtime"},
                        "localization": {"supportedLocales": ["de", "fr"], "defaultLocale": "fr"},
                        "publication": {"mountPath": "/spark/"},
                        "artifacts": [],
                    },
                ],
            },
            by_alias=True,
            by_name=False,
        )

        with tempfile.TemporaryDirectory() as tempdir:
            site = resolve_site_config(catalog=catalog, workspace_root=Path(tempdir))

        localization = site.components[0].localization
        self.assertEqual(("de", "fr"), localization.supported_locales)
        self.assertEqual("fr", localization.default_locale)
        self.assertEqual("de", localization.fallback_locale)
        self.assertEqual("prefixAll", localization.route_mode.value)