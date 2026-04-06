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

"""Direct coverage for publication-path and ownership helpers."""

from __future__ import annotations

from pathlib import Path
import unittest

from apache_buildish_site_pipeline.models.enums import PublicationState, RecordKind
from apache_buildish_site_pipeline.planning.types import (
    IndexedProviderRecord,
    ResolvedOrigin,
    ResolvedPublicationPolicy,
    ResolvedSourceBinding,
    SelectedVersionContext,
)
from apache_buildish_site_pipeline.staging.ownership import context_subpath
from apache_buildish_site_pipeline.staging.publication_paths import (
    public_path_for_context,
    target_id_for_context,
)


class PublicationAndOwnershipHelpersTests(unittest.TestCase):
    def test_target_id_for_context_covers_each_selected_record_kind(self) -> None:
        self.assertEqual(
            target_id_for_context(self._context(RecordKind.DEVELOPMENT)),
            "development:spark:runtime",
        )
        self.assertEqual(
            target_id_for_context(self._context(RecordKind.NAMED_REF, named_ref_key="main")),
            "named-ref:spark:runtime:main",
        )
        self.assertEqual(
            target_id_for_context(self._context(RecordKind.LINE_HEAD, release_line="4.0")),
            "line-head:spark:runtime:4.0",
        )
        self.assertEqual(
            target_id_for_context(self._context(RecordKind.CANDIDATE, version="4.1.0-rc1")),
            "candidate:spark:runtime:4.1.0-rc1",
        )
        self.assertEqual(
            target_id_for_context(self._context(RecordKind.RELEASED, version="4.0.0")),
            "released:spark:runtime:4.0.0",
        )

    def test_target_id_for_context_uses_component_owner_key_when_artifact_is_missing(self) -> None:
        self.assertEqual(
            target_id_for_context(
                self._context(RecordKind.DEVELOPMENT, artifact_key=None)
            ),
            "development:spark:component",
        )

    def test_public_path_for_context_uses_component_root_when_docs_and_dev_match(self) -> None:
        same_base_publication = self._publication(docs_path="/spark/", development_path="/spark/")

        self.assertEqual(
            public_path_for_context(same_base_publication, self._context(RecordKind.RELEASED, version="4.0.0")),
            "/spark/releases/4.0.0/",
        )
        self.assertEqual(
            public_path_for_context(self._publication(), self._context(RecordKind.NAMED_REF, named_ref_key="main")),
            "/spark/docs/refs/main/",
        )

    def test_context_subpath_covers_release_line_fallbacks_and_refs(self) -> None:
        line_head = self._context(
            RecordKind.LINE_HEAD,
            provider_record=IndexedProviderRecord(
                provider="provider",
                kind=RecordKind.LINE_HEAD,
                component_slug="spark",
                artifact_key="runtime",
                external_id=None,
                external_url=None,
                version=None,
                display_version=None,
                tag=None,
                ref="maintenance/4.0",
                commit_sha=None,
                named_ref_key=None,
                release_line="4.0",
                release_line_ancestors=(),
                support_status=None,
                publication_state=PublicationState.PUBLISHED,
                maturity=None,
                candidate_sequence=None,
                vote_status=None,
                created_at=None,
                published_at=None,
                updated_at=None,
                urls={},
                assets=(),
            ),
        )

        self.assertEqual(context_subpath(line_head), Path("line-heads/4.0"))
        self.assertEqual(
            context_subpath(self._context(RecordKind.NAMED_REF, named_ref_key="main")),
            Path("refs/main"),
        )
        self.assertEqual(
            context_subpath(self._context(RecordKind.CANDIDATE, version="4.1.0-rc1")),
            Path("candidates/4.1.0-rc1"),
        )

    @staticmethod
    def _publication(
        *,
        docs_path: str = "/spark/docs/",
        development_path: str = "/spark/dev/",
    ) -> ResolvedPublicationPolicy:
        return ResolvedPublicationPolicy(
            origin=ResolvedOrigin(
                key="docs",
                base_url="https://docs.example.org",
                hostname="docs.example.org",
                canonical=True,
            ),
            component_path="/spark/",
            development_path=development_path,
            docs_path=docs_path,
            assets_path="/spark/assets/",
            component_url="https://docs.example.org/spark/",
            development_url="https://docs.example.org/spark/dev/",
            docs_url="https://docs.example.org/spark/docs/",
            assets_url="https://docs.example.org/spark/assets/",
            canonical_path=None,
            aliases=(),
            redirects=(),
        )

    @staticmethod
    def _context(
        kind: RecordKind,
        *,
        artifact_key: str | None = "runtime",
        version: str | None = None,
        release_line: str | None = None,
        named_ref_key: str | None = None,
        provider_record: IndexedProviderRecord | None = None,
    ) -> SelectedVersionContext:
        return SelectedVersionContext(
            component_slug="spark",
            artifact_key=artifact_key,
            kind=kind,
            source_binding=ResolvedSourceBinding(
                key=artifact_key or "component-content",
                local_dir=Path("/workspace/components/runtime"),
                metadata_file=None,
                repository=None,
                default_branch=None,
            ),
            docs_root=Path("/workspace/components/runtime/docs"),
            assets_root=None,
            version=version,
            release_line=release_line,
            named_ref_key=named_ref_key,
            provider_record=provider_record,
        )