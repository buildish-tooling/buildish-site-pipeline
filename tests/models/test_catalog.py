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

"""Tests for consumer-authored catalog document models and loading."""

from __future__ import annotations

import json
import unittest
from copy import deepcopy

from pydantic import ValidationError

from apache_buildish_site_pipeline.models.catalog import (
    ArtifactConfig,
    ArtifactLifecycleConfig,
    ArtifactVersioningConfig,
    CandidateSelectionPolicy,
    CatalogDocumentV1,
    ComponentCatalogEntry,
    ExactReleaseConfig,
    LineHeadSelectionPolicy,
    LocalizationConfig,
    MountConfig,
    PublicationSelectionPolicy,
    ReleaseLineConfig,
    ReleaseSelectionPolicy,
    SourceConfig,
)
from apache_buildish_site_pipeline.models.enums import (
    CandidateSelectionMode,
    DocumentFormat,
    IndexBehavior,
    LineHeadSelectionMode,
    PublicationState,
    ReleaseSelectionMode,
    RouteMode,
    TrustClass,
    WithdrawalBehavior,
)
from apache_buildish_site_pipeline.models.loading import DocumentValidationFailure, load_catalog_document


def _build_valid_catalog_document() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "defaults": {
            "publication": {"origin": "docs"},
            "localization": {
                "defaultLocale": "en",
                "supportedLocales": ["en", "de"],
                "routeMode": "prefixAll",
                "fallbackLocale": "en",
            },
        },
        "site": {
            "pagesRoot": "site/pages",
            "assetsRoot": "site/assets",
            "vendorAssets": [{"source": "vendor/brand", "mountPath": "/vendor/brand/"}],
        },
        "origins": {
            "docs": {"baseUrl": "https://docs.example.org", "canonical": True},
        },
        "sources": {
            "consumer": {
                "localDir": "components/spark",
                "repository": "https://github.com/apache/spark",
                "defaultBranch": "main",
            },
        },
        "groups": {
            "streaming": {
                "displayName": "Streaming",
                "pathPrefix": "/platform/",
                "publication": {"origin": "docs"},
            },
        },
        "components": [
            {
                "slug": "spark",
                "displayName": "Apache Spark",
                "weight": 100,
                "group": "streaming",
                "content": {"source": "consumer"},
                "publication": {
                    "origin": "docs",
                    "mountPath": "/spark/",
                    "aliases": [{"path": "/spark/latest/"}],
                    "redirects": [{"fromPath": "/spark/old/", "target": "route:/spark/"}],
                },
                "artifacts": [
                    {
                        "key": "runtime",
                        "source": "consumer",
                        "docsRoot": "docs/runtime",
                        "versioning": {
                            "developmentRef": "main",
                            "tagPattern": "^v[0-9]+\\.[0-9]+\\.[0-9]+$",
                            "namedRefs": [{"key": "preview", "ref": "preview"}],
                        },
                        "publicationSelection": {
                            "development": True,
                            "namedRefs": ["preview"],
                            "lineHeads": {"mode": "explicit", "keys": ["4.x"]},
                            "releases": {"mode": "latestN", "count": 2},
                            "candidates": {"mode": "none"},
                        },
                        "lifecycle": {
                            "latestStable": "4.0.0",
                            "releaseLines": [
                                {
                                    "key": "4.x",
                                    "latest": "4.0.0",
                                    "maintenanceRef": "releases/4.x",
                                    "supportWindow": {
                                        "releaseDate": "2024-01-01T00:00:00Z",
                                        "endOfSupportDate": "2025-01-01T00:00:00Z",
                                    },
                                },
                            ],
                            "releases": [
                                {
                                    "version": "4.0.0",
                                    "publicationState": "withdrawn",
                                    "withdrawalBehavior": "redirect",
                                    "redirectTarget": "route:/spark/",
                                },
                            ],
                        },
                        "mounts": [
                            {
                                "source": "generated/api",
                                "mountPath": "/spark/api/",
                                "kind": "generatedApi",
                                "trustClass": "passive",
                                "metadata": {"generator": "openapi"},
                            },
                        ],
                    },
                ],
            },
        ],
    }


