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

"""Direct coverage for planning selection and reference-index helpers."""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import apache_buildish_site_pipeline.planning.selection as selection_module
from apache_buildish_site_pipeline.evaluation.collector import DiagnosticCollector
from apache_buildish_site_pipeline.evaluation.reference_index import (
    KnownRoute,
    _build_context_reference_index,
    _has_line_cycle,
    _reference_exists,
    _validate_component_artifacts,
    _validate_compatibility_references,
    _validate_release_lines,
    _validate_selection_references,
    build_reference_index,
    resolve_internal_reference,
    validate_references,
)
from apache_buildish_site_pipeline.evaluation.types import PublishedTarget
from apache_buildish_site_pipeline.models.catalog import (
    ArtifactLifecycleConfig,
    ArtifactVersioningConfig,
    CandidateSelectionPolicy,
    CompatibilityAssertionConfig,
    ExactReleaseConfig,
    LineHeadSelectionPolicy,
    NamedRefConfig,
    PublicationSelectionPolicy,
    ReleaseLineConfig,
    ReleaseSelectionPolicy,
)
from apache_buildish_site_pipeline.models.enums import (
    CandidateSelectionMode,
    LineHeadSelectionMode,
    PublicationState,
    RecordKind,
    ReleaseSelectionMode,
)
from apache_buildish_site_pipeline.planning.selection import (
    _select_development_context,
    _select_candidate_contexts,
    _select_line_head_contexts,
    _select_named_ref_contexts,
    _select_release_contexts,
    _version_sort_key,
    select_version_contexts,
)
from apache_buildish_site_pipeline.planning.types import (
    IndexedProviderRecord,
    ProviderContextIndex,
    ProviderSnapshotIndex,
    ResolvedSourceBinding,
)


