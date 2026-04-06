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

from apache_buildish_site_pipeline.models import (
    ComponentMetadataDocumentV1,
    SiteCatalogDocumentV1,
)
from apache_buildish_site_pipeline.planning.effective_config import (
    _join_public_path,
    _resolve_repo_path,
    resolve_site_config,
)


class EffectiveConfigResolutionTests(unittest.TestCase):
    def test_resolves_component_local_dir_into_implicit_content_source(self) -> None:
        catalog = SiteCatalogDocumentV1.model_validate(
            {
                "schemaVersion": 1,
                "defaults": {
                    "metadataFile": "site/component.yaml",
                    "publication": {"origin": "docs"},
                },
                "site": {},
                "origins": {"docs": {"baseUrl": "https://docs.example.org"}},
                "components": [
                    {
                        "slug": "spark",
                        "localDir": "components/runtime",
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

        component = site.components[0]
        self.assertEqual(component.content_source.key, "component:spark")
        self.assertEqual(component.content_source.local_dir, site.workspace_root / "components/runtime")
        self.assertEqual(
            component.content_source.metadata_file,
            site.workspace_root / "components/runtime/site/component.yaml",
        )

    def test_resolves_defaults_groups_and_component_documents(self) -> None:
        catalog = SiteCatalogDocumentV1.model_validate(
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
        component_document = ComponentMetadataDocumentV1.model_validate(
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
        self.assertEqual(component.publication.development_url, "https://docs.example.org/streaming/spark/development/")
        self.assertEqual(component.publication.docs_url, "https://docs.example.org/streaming/spark/development/")
        self.assertEqual(component.publication.assets_url, "https://docs.example.org/streaming/spark/assets/")
        self.assertEqual(component.pages_root.name, "pages")
        self.assertEqual(component.docs_root.name, "rendered")
        self.assertEqual(artifact.docs_root.name, "rendered")

    def test_preserves_explicit_nested_publication_segments(self) -> None:
        catalog = SiteCatalogDocumentV1.model_validate(
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
        catalog = SiteCatalogDocumentV1.model_validate(
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

    def test_rejects_missing_publication_origin(self) -> None:
        catalog = SiteCatalogDocumentV1.model_validate(
            {
                "schemaVersion": 1,
                "site": {},
                "components": [
                    {
                        "slug": "spark",
                        "publication": {"mountPath": "/spark/"},
                        "artifacts": [],
                    },
                ],
            },
            by_alias=True,
            by_name=False,
        )

        with tempfile.TemporaryDirectory() as tempdir, self.assertRaisesRegex(
            ValueError, "cannot resolve a publication origin"
        ):
            resolve_site_config(catalog=catalog, workspace_root=Path(tempdir))

    def test_allows_component_without_bound_content_source(self) -> None:
        catalog = SiteCatalogDocumentV1.model_validate(
            {
                "schemaVersion": 1,
                "defaults": {"publication": {"origin": "docs"}},
                "site": {},
                "origins": {"docs": {"baseUrl": "https://docs.example.org"}},
                "components": [
                    {
                        "slug": "spark",
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

        component = site.components[0]
        self.assertIsNone(component.content_source)
        self.assertIsNone(component.pages_root)
        self.assertIsNone(component.docs_root)
        self.assertIsNone(component.assets_root)

    def test_resolves_component_localization_from_defaults_and_overrides(self) -> None:
        catalog = SiteCatalogDocumentV1.model_validate(
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

    def test_resolves_site_link_check_policy(self) -> None:
        catalog = SiteCatalogDocumentV1.model_validate(
            {
                "schemaVersion": 1,
                "site": {},
                "validation": {
                    "linkChecks": {
                        "enabled": True,
                        "mode": "file-html",
                        "checkRootAbsolute": True,
                        "internalPrefixes": ["/components/", "/docs/"],
                    }
                },
                "origins": {"docs": {"baseUrl": "https://docs.example.org"}},
                "components": [
                    {
                        "slug": "spark",
                        "publication": {"origin": "docs", "mountPath": "/spark/"},
                        "artifacts": [],
                    },
                ],
            },
            by_alias=True,
            by_name=False,
        )

        with tempfile.TemporaryDirectory() as tempdir:
            site = resolve_site_config(catalog=catalog, workspace_root=Path(tempdir))

        self.assertIsNotNone(site.link_checks)
        self.assertTrue(site.link_checks.enabled)
        self.assertEqual(site.link_checks.mode.value, "file-html")
        self.assertEqual(site.link_checks.internal_prefixes, ("/components/", "/docs/"))

    def test_join_public_path_handles_root_prefix(self) -> None:
        self.assertEqual(_join_public_path("/", "spark"), "/spark/")

    def test_resolve_repo_path_rejects_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir, self.assertRaisesRegex(
            ValueError, "escapes declared root"
        ):
            _resolve_repo_path(Path(tempdir), "../outside")