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

"""Tests for normalized provider snapshot models and loading."""

from __future__ import annotations

import unittest

from apache_buildish_site_pipeline.models.enums import DocumentFormat, RecordKind
from apache_buildish_site_pipeline.models.loading import (
    DocumentValidationFailure,
    load_provider_snapshot_document,
)
from apache_buildish_site_pipeline.models.provider.provider_snapshot import (
    ProviderSnapshotDocumentV1,
)


class ProviderSnapshotTests(unittest.TestCase):
    """Validate provider snapshot contracts and cross-record checks."""

    def test_loads_valid_provider_snapshot(self) -> None:
        snapshot = load_provider_snapshot_document(
            '{"schemaVersion":1,"providers":[{"key":"github-releases","type":"github","displayName":"GitHub Releases","baseUrl":"https://github.com/apache/spark","fetchedAt":"2026-04-03T18:00:00Z"}],"records":[{"provider":"github-releases","kind":"released","componentSlug":"spark","artifactKey":"runtime","externalId":"spark-4.0.0","version":"4.0.0","externalUrl":"https://github.com/apache/spark/releases/tag/v4.0.0","publishedAt":"2026-04-03T18:00:00Z","assets":[{"name":"spark-4.0.0-src.tgz","url":"https://downloads.apache.org/spark/spark-4.0.0-src.tgz","checksums":{"sha256":"abc123"}}]}]}',
            document_format=DocumentFormat.JSON,
            source_name="providers.json",
        )

        self.assertIsInstance(snapshot, ProviderSnapshotDocumentV1)
        self.assertEqual(snapshot.records[0].kind, RecordKind.RELEASED)
        self.assertEqual(snapshot.providers[0].key, "github-releases")

    def test_rejects_records_without_stable_locator(self) -> None:
        with self.assertRaises(DocumentValidationFailure):
            load_provider_snapshot_document(
                '{"schemaVersion":1,"providers":[{"key":"github-releases","type":"github","fetchedAt":"2026-04-03T18:00:00Z"}],"records":[{"provider":"github-releases","kind":"namedRef","componentSlug":"spark","artifactKey":"runtime"}]}',
                document_format=DocumentFormat.JSON,
                source_name="providers.json",
            )

    def test_rejects_unknown_provider_and_duplicate_provider_external_id_pairs(self) -> None:
        with self.assertRaises(DocumentValidationFailure):
            load_provider_snapshot_document(
                '{"schemaVersion":1,"providers":[{"key":"github-releases","type":"github","fetchedAt":"2026-04-03T18:00:00Z"}],"records":[{"provider":"missing","kind":"released","componentSlug":"spark","artifactKey":"runtime","externalId":"spark-4.0.0"}]}',
                document_format=DocumentFormat.JSON,
                source_name="providers.json",
            )

        with self.assertRaises(DocumentValidationFailure):
            load_provider_snapshot_document(
                '{"schemaVersion":1,"providers":[{"key":"github-releases","type":"github","fetchedAt":"2026-04-03T18:00:00Z"}],"records":[{"provider":"github-releases","kind":"released","componentSlug":"spark","artifactKey":"runtime","externalId":"spark-4.0.0"},{"provider":"github-releases","kind":"candidate","componentSlug":"spark","artifactKey":"runtime","externalId":"spark-4.0.0","tag":"v4.0.0-rc1"}]}',
                document_format=DocumentFormat.JSON,
                source_name="providers.json",
            )

    def test_rejects_non_public_or_raw_api_provider_base_urls(self) -> None:
        with self.assertRaises(DocumentValidationFailure):
            load_provider_snapshot_document(
                '{"schemaVersion":1,"providers":[{"key":"github-releases","type":"github","baseUrl":"https://localhost/provider","fetchedAt":"2026-04-03T18:00:00Z"}],"records":[]}',
                document_format=DocumentFormat.JSON,
                source_name="providers.json",
            )

        with self.assertRaises(DocumentValidationFailure):
            load_provider_snapshot_document(
                '{"schemaVersion":1,"providers":[{"key":"github-releases","type":"github","baseUrl":"https://api.github.com/repos/apache/spark","fetchedAt":"2026-04-03T18:00:00Z"}],"records":[]}',
                document_format=DocumentFormat.JSON,
                source_name="providers.json",
            )