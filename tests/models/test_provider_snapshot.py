# Copyright 2026 The Buildish Authors
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
import json
from pydantic import ValidationError

from buildish_site_pipeline.models.enums import DocumentFormat, RecordKind
from buildish_site_pipeline.models.loading import (
    DocumentValidationFailure,
    load_provider_snapshot_document,
)
from buildish_site_pipeline.models.provider.provider_snapshot import (
    DocsSource,
    ProviderSnapshotDocumentV1,
)


class ProviderSnapshotTests(unittest.TestCase):
    """Validate provider snapshot contracts and cross-record checks."""

    def test_docs_source_round_trip_and_narrow_validation(self):
        for root in (".", "manual/developer-guide"):
            with self.subTest(root=root):
                target = {"repository": "https://forge.example/original", "root": root, "ref": "releases/4.0"}
                self.assertEqual(DocsSource.model_validate(target).model_dump(), target)
        valid = {"repository": "https://forge.example/original", "root": "docs", "ref": "v4.0.0"}
        invalid = [
            dict(valid, root=root)
            for root in ("/outside/docs", "../docs", "docs/../private", "docs\\private", "C:/docs", "C:docs", ".git", "docs/.GIT/hooks", "docs//nested")
        ] + [
            dict(valid, repository=repository)
            for repository in ("https://user:secret@forge.example/repo", "https://forge.example/repo?token=x", "https://forge.example/repo#fragment", "file:///tmp/repo")
        ] + [{key: value for key, value in valid.items() if key != missing} for missing in valid]
        for target in invalid:
            with self.subTest(target=target), self.assertRaises(ValidationError):
                DocsSource.model_validate(target)

    def test_docs_source_survives_snapshot_loading(self):
        document = {
            "schemaVersion": 1,
            "providers": [{"key": "git", "type": "git", "fetchedAt": "2026-11-17T00:00:00Z"}],
            "records": [{
                "provider": "git", "kind": "released", "componentSlug": "spark", "artifactKey": "runtime",
                "version": "4.0.0", "tag": "different-tag",
                "docsSource": {"repository": "https://forge.example/original", "root": ".", "ref": "exported/commit"},
            }],
        }
        loaded = load_provider_snapshot_document(json.dumps(document), document_format=DocumentFormat.JSON, source_name="test")
        self.assertEqual(loaded.records[0].docs_source.ref, "exported/commit")
        self.assertEqual(loaded.model_dump(by_alias=True, exclude_none=True)["records"][0]["docsSource"], document["records"][0]["docsSource"])

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