class CatalogDocumentTests(unittest.TestCase):
    """Validate the consumer catalog document contract."""

    def test_loads_valid_catalog_document(self) -> None:
        document = load_catalog_document(
            json.dumps(_build_valid_catalog_document()),
            document_format=DocumentFormat.JSON,
            source_name="site/components.json",
        )

        self.assertIsInstance(document, CatalogDocumentV1)
        self.assertEqual(document.components[0].slug, "spark")
        self.assertEqual(document.components[0].weight, 100)
        self.assertEqual(document.defaults.localization.route_mode, RouteMode.PREFIX_ALL)
        self.assertEqual(document.components[0].artifacts[0].mounts[0].trust_class, TrustClass.PASSIVE)

    def test_rejects_unknown_local_cross_references(self) -> None:
        document = _build_valid_catalog_document()
        document["components"][0]["group"] = "missing"
        with self.assertRaises(DocumentValidationFailure):
            load_catalog_document(
                json.dumps(document),
                document_format=DocumentFormat.JSON,
                source_name="site/components.json",
            )

        document = _build_valid_catalog_document()
        document["components"][0]["content"]["source"] = "missing"
        with self.assertRaises(DocumentValidationFailure):
            load_catalog_document(
                json.dumps(document),
                document_format=DocumentFormat.JSON,
                source_name="site/components.json",
            )

        document = _build_valid_catalog_document()
        document["components"][0]["publication"]["origin"] = "missing"
        with self.assertRaises(DocumentValidationFailure):
            load_catalog_document(
                json.dumps(document),
                document_format=DocumentFormat.JSON,
                source_name="site/components.json",
            )

    def test_rejects_duplicate_artifacts_and_unknown_selection_references(self) -> None:
        document = _build_valid_catalog_document()
        duplicate_artifact = deepcopy(document["components"][0]["artifacts"][0])
        document["components"][0]["artifacts"].append(duplicate_artifact)
        with self.assertRaises(DocumentValidationFailure):
            load_catalog_document(
                json.dumps(document),
                document_format=DocumentFormat.JSON,
                source_name="site/components.json",
            )

        document = _build_valid_catalog_document()
        document["components"][0]["artifacts"][0]["publicationSelection"]["namedRefs"] = ["missing"]
        with self.assertRaises(DocumentValidationFailure):
            load_catalog_document(
                json.dumps(document),
                document_format=DocumentFormat.JSON,
                source_name="site/components.json",
            )

        document = _build_valid_catalog_document()
        document["components"][0]["artifacts"][0]["publicationSelection"]["lineHeads"]["keys"] = ["5.x"]
        with self.assertRaises(DocumentValidationFailure):
            load_catalog_document(
                json.dumps(document),
                document_format=DocumentFormat.JSON,
                source_name="site/components.json",
            )

    def test_rejects_invalid_redirect_and_withdrawal_configurations(self) -> None:
        document = _build_valid_catalog_document()
        document["components"][0]["publication"]["redirects"][0]["status"] = 303
        with self.assertRaises(DocumentValidationFailure):
            load_catalog_document(
                json.dumps(document),
                document_format=DocumentFormat.JSON,
                source_name="site/components.json",
            )

        document = _build_valid_catalog_document()
        document["components"][0]["artifacts"][0]["lifecycle"]["releases"][0].pop("redirectTarget")
        with self.assertRaises(DocumentValidationFailure):
            load_catalog_document(
                json.dumps(document),
                document_format=DocumentFormat.JSON,
                source_name="site/components.json",
            )

    def test_rejects_invalid_support_windows_release_line_chains_and_regexes(self) -> None:
        document = _build_valid_catalog_document()
        document["components"][0]["artifacts"][0]["lifecycle"]["releaseLines"][0]["supportWindow"] = {
            "releaseDate": "2025-01-01T00:00:00Z",
            "endOfSupportDate": "2024-01-01T00:00:00Z",
        }
        with self.assertRaises(DocumentValidationFailure):
            load_catalog_document(
                json.dumps(document),
                document_format=DocumentFormat.JSON,
                source_name="site/components.json",
            )

        document = _build_valid_catalog_document()
        document["components"][0]["artifacts"][0]["lifecycle"]["releaseLines"] = [
            {"key": "4.x", "parent": "5.x", "latest": "4.0.0"},
            {"key": "5.x", "parent": "4.x", "latest": "5.0.0"},
        ]
        with self.assertRaises(DocumentValidationFailure):
            load_catalog_document(
                json.dumps(document),
                document_format=DocumentFormat.JSON,
                source_name="site/components.json",
            )

        document = _build_valid_catalog_document()
        document["components"][0]["artifacts"][0]["versioning"]["tagPattern"] = "["
        with self.assertRaises(DocumentValidationFailure):
            load_catalog_document(
                json.dumps(document),
                document_format=DocumentFormat.JSON,
                source_name="site/components.json",
            )

    def test_rejects_oversized_mount_metadata(self) -> None:
        document = _build_valid_catalog_document()
        document["components"][0]["artifacts"][0]["mounts"][0]["metadata"] = {"blob": "x" * (16 * 1024)}

        with self.assertRaises(DocumentValidationFailure):
            load_catalog_document(
                json.dumps(document),
                document_format=DocumentFormat.JSON,
                source_name="site/components.json",
            )

    def test_rejects_locales_outside_the_supported_set(self) -> None:
        with self.assertRaises(ValidationError):
            LocalizationConfig(default_locale="fr", supported_locales=["en", "de"])

        with self.assertRaises(ValidationError):
            LocalizationConfig(
                default_locale="en",
                fallback_locale="fr",
                supported_locales=["en", "de"],
            )

    def test_selection_policies_enforce_mode_specific_fields(self) -> None:
        invalid_cases = (
            lambda: LineHeadSelectionPolicy(mode=LineHeadSelectionMode.EXPLICIT),
            lambda: LineHeadSelectionPolicy(
                mode=LineHeadSelectionMode.ALL_AUTHORED,
                keys=["4.x"],
            ),
            lambda: ReleaseSelectionPolicy(mode=ReleaseSelectionMode.LATEST_N),
            lambda: ReleaseSelectionPolicy(
                mode=ReleaseSelectionMode.LATEST_N,
                count=1,
                versions=["4.0.0"],
            ),
            lambda: ReleaseSelectionPolicy(mode=ReleaseSelectionMode.EXPLICIT),
            lambda: ReleaseSelectionPolicy(
                mode=ReleaseSelectionMode.EXPLICIT,
                count=1,
                versions=["4.0.0"],
            ),
            lambda: ReleaseSelectionPolicy(
                mode=ReleaseSelectionMode.ALL_KNOWN,
                count=1,
            ),
            lambda: ReleaseSelectionPolicy(
                mode=ReleaseSelectionMode.ALL_KNOWN,
                versions=["4.0.0"],
            ),
            lambda: CandidateSelectionPolicy(mode=CandidateSelectionMode.EXPLICIT),
            lambda: CandidateSelectionPolicy(
                mode=CandidateSelectionMode.LATEST,
                versions=["4.0.0-rc1"],
            ),
        )

        for invalid_case in invalid_cases:
            with self.subTest(case=invalid_case), self.assertRaises(ValidationError):
                invalid_case()

        self.assertEqual(
            ReleaseSelectionPolicy(
                mode=ReleaseSelectionMode.EXPLICIT,
                versions=["4.0.0"],
            ).versions,
            ["4.0.0"],
        )
        self.assertIs(
            ReleaseSelectionPolicy(mode=ReleaseSelectionMode.ALL_KNOWN).mode,
            ReleaseSelectionMode.ALL_KNOWN,
        )
        self.assertEqual(
            CandidateSelectionPolicy(
                mode=CandidateSelectionMode.EXPLICIT,
                versions=["4.0.0-rc1"],
            ).versions,
            ["4.0.0-rc1"],
        )

    def test_release_and_lifecycle_validators_cover_optional_and_error_paths(self) -> None:
        versioning = ArtifactVersioningConfig(
            development_ref="main",
            tag_pattern="^v[0-9]+\\.[0-9]+\\.[0-9]+$",
        )
        mount = MountConfig(
            source="generated/api",
            mount_path="/spark/api/",
            kind="generatedApi",
            trust_class=TrustClass.PASSIVE,
            index_behavior=IndexBehavior.METADATA_ONLY,
        )
        component = ComponentCatalogEntry(slug="spark")
        lifecycle = ArtifactLifecycleConfig(
            release_lines=[
                ReleaseLineConfig(key="4.x", latest="4.0.0"),
                ReleaseLineConfig(key="4.1.x", parent="4.x", latest="4.1.0"),
            ]
        )

        self.assertIsNone(versioning.named_refs)
        self.assertIsNone(mount.metadata)
        self.assertIsNone(component.artifacts)
        self.assertEqual([line.key for line in lifecycle.release_lines], ["4.x", "4.1.x"])
        self.assertIsNone(ArtifactLifecycleConfig().release_lines)
        self.assertEqual(ExactReleaseConfig(version="4.0.0").version, "4.0.0")

        with self.assertRaises(ValidationError):
            ExactReleaseConfig(version="4.0.0", redirect_target="route:/spark/")

        with self.assertRaises(ValidationError):
            ExactReleaseConfig(
                version="4.0.0",
                publication_state=PublicationState.PUBLISHED,
                withdrawal_behavior=WithdrawalBehavior.NOTICE,
            )

        with self.assertRaises(ValidationError):
            ExactReleaseConfig(
                version="4.0.0",
                publication_state=PublicationState.WITHDRAWN,
                withdrawal_behavior=WithdrawalBehavior.NOTICE,
                redirect_target="route:/spark/",
            )

        with self.assertRaises(ValidationError):
            ArtifactLifecycleConfig(
                release_lines=[ReleaseLineConfig(key="4.x", parent="5.x", latest="4.0.0")]
            )

    def test_catalog_document_allows_optional_publication_and_selection_fields(self) -> None:
        document = CatalogDocumentV1(
            schema_version=1,
            sources={"consumer": SourceConfig(local_dir="components/spark")},
            components=[
                ComponentCatalogEntry(slug="spark"),
                ComponentCatalogEntry(
                    slug="spark-connect",
                    artifacts=[
                        ArtifactConfig(
                            key="runtime",
                            source="consumer",
                            versioning=ArtifactVersioningConfig(
                                development_ref="main",
                                tag_pattern="^v[0-9]+\\.[0-9]+\\.[0-9]+$",
                            ),
                            publication_selection=PublicationSelectionPolicy(
                                development=True,
                            ),
                        )
                    ],
                ),
            ],
        )

        self.assertEqual([component.slug for component in document.components], ["spark", "spark-connect"])
        self.assertTrue(
            document.components[1].artifacts[0].publication_selection.development,
        )

    def test_rejects_unknown_artifact_source_reference(self) -> None:
        document = _build_valid_catalog_document()
        document["components"][0]["artifacts"][0]["source"] = "missing"

        with self.assertRaises(DocumentValidationFailure):
            load_catalog_document(
                json.dumps(document),
                document_format=DocumentFormat.JSON,
                source_name="site/components.json",
            )