class SelectionAndReferenceIndexTests(unittest.TestCase):
    def test_build_context_reference_index_collects_routes_targets_and_provider_releases(self) -> None:
        artifact = self._artifact(
            lifecycle=ArtifactLifecycleConfig(
                releases=[ExactReleaseConfig(version="4.0.0", release_line="4.0")],
                release_lines=[ReleaseLineConfig(key="4.0", latest="4.0.0")],
            )
        )
        planning = SimpleNamespace(
            site=SimpleNamespace(
                components=(
                    SimpleNamespace(
                        slug="spark",
                        artifacts=(artifact,),
                    ),
                )
            ),
            selected_versions=SimpleNamespace(
                contexts=(
                    SimpleNamespace(
                        component_slug="spark",
                        artifact_key="runtime",
                        kind=RecordKind.RELEASED,
                        release_line="4.0",
                        version="4.0.0",
                    ),
                )
            ),
            provider_index=ProviderSnapshotIndex(
                providers={},
                contexts_by_artifact={
                    ("spark", "runtime"): ProviderContextIndex(
                        released_by_version={
                            "4.0.1": (
                                self._provider_record(
                                    RecordKind.RELEASED,
                                    version="4.0.1",
                                ),
                            )
                        },
                        candidates_by_version={},
                        named_refs_by_key={},
                        refs_by_ref={},
                        line_heads_by_release_line={},
                        development_records=(),
                    )
                },
                by_external_id={},
                snapshot_bytes=0,
                record_count=0,
            ),
        )

        reference_index = _build_context_reference_index(
            planning=planning,
            publication_targets=(
                PublishedTarget(
                    component_slug="spark",
                    target_id="component:spark",
                    origin_key="docs",
                    path="/spark/guide/",
                ),
            ),
        )

        self.assertEqual(
            reference_index.routes_by_lookup_key[("docs", "/spark/guide/")].route_id,
            "component:spark",
        )
        self.assertIn("component:spark", reference_index.targets_by_reference)
        self.assertIn("line:spark/runtime@4.0", reference_index.targets_by_reference)
        self.assertIn("release:spark/runtime@4.0.0", reference_index.targets_by_reference)
        self.assertEqual(reference_index.known_components, frozenset({"spark"}))
        self.assertEqual(
            reference_index.artifacts_by_component,
            {"spark": frozenset({"runtime"})},
        )
        self.assertEqual(
            reference_index.releases_by_artifact[("spark", "runtime")],
            frozenset({"4.0.0", "4.0.1"}),
        )
        self.assertEqual(
            reference_index.named_refs_by_artifact[("spark", "runtime")],
            frozenset({"main"}),
        )

    def test_select_release_contexts_all_known_merges_and_sorts_versions(self) -> None:
        artifact = self._artifact(
            publication_selection=PublicationSelectionPolicy(
                releases=ReleaseSelectionPolicy(mode=ReleaseSelectionMode.ALL_KNOWN)
            ),
            lifecycle=ArtifactLifecycleConfig(
                releases=[ExactReleaseConfig(version="4.0.0", release_line="4.0")],
                release_lines=[ReleaseLineConfig(key="4.0", latest="4.0.0")],
            ),
        )
        provider_context = ProviderContextIndex(
            released_by_version={
                "4.1.0": (self._provider_record(RecordKind.RELEASED, version="4.1.0"),)
            },
            candidates_by_version={},
            named_refs_by_key={},
            refs_by_ref={},
            line_heads_by_release_line={},
            development_records=(),
        )

        contexts = _select_release_contexts(
            "spark",
            artifact,
            provider_context,
            artifact.publication_selection,
        )

        self.assertEqual([context.version for context in contexts], ["4.1.0", "4.0.0"])
        self.assertEqual(contexts[0].display_version, "4.1.0")
        self.assertEqual(contexts[1].publication_state, None)

    def test_select_named_ref_contexts_falls_back_to_ref_lookup(self) -> None:
        artifact = self._artifact(
            publication_selection=PublicationSelectionPolicy(named_refs=["main"]),
        )
        provider_context = ProviderContextIndex(
            released_by_version={},
            candidates_by_version={},
            named_refs_by_key={},
            refs_by_ref={
                "refs/heads/main": (
                    self._provider_record(
                        RecordKind.NAMED_REF,
                        named_ref_key="provider-main",
                        ref="refs/heads/main",
                    ),
                )
            },
            line_heads_by_release_line={},
            development_records=(),
        )

        contexts = _select_named_ref_contexts(
            "spark",
            artifact,
            provider_context,
            artifact.publication_selection,
        )

        self.assertEqual(len(contexts), 1)
        self.assertEqual(contexts[0].named_ref_key, "main")
        self.assertEqual(contexts[0].ref, "refs/heads/main")
        self.assertEqual(contexts[0].display_version, None)

    def test_select_candidate_contexts_filters_external_ids_and_marks_nondeterministic(self) -> None:
        artifact = self._artifact(
            publication_selection=PublicationSelectionPolicy(
                candidates=CandidateSelectionPolicy(
                    mode=CandidateSelectionMode.EXPLICIT,
                    versions=["4.1.0-rc1"],
                    external_ids=["winner", "runner-up"],
                )
            )
        )
        provider_context = ProviderContextIndex(
            released_by_version={},
            candidates_by_version={
                "4.1.0-rc1": (
                    self._provider_record(
                        RecordKind.CANDIDATE,
                        version="4.1.0-rc1",
                        external_id="winner",
                    ),
                    self._provider_record(
                        RecordKind.CANDIDATE,
                        version="4.1.0-rc1",
                        external_id="runner-up",
                    ),
                    self._provider_record(
                        RecordKind.CANDIDATE,
                        version="4.1.0-rc1",
                        external_id="ignored",
                    ),
                )
            },
            named_refs_by_key={},
            refs_by_ref={},
            line_heads_by_release_line={},
            development_records=(),
        )

        contexts = _select_candidate_contexts(
            "spark",
            artifact,
            provider_context,
            artifact.publication_selection,
        )

        self.assertEqual(len(contexts), 1)
        self.assertEqual(contexts[0].version, "4.1.0-rc1")
        self.assertFalse(contexts[0].deterministic)
        self.assertIn(contexts[0].provider_record.external_id, {"winner", "runner-up"})

    def test_select_candidate_contexts_latest_prefers_highest_version(self) -> None:
        artifact = self._artifact(
            publication_selection=PublicationSelectionPolicy(
                candidates=CandidateSelectionPolicy(mode=CandidateSelectionMode.LATEST)
            )
        )
        provider_context = ProviderContextIndex(
            released_by_version={},
            candidates_by_version={
                "4.1.0-rc1": (
                    self._provider_record(RecordKind.CANDIDATE, version="4.1.0-rc1"),
                ),
                "4.2.0-rc1": (
                    self._provider_record(RecordKind.CANDIDATE, version="4.2.0-rc1"),
                ),
            },
            named_refs_by_key={},
            refs_by_ref={},
            line_heads_by_release_line={},
            development_records=(),
        )

        contexts = _select_candidate_contexts(
            "spark",
            artifact,
            provider_context,
            artifact.publication_selection,
        )

        self.assertEqual([context.version for context in contexts], ["4.2.0-rc1"])

    def test_select_line_head_contexts_uses_provider_ref_when_authored_ref_missing(self) -> None:
        artifact = self._artifact(
            publication_selection=PublicationSelectionPolicy(
                line_heads=LineHeadSelectionPolicy(mode="explicit", keys=["4.0"])
            ),
            lifecycle=ArtifactLifecycleConfig(
                release_lines=[ReleaseLineConfig(key="4.0", latest="4.0.0")]
            ),
        )
        provider_context = ProviderContextIndex(
            released_by_version={},
            candidates_by_version={},
            named_refs_by_key={},
            refs_by_ref={},
            line_heads_by_release_line={
                "4.0": (
                    self._provider_record(
                        RecordKind.LINE_HEAD,
                        release_line="4.0",
                        ref="maintenance/4.0",
                    ),
                )
            },
            development_records=(),
        )

        contexts = _select_line_head_contexts(
            "spark",
            artifact,
            provider_context,
            artifact.publication_selection,
        )

        self.assertEqual(len(contexts), 1)
        self.assertEqual(contexts[0].release_line, "4.0")
        self.assertEqual(contexts[0].ref, "maintenance/4.0")

    def test_select_version_contexts_uses_default_policy_when_no_publication_selection_is_authored(self) -> None:
        artifact = self._artifact(
            lifecycle=ArtifactLifecycleConfig(
                releases=[ExactReleaseConfig(version="4.0.0", release_line="4.0")],
                release_lines=[
                    ReleaseLineConfig(
                        key="4.0",
                        latest="4.0.0",
                        maintenance_ref="refs/heads/4.0",
                    )
                ],
            )
        )
        site = SimpleNamespace(
            components=(
                SimpleNamespace(
                    slug="spark",
                    artifacts=(artifact,),
                    publication_selection=None,
                ),
            )
        )
        provider_index = ProviderSnapshotIndex(
            providers={},
            contexts_by_artifact={("spark", "runtime"): self._provider_context()},
            by_external_id={},
            snapshot_bytes=0,
            record_count=0,
        )

        selected = select_version_contexts(site=site, provider_index=provider_index)

        self.assertEqual(
            [context.kind for context in selected.contexts],
            [RecordKind.DEVELOPMENT, RecordKind.LINE_HEAD, RecordKind.RELEASED],
        )
        self.assertTrue(selected.deterministic)

    def test_select_version_contexts_rejects_more_than_the_context_ceiling(self) -> None:
        artifact = self._artifact(
            lifecycle=ArtifactLifecycleConfig(
                releases=[ExactReleaseConfig(version="4.0.0", release_line="4.0")],
                release_lines=[
                    ReleaseLineConfig(
                        key="4.0",
                        latest="4.0.0",
                        maintenance_ref="refs/heads/4.0",
                    )
                ],
            )
        )
        site = SimpleNamespace(
            components=(
                SimpleNamespace(
                    slug="spark",
                    artifacts=(artifact,),
                    publication_selection=None,
                ),
            )
        )
        provider_index = ProviderSnapshotIndex(
            providers={},
            contexts_by_artifact={("spark", "runtime"): self._provider_context()},
            by_external_id={},
            snapshot_bytes=0,
            record_count=0,
        )

        with mock.patch.object(selection_module, "_MAX_SELECTED_CONTEXTS", 1), self.assertRaisesRegex(
            ValueError,
            "512 version-context ceiling",
        ):
            select_version_contexts(site=site, provider_index=provider_index)

    def test_select_development_context_returns_no_context_when_policy_disables_development(self) -> None:
        contexts = _select_development_context(
            "spark",
            self._artifact(),
            self._provider_context(),
            PublicationSelectionPolicy(development=False),
        )

        self.assertEqual(contexts, [])

    def test_select_line_head_contexts_return_empty_when_policy_is_missing_or_none(self) -> None:
        artifact = self._artifact()

        self.assertEqual(
            _select_line_head_contexts(
                "spark",
                artifact,
                self._provider_context(),
                PublicationSelectionPolicy(line_heads=None),
            ),
            [],
        )
        self.assertEqual(
            _select_line_head_contexts(
                "spark",
                artifact,
                self._provider_context(),
                PublicationSelectionPolicy(
                    line_heads=LineHeadSelectionPolicy(mode=LineHeadSelectionMode.NONE)
                ),
            ),
            [],
        )

    def test_select_release_contexts_cover_missing_policy_explicit_and_latest_n_modes(self) -> None:
        artifact = self._artifact(
            lifecycle=ArtifactLifecycleConfig(
                releases=[ExactReleaseConfig(version="4.0.0", release_line="4.0")],
                release_lines=[ReleaseLineConfig(key="4.0", latest="4.0.0")],
            )
        )
        provider_context = ProviderContextIndex(
            released_by_version={
                "4.0.1": (self._provider_record(RecordKind.RELEASED, version="4.0.1"),),
                "4.1.0": (self._provider_record(RecordKind.RELEASED, version="4.1.0"),),
            },
            candidates_by_version={},
            named_refs_by_key={},
            refs_by_ref={},
            line_heads_by_release_line={},
            development_records=(),
        )

        self.assertEqual(
            _select_release_contexts(
                "spark",
                artifact,
                provider_context,
                PublicationSelectionPolicy(releases=None),
            ),
            [],
        )
        self.assertEqual(
            [
                context.version
                for context in _select_release_contexts(
                    "spark",
                    artifact,
                    provider_context,
                    PublicationSelectionPolicy(
                        releases=ReleaseSelectionPolicy(
                            mode=ReleaseSelectionMode.EXPLICIT,
                            versions=["4.0.1"],
                        )
                    ),
                )
            ],
            ["4.0.1"],
        )
        self.assertEqual(
            [
                context.version
                for context in _select_release_contexts(
                    "spark",
                    artifact,
                    provider_context,
                    PublicationSelectionPolicy(
                        releases=ReleaseSelectionPolicy(
                            mode=ReleaseSelectionMode.LATEST_N,
                            count=2,
                        )
                    ),
                )
            ],
            ["4.1.0", "4.0.1"],
        )

    def test_select_candidate_contexts_skip_versions_filtered_to_zero_provider_records(self) -> None:
        artifact = self._artifact(
            publication_selection=PublicationSelectionPolicy(
                candidates=CandidateSelectionPolicy(
                    mode=CandidateSelectionMode.EXPLICIT,
                    versions=["4.1.0-rc1"],
                    external_ids=["winner"],
                )
            )
        )
        provider_context = ProviderContextIndex(
            released_by_version={},
            candidates_by_version={
                "4.1.0-rc1": (
                    self._provider_record(
                        RecordKind.CANDIDATE,
                        version="4.1.0-rc1",
                        external_id="other",
                    ),
                )
            },
            named_refs_by_key={},
            refs_by_ref={},
            line_heads_by_release_line={},
            development_records=(),
        )

        self.assertEqual(
            _select_candidate_contexts(
                "spark",
                artifact,
                provider_context,
                artifact.publication_selection,
            ),
            [],
        )

    def test_version_sort_key_rejects_unsortable_versions(self) -> None:
        with self.assertRaises(ValueError) as raised:
            _version_sort_key("main")

        self.assertIn("not sortable", str(raised.exception))

    def test_reference_resolution_and_existence_cover_lookup_kinds(self) -> None:
        route = KnownRoute(
            route_id="component:spark",
            origin_key="docs",
            path="/spark/guide/",
            component_slug="spark",
            route_kind="published",
        )
        reference_index = build_reference_index(
            routes_by_lookup_key={("docs", "/spark/guide/"): route},
            targets_by_reference={"component:spark": route},
            known_components=frozenset({"spark"}),
            artifacts_by_component={"spark": frozenset({"runtime"})},
            release_lines_by_artifact={("spark", "runtime"): frozenset({"4.0"})},
            releases_by_artifact={("spark", "runtime"): frozenset({"4.0.0"})},
            routes_by_path={"/spark/guide/": (route,)},
        )

        self.assertEqual(
            resolve_internal_reference(
                reference="route:/spark/guide/",
                source_origin_key="docs",
                reference_index=reference_index,
            ),
            route,
        )
        self.assertTrue(_reference_exists(reference="component:spark", reference_index=reference_index))
        self.assertTrue(_reference_exists(reference="artifact:spark/runtime", reference_index=reference_index))
        self.assertTrue(_reference_exists(reference="line:spark/runtime@4.0", reference_index=reference_index))
        self.assertTrue(_reference_exists(reference="release:spark/runtime@4.0.0", reference_index=reference_index))
        self.assertTrue(_reference_exists(reference="route:/spark/guide/", reference_index=reference_index))
        self.assertFalse(_reference_exists(reference="component:flink", reference_index=reference_index))

    def test_resolve_internal_reference_returns_none_for_malformed_strings_and_non_route_targets(self) -> None:
        route = KnownRoute(
            route_id="named:spark-main",
            origin_key="docs",
            path="/spark/guide/",
            component_slug="spark",
            route_kind="namedRef",
        )
        reference_index = build_reference_index(
            routes_by_lookup_key={("docs", "/spark/guide/"): route},
            targets_by_reference={"named:spark-main": route},
        )

        self.assertIsNone(
            resolve_internal_reference(
                reference="not-a-reference",
                source_origin_key="docs",
                reference_index=reference_index,
            )
        )
        self.assertEqual(
            resolve_internal_reference(
                reference="named:spark-main",
                source_origin_key="docs",
                reference_index=reference_index,
            ),
            route,
        )

    def test_validate_references_delegates_to_component_artifact_and_compatibility_helpers(self) -> None:
        artifact = self._artifact()
        artifact.authored = SimpleNamespace(compatibility=("artifact-compat",))
        component = SimpleNamespace(
            slug="spark",
            artifacts=(artifact,),
            authored=SimpleNamespace(compatibility=("component-compat",)),
        )
        planning = SimpleNamespace(
            site=SimpleNamespace(components=(component,)),
            selected_versions=SimpleNamespace(contexts=()),
            provider_index=ProviderSnapshotIndex(
                providers={},
                contexts_by_artifact={},
                by_external_id={},
                snapshot_bytes=0,
                record_count=0,
            ),
        )
        collector = DiagnosticCollector()
        reference_index = build_reference_index(routes_by_lookup_key={}, targets_by_reference={})

        with mock.patch(
            "apache_buildish_site_pipeline.evaluation.reference_index._build_context_reference_index",
            return_value=reference_index,
        ) as build_index, mock.patch(
            "apache_buildish_site_pipeline.evaluation.reference_index._validate_component_artifacts"
        ) as validate_component_artifacts, mock.patch(
            "apache_buildish_site_pipeline.evaluation.reference_index._validate_compatibility_references"
        ) as validate_compatibility_references, mock.patch(
            "apache_buildish_site_pipeline.evaluation.reference_index._validate_release_lines"
        ) as validate_release_lines, mock.patch(
            "apache_buildish_site_pipeline.evaluation.reference_index._validate_selection_references"
        ) as validate_selection_references:
            validate_references(
                planning=planning,
                publication_targets=(
                    PublishedTarget(
                        component_slug="spark",
                        target_id="component:spark",
                        origin_key="docs",
                        path="/spark/guide/",
                    ),
                ),
                collector=collector,
            )

        build_index.assert_called_once()
        validate_component_artifacts.assert_called_once_with(
            component=component,
            collector=collector,
        )
        validate_release_lines.assert_called_once_with(
            component_slug="spark",
            artifact=artifact,
            collector=collector,
        )
        validate_selection_references.assert_called_once_with(
            component_slug="spark",
            artifact=artifact,
            planning=planning,
            collector=collector,
        )
        self.assertEqual(validate_compatibility_references.call_count, 2)

    def test_validate_release_lines_reports_unknown_parent_and_cycles(self) -> None:
        collector = DiagnosticCollector()
        artifact = self._artifact(
            lifecycle=ArtifactLifecycleConfig.model_construct(
                release_lines=[
                    ReleaseLineConfig.model_construct(
                        key="4.0", latest="4.0.0", parent="3.0"
                    ),
                    ReleaseLineConfig.model_construct(
                        key="5.0", latest="5.0.0", parent="6.0"
                    ),
                    ReleaseLineConfig.model_construct(
                        key="6.0", latest="6.0.0", parent="5.0"
                    ),
                ]
            )
        )

        _validate_release_lines(
            component_slug="spark",
            artifact=artifact,
            collector=collector,
        )

        self.assertEqual(
            [entry.code for entry in collector.build()],
            [
                "reference-configuration-invalid",
                "reference-configuration-invalid",
                "reference-configuration-invalid",
            ],
        )
        self.assertTrue(
            _has_line_cycle(
                start_key="5.0",
                release_lines=tuple(artifact.lifecycle.release_lines),
            )
        )

    def test_validate_component_artifacts_reports_duplicate_keys(self) -> None:
        collector = DiagnosticCollector()
        component = SimpleNamespace(
            slug="spark",
            artifacts=(self._artifact(), self._artifact()),
        )

        _validate_component_artifacts(component=component, collector=collector)

        entries = collector.build()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].details["artifactKey"], "runtime")

    def test_validate_selection_references_reports_unknown_versions_refs_and_lines(self) -> None:
        collector = DiagnosticCollector()
        artifact = self._artifact(
            publication_selection=PublicationSelectionPolicy(
                named_refs=["unknown-ref"],
                releases=ReleaseSelectionPolicy(
                    mode=ReleaseSelectionMode.EXPLICIT,
                    versions=["4.0.1"],
                ),
            ),
            lifecycle=ArtifactLifecycleConfig(
                releases=[ExactReleaseConfig(version="4.0.0", release_line="missing-line")],
                release_lines=[ReleaseLineConfig(key="4.0", latest="4.0.0")],
            ),
        )
        planning = SimpleNamespace(
            provider_index=ProviderSnapshotIndex(
                providers={},
                contexts_by_artifact={},
                by_external_id={},
                snapshot_bytes=0,
                record_count=0,
            )
        )

        _validate_selection_references(
            component_slug="spark",
            artifact=artifact,
            planning=planning,
            collector=collector,
        )

        self.assertEqual(
            [entry.code for entry in collector.build()],
            [
                "reference-configuration-invalid",
                "reference-configuration-invalid",
                "reference-configuration-invalid",
            ],
        )

    def test_validate_selection_references_accepts_known_provider_versions_refs_and_lines(self) -> None:
        collector = DiagnosticCollector()
        artifact = self._artifact(
            publication_selection=PublicationSelectionPolicy(
                named_refs=["main"],
                releases=ReleaseSelectionPolicy(
                    mode=ReleaseSelectionMode.EXPLICIT,
                    versions=["4.0.1"],
                ),
            ),
            lifecycle=ArtifactLifecycleConfig(
                releases=[ExactReleaseConfig(version="4.0.0", release_line="4.0")],
                release_lines=[ReleaseLineConfig(key="4.0", latest="4.0.0")],
            ),
        )
        planning = SimpleNamespace(
            provider_index=ProviderSnapshotIndex(
                providers={},
                contexts_by_artifact={
                    ("spark", "runtime"): ProviderContextIndex(
                        released_by_version={
                            "4.0.1": (
                                self._provider_record(
                                    RecordKind.RELEASED,
                                    version="4.0.1",
                                ),
                            )
                        },
                        candidates_by_version={},
                        named_refs_by_key={},
                        refs_by_ref={},
                        line_heads_by_release_line={},
                        development_records=(),
                    )
                },
                by_external_id={},
                snapshot_bytes=0,
                record_count=0,
            )
        )

        _validate_selection_references(
            component_slug="spark",
            artifact=artifact,
            planning=planning,
            collector=collector,
        )

        self.assertEqual(collector.build(), ())

    def test_validate_selection_references_returns_early_when_publication_selection_is_missing(self) -> None:
        collector = DiagnosticCollector()

        _validate_selection_references(
            component_slug="spark",
            artifact=self._artifact(publication_selection=None),
            planning=SimpleNamespace(
                provider_index=ProviderSnapshotIndex(
                    providers={},
                    contexts_by_artifact={},
                    by_external_id={},
                    snapshot_bytes=0,
                    record_count=0,
                )
            ),
            collector=collector,
        )

        self.assertEqual(collector.build(), ())

    def test_validate_compatibility_references_accept_known_targets_and_report_unknown_ones(self) -> None:
        collector = DiagnosticCollector()
        route = KnownRoute(
            route_id="named:spark-main",
            origin_key="docs",
            path="/spark/guide/",
            component_slug="spark",
            route_kind="namedRef",
        )
        reference_index = build_reference_index(
            routes_by_lookup_key={("docs", "/spark/guide/"): route},
            targets_by_reference={"target:spark-main": route},
            known_components=frozenset({"spark"}),
            routes_by_path={"/spark/guide/": (route,)},
        )

        _validate_compatibility_references(
            component_slug="spark",
            artifact_key="runtime",
            compatibility=(
                CompatibilityAssertionConfig(
                    subject_ref="component:spark",
                    target_ref="route:/spark/guide/",
                    relation="compatibleWith",
                ),
                CompatibilityAssertionConfig(
                    subject_ref="component:missing",
                    target_ref="route:/missing/",
                    relation="compatibleWith",
                ),
            ),
            reference_index=reference_index,
            collector=collector,
        )

        entries = collector.build()
        self.assertEqual(len(entries), 2)
        self.assertEqual({entry.details["reference"] for entry in entries}, {"component:missing", "route:/missing/"})
        self.assertTrue(
            _reference_exists(
                reference="target:spark-main",
                reference_index=reference_index,
            )
        )

    @staticmethod
    def _artifact(
        *,
        publication_selection: PublicationSelectionPolicy | None = None,
        lifecycle: ArtifactLifecycleConfig | None = None,
    ) -> SimpleNamespace:
        return SimpleNamespace(
            key="runtime",
            source_binding=ResolvedSourceBinding(
                key="runtime",
                local_dir=Path("/workspace/components/runtime"),
                metadata_file=None,
                repository=None,
                default_branch=None,
            ),
            docs_root=Path("/workspace/components/runtime/docs"),
            assets_root=None,
            versioning=ArtifactVersioningConfig(
                development_ref="main",
                tag_pattern="^v.*$",
                named_refs=[NamedRefConfig(key="main", ref="refs/heads/main")],
            ),
            publication_selection=publication_selection,
            lifecycle=lifecycle,
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
    def _provider_context() -> ProviderContextIndex:
        return ProviderContextIndex(
            released_by_version={
                "4.0.0": (
                    SelectionAndReferenceIndexTests._provider_record(
                        RecordKind.RELEASED,
                        version="4.0.0",
                    ),
                )
            },
            candidates_by_version={},
            named_refs_by_key={},
            refs_by_ref={},
            line_heads_by_release_line={
                "4.0": (
                    SelectionAndReferenceIndexTests._provider_record(
                        RecordKind.LINE_HEAD,
                        release_line="4.0",
                        ref="refs/heads/4.0",
                    ),
                )
            },
            development_records=(
                SelectionAndReferenceIndexTests._provider_record(
                    RecordKind.DEVELOPMENT,
                    ref="main",
                ),
            ),
        )
