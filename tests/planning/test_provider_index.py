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

"""Tests for provider snapshot indexing safety and planning ceilings."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from apache_buildish_site_pipeline.models import ProviderSnapshotDocumentV1
from apache_buildish_site_pipeline.planning.provider_index import build_provider_snapshot_index


class ProviderIndexTests(unittest.TestCase):
    def test_rejects_provider_record_for_unknown_artifact(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown artifact spark:missing"):
            build_provider_snapshot_index(
                provider_snapshot=_provider_snapshot(
                    [
                        {
                            "provider": "github",
                            "kind": "development",
                            "componentSlug": "spark",
                            "artifactKey": "missing",
                            "ref": "main",
                        },
                    ]
                ),
                site=_site_with_runtime_artifact(),
            )

    def test_rejects_provider_snapshot_when_record_ceiling_is_exceeded(self) -> None:
        with patch("apache_buildish_site_pipeline.planning.provider_index._MAX_PROVIDER_RECORDS", 1):
            with self.assertRaisesRegex(ValueError, "50,000 record planning ceiling"):
                build_provider_snapshot_index(
                    provider_snapshot=_provider_snapshot(
                        [
                            {
                                "provider": "github",
                                "kind": "development",
                                "componentSlug": "spark",
                                "artifactKey": "runtime",
                                "ref": "main",
                            },
                            {
                                "provider": "github",
                                "kind": "released",
                                "componentSlug": "spark",
                                "artifactKey": "runtime",
                                "version": "4.0.0",
                                "tag": "v4.0.0",
                            },
                        ]
                    ),
                    site=_site_with_runtime_artifact(),
                )

    def test_rejects_provider_snapshot_when_byte_ceiling_is_exceeded(self) -> None:
        with patch("apache_buildish_site_pipeline.planning.provider_index._MAX_PROVIDER_SNAPSHOT_BYTES", 1):
            with self.assertRaisesRegex(ValueError, "16 MiB planning ceiling"):
                build_provider_snapshot_index(
                    provider_snapshot=_provider_snapshot(
                        [
                            {
                                "provider": "github",
                                "kind": "development",
                                "componentSlug": "spark",
                                "artifactKey": "runtime",
                                "ref": "main",
                            },
                        ]
                    ),
                    site=_site_with_runtime_artifact(),
                )


def _provider_snapshot(
    records: list[dict[str, object]],
) -> ProviderSnapshotDocumentV1:
    return ProviderSnapshotDocumentV1.model_validate(
        {
            "schemaVersion": 1,
            "providers": [{"key": "github", "type": "githubReleases", "fetchedAt": "2026-04-03T00:00:00Z"}],
            "records": records,
        }
    )


def _site_with_runtime_artifact() -> object:
    return SimpleNamespace(
        components=(
            SimpleNamespace(
                slug="spark",
                artifacts=(SimpleNamespace(key="runtime"),),
            ),
        ),
    )