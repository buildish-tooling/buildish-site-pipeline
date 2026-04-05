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

"""Direct coverage for input, provider, and publication evaluation helpers."""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace

from apache_buildish_site_pipeline.evaluation.collector import DiagnosticCollector
from apache_buildish_site_pipeline.evaluation.inputs import validate_inputs
from apache_buildish_site_pipeline.evaluation.providers import _matching_records, validate_providers
from apache_buildish_site_pipeline.evaluation.publication import (
    build_publication_index,
    validate_publication,
)
from apache_buildish_site_pipeline.models.enums import (
    MaterializationInputKind,
    MaterializationStatus,
    PublicationState,
    RecordKind,
    WithdrawalBehavior,
)
from apache_buildish_site_pipeline.planning.types import (
    InputReadiness,
    IndexedProviderRecord,
    LocalInputIdentity,
    MaterializationStatusReason,
    ProviderContextIndex,
    ResolvedOrigin,
    ResolvedLocalInput,
    ResolvedPublicationPolicy,
    ResolvedSourceBinding,
    SelectedVersionContext,
)


class InputProviderAndPublicationTests(unittest.TestCase):
    def test_validate_inputs_maps_missing_stale_and_unresolved_statuses(self) -> None:
        collector = DiagnosticCollector()

        validate_inputs(
            SimpleNamespace(
                local_inputs=(
                    self._local_input(MaterializationStatus.PRESENT),
                    self._local_input(
                        MaterializationStatus.MISSING,
                        reason=MaterializationStatusReason.PATH_MISSING,
                    ),
                    self._local_input(
                        MaterializationStatus.STALE,
                        reason=MaterializationStatusReason.STALE_IDENTITY_MISMATCH,
                    ),
                    self._local_input(
                        MaterializationStatus.UNRESOLVED,
                        reason=MaterializationStatusReason.EXPECTED_DIRECTORY,
                    ),
                )
            ),
            collector,
        )

        self.assertEqual(
            [entry.code for entry in collector.build()],
            ["input-missing", "input-stale", "input-unresolved"],
        )

    def test_matching_records_covers_kind_specific_lookup_paths(self) -> None:
        development = self._provider_record(RecordKind.DEVELOPMENT, ref="main")
        line_head = self._provider_record(RecordKind.LINE_HEAD, release_line="4.0")
        released = self._provider_record(RecordKind.RELEASED, version="4.0.0")
        named = self._provider_record(RecordKind.NAMED_REF, named_ref_key="main", ref="refs/heads/main")
        candidate = self._provider_record(RecordKind.CANDIDATE, version="4.1.0-rc1")
        planning = SimpleNamespace(
            provider_index=SimpleNamespace(
                contexts_by_artifact={
                    ("spark", "runtime"): ProviderContextIndex(
                        released_by_version={"4.0.0": (released,)},
                        candidates_by_version={"4.1.0-rc1": (candidate,)},
                        named_refs_by_key={"main": (named,)},
                        refs_by_ref={"refs/heads/main": (named,)},
                        line_heads_by_release_line={"4.0": (line_head,)},
                        development_records=(development,),
                    )
                }
            )
        )

        self.assertEqual(_matching_records(planning=planning, context=self._context(RecordKind.DEVELOPMENT, ref="main")), (development,))
        self.assertEqual(_matching_records(planning=planning, context=self._context(RecordKind.DEVELOPMENT)), ())
        self.assertEqual(_matching_records(planning=planning, context=self._context(RecordKind.LINE_HEAD, release_line="4.0")), (line_head,))
        self.assertEqual(_matching_records(planning=planning, context=self._context(RecordKind.RELEASED, version="4.0.0")), (released,))
        self.assertEqual(_matching_records(planning=planning, context=self._context(RecordKind.NAMED_REF, named_ref_key="main")), (named,))
        self.assertEqual(_matching_records(planning=planning, context=self._context(RecordKind.NAMED_REF, ref="refs/heads/main")), (named,))
        self.assertEqual(_matching_records(planning=planning, context=self._context(RecordKind.CANDIDATE, version="4.1.0-rc1")), (candidate,))
        self.assertEqual(_matching_records(planning=planning, context=self._context(RecordKind.RELEASED, component_slug="flink")), ())

    def test_validate_providers_reports_ambiguous_and_nondeterministic_contexts(self) -> None:
        matching = (
            self._provider_record(RecordKind.RELEASED, version="4.0.0", external_id="a"),
            self._provider_record(RecordKind.RELEASED, version="4.0.0", external_id="b"),
        )
        planning = SimpleNamespace(
            provider_index=SimpleNamespace(
                contexts_by_artifact={
                    ("spark", "runtime"): ProviderContextIndex(
                        released_by_version={"4.0.0": matching},
                        candidates_by_version={},
                        named_refs_by_key={},
                        refs_by_ref={},
                        line_heads_by_release_line={},
                        development_records=(),
                    )
                }
            ),
            selected_versions=SimpleNamespace(
                contexts=(
            self._context(RecordKind.RELEASED, version="4.0.0"),
            self._context(
                RecordKind.RELEASED,
                version="4.0.0",
                deterministic=False,
            ),
                )
            ),
        )
        collector = DiagnosticCollector()

        validate_providers(planning=planning, collector=collector)

        self.assertEqual([entry.code for entry in collector.build()], ["provider-context-ambiguous", "provider-context-ambiguous"])

    def test_build_publication_index_adds_docs_target_only_when_distinct(self) -> None:
        planning = SimpleNamespace(
            site=SimpleNamespace(
                components=(
                    SimpleNamespace(slug="spark", publication=self._publication()),
                    SimpleNamespace(
                        slug="flink",
                        publication=self._publication(
                            component_path="/flink/",
                            development_path="/flink/",
                            docs_path="/flink/",
                        ),
                    ),
                )
            )
        )

        index = build_publication_index(planning)

        self.assertEqual(
            [target.target_id for target in index.targets],
            [
                "component:spark",
                "development:spark",
                "assets:spark",
                "docs:spark",
                "component:flink",
                "development:flink",
                "assets:flink",
            ],
        )

    def test_validate_publication_rejects_case_insensitive_route_collisions(self) -> None:
        planning = SimpleNamespace(
            site=SimpleNamespace(
                components=(
                    SimpleNamespace(slug="spark", publication=self._publication(component_path="/Docs/")),
                    SimpleNamespace(
                        slug="flink",
                        publication=self._publication(
                            component_path="/docs/",
                            development_path="/flink/dev/",
                            docs_path="/flink/docs/",
                        ),
                    ),
                )
            )
        )
        collector = DiagnosticCollector()

        validate_publication(planning=planning, collector=collector)

        self.assertEqual(
            [entry.code for entry in collector.build()],
            ["publication-route-collision", "publication-route-collision"],
        )

    @staticmethod
    def _local_input(
        status: MaterializationStatus,
        *,
        reason: MaterializationStatusReason | None = None,
    ) -> ResolvedLocalInput:
        return ResolvedLocalInput(
            identity=LocalInputIdentity(
                source_key="runtime",
                input_kind=MaterializationInputKind.DEVELOPMENT,
                component_slug="spark",
                artifact_key="runtime",
            ),
            declared_root=Path("/workspace/components"),
            expected_local_path=Path("/workspace/components/runtime"),
            provenance="component:spark",
            readiness=InputReadiness(status=status, reason=reason),
            watch_eligible=True,
        )

    @staticmethod
    def _provider_record(
        kind: RecordKind,
        *,
        version: str | None = None,
        release_line: str | None = None,
        named_ref_key: str | None = None,
        ref: str | None = None,
        external_id: str | None = None,
    ) -> IndexedProviderRecord:
        return IndexedProviderRecord(
            provider="provider",
            kind=kind,
            component_slug="spark",
            artifact_key="runtime",
            external_id=external_id,
            external_url=None,
            version=version,
            display_version=version,
            tag=None,
            ref=ref,
            commit_sha=None,
            named_ref_key=named_ref_key,
            release_line=release_line,
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
        )

    @staticmethod
    def _context(
        kind: RecordKind,
        *,
        component_slug: str = "spark",
        version: str | None = None,
        release_line: str | None = None,
        named_ref_key: str | None = None,
        ref: str | None = None,
        deterministic: bool = True,
    ) -> SelectedVersionContext:
        return SelectedVersionContext(
            component_slug=component_slug,
            artifact_key="runtime",
            kind=kind,
            source_binding=ResolvedSourceBinding(
                key="runtime",
                local_dir=Path("/workspace/components/runtime"),
                metadata_file=None,
                repository=None,
                default_branch=None,
            ),
            docs_root=Path("/workspace/components/runtime/docs"),
            assets_root=None,
            version=version,
            release_line=release_line,
            ref=ref,
            named_ref_key=named_ref_key,
            publication_state=PublicationState.PUBLISHED,
            withdrawal_behavior=WithdrawalBehavior.NOTICE,
            deterministic=deterministic,
        )

    @staticmethod
    def _publication(
        *,
        component_path: str = "/spark/",
        development_path: str = "/spark/dev/",
        docs_path: str = "/spark/docs/",
    ) -> ResolvedPublicationPolicy:
        return ResolvedPublicationPolicy(
            origin=ResolvedOrigin(
                key="docs",
                base_url="https://docs.example.org",
                hostname="docs.example.org",
                canonical=True,
            ),
            component_path=component_path,
            development_path=development_path,
            docs_path=docs_path,
            assets_path=f"{component_path}assets/",
            component_url=f"https://docs.example.org{component_path}",
            development_url=f"https://docs.example.org{development_path}",
            docs_url=f"https://docs.example.org{docs_path}",
            assets_url=f"https://docs.example.org{component_path}assets/",
            canonical_path=None,
            aliases=(),
            redirects=(),
        )