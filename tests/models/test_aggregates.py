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

"""Tests for staged aggregate entry models."""

from __future__ import annotations

import json
import unittest

from pydantic import ValidationError

from apache_buildish_site_pipeline.models.aggregates import (
    CompatibilityAggregateEntry,
    ComponentsDataEntry,
    ContentIndexEntry,
    MountAggregateEntry,
    ProvidersDataEntry,
    RedirectAggregateEntry,
    RefAggregateEntry,
    ReleaseAggregateEntry,
    RouteAggregateEntry,
    TranslationSetAggregateEntry,
)


class AggregateModelTests(unittest.TestCase):
    """Validate the public staged aggregate entry contract."""

    def test_serializes_valid_component_and_provider_entries(self) -> None:
        provider = ProvidersDataEntry.model_validate(
            {
                "key": "github-releases",
                "type": "githubReleases",
                "baseUrl": "https://github.com/apache/spark/releases",
                "fetchedAt": "2026-04-03T18:00:00Z",
            },
            by_alias=True,
            by_name=False,
        )
        component = ComponentsDataEntry.model_validate(
            {
                "slug": "spark",
                "weight": 100,
                "originKey": "docs",
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
                "providerKeys": ["github-releases"],
            },
            by_alias=True,
            by_name=False,
        )

        provider_payload = provider.model_dump(by_alias=True, exclude_none=True)
        component_payload = component.model_dump(by_alias=True, exclude_none=True)
        self.assertIn("fetchedAt", provider_payload)
        self.assertIn("providerKeys", component_payload)
        self.assertEqual(component_payload["weight"], 100)
        self.assertNotIn("provider_keys", json.dumps(component_payload))

    def test_rejects_inconsistent_origin_redirect_and_ref_kinds(self) -> None:
        with self.assertRaises(ValidationError):
            ComponentsDataEntry.model_validate(
                {
                    "slug": "spark",
                    "originKey": "downloads",
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
                by_alias=True,
                by_name=False,
            )

        with self.assertRaises(ValidationError):
            ReleaseAggregateEntry.model_validate(
                {
                    "componentSlug": "spark",
                    "artifactKey": "runtime",
                    "version": "4.0.0",
                    "publicationState": "withdrawn",
                    "withdrawalBehavior": "redirect",
                },
                by_alias=True,
                by_name=False,
            )

        with self.assertRaises(ValidationError):
            RefAggregateEntry.model_validate(
                {
                    "componentSlug": "spark",
                    "artifactKey": "runtime",
                    "kind": "released",
                    "ref": "main",
                },
                by_alias=True,
                by_name=False,
            )

    def test_rejects_invalid_routes_translation_sets_and_mount_metadata(self) -> None:
        with self.assertRaises(ValidationError):
            RouteAggregateEntry.model_validate(
                {
                    "originKey": "docs",
                    "baseUrl": "https://docs.example.org",
                    "path": "/spark/",
                    "url": "https://docs.example.org/other/",
                    "componentSlug": "spark",
                },
                by_alias=True,
                by_name=False,
            )

        with self.assertRaises(ValidationError):
            RouteAggregateEntry.model_validate(
                {
                    "originKey": "docs",
                    "baseUrl": "https://docs.example.org",
                    "path": "/spark/",
                    "url": "https://docs.example.org/spark/",
                    "componentSlug": "spark",
                    "redirectTargetUrl": "https://docs.example.org/new-spark/",
                    "redirectStatus": 302,
                },
                by_alias=True,
                by_name=False,
            )

        with self.assertRaises(ValidationError):
            RedirectAggregateEntry.model_validate(
                {
                    "fromUrl": "https://docs.example.org/spark/",
                    "toUrl": "https://docs.example.org/spark/latest/",
                    "status": 303,
                },
                by_alias=True,
                by_name=False,
            )

        with self.assertRaises(ValidationError):
            TranslationSetAggregateEntry.model_validate(
                {
                    "translationKey": "spark-overview",
                    "componentSlug": "spark",
                    "entries": [
                        {"locale": "en", "url": "https://docs.example.org/spark/"},
                        {"locale": "en", "url": "https://docs.example.org/en/spark/"},
                    ],
                },
                by_alias=True,
                by_name=False,
            )

        with self.assertRaises(ValidationError):
            CompatibilityAggregateEntry.model_validate(
                {
                    "subjectId": "component:spark",
                    "targetId": "component:flink",
                    "relation": "supports",
                    "evidence": ["matrix", "matrix"],
                },
                by_alias=True,
                by_name=False,
            )

        with self.assertRaises(ValidationError):
            MountAggregateEntry.model_validate(
                {
                    "mountId": "spark-api",
                    "ownerId": "component:spark",
                    "kind": "generatedApi",
                    "trustClass": "passive",
                    "publicPath": "/spark/api/",
                    "sourceRef": "generated:api",
                    "metadata": {"blob": "x" * (16 * 1024)},
                },
                by_alias=True,
                by_name=False,
            )

    def test_rejects_release_redirect_field_combinations_and_accepts_valid_small_metadata(self) -> None:
        with self.assertRaises(ValidationError):
            ReleaseAggregateEntry.model_validate(
                {
                    "componentSlug": "spark",
                    "artifactKey": "runtime",
                    "version": "4.0.0",
                    "redirectTarget": "route:/spark/latest/",
                },
                by_alias=True,
                by_name=False,
            )

        with self.assertRaises(ValidationError):
            ReleaseAggregateEntry.model_validate(
                {
                    "componentSlug": "spark",
                    "artifactKey": "runtime",
                    "version": "4.0.0",
                    "publicationState": "published",
                    "withdrawalBehavior": "notice",
                },
                by_alias=True,
                by_name=False,
            )

        with self.assertRaises(ValidationError):
            ReleaseAggregateEntry.model_validate(
                {
                    "componentSlug": "spark",
                    "artifactKey": "runtime",
                    "version": "4.0.0",
                    "publicationState": "withdrawn",
                    "withdrawalBehavior": "notice",
                    "redirectTarget": "route:/spark/latest/",
                },
                by_alias=True,
                by_name=False,
            )

        mount = MountAggregateEntry.model_validate(
            {
                "mountId": "spark-api",
                "ownerId": "component:spark",
                "kind": "generatedApi",
                "trustClass": "passive",
                "publicPath": "/spark/api/",
                "sourceRef": "generated:api",
                "metadata": {"summary": "small"},
            },
            by_alias=True,
            by_name=False,
        )

        self.assertEqual(mount.metadata, {"summary": "small"})

    def test_rejects_duplicate_content_index_ancestors(self) -> None:
        with self.assertRaises(ValidationError):
            ContentIndexEntry.model_validate(
                {
                    "id": "page:spark-overview",
                    "componentSlug": "spark",
                    "pageKind": "docsPage",
                    "originKey": "docs",
                    "path": "/spark/overview/",
                    "url": "https://docs.example.org/spark/overview/",
                    "ancestorIds": ["page:spark", "page:spark"],
                },
                by_alias=True,
                by_name=False,
            )