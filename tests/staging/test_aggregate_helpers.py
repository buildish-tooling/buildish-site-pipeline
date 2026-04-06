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

"""Direct coverage for staging aggregate helper branches."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from apache_buildish_site_pipeline.cli.errors import StageIntegrityError
from apache_buildish_site_pipeline.models.catalog import (
    ArtifactLifecycleConfig,
    CompatibilityAssertionConfig,
    ExactReleaseConfig,
    MountConfig,
    ReleaseLineConfig,
    SupportWindow,
)
from apache_buildish_site_pipeline.models.enums import (
    IndexBehavior,
    PublicationState,
    RecordKind,
    TrustClass,
)
from apache_buildish_site_pipeline.planning.types import (
    IndexedProviderRecord,
    ResolvedOrigin,
    ResolvedPublicationPolicy,
)
from apache_buildish_site_pipeline.staging.aggregates import (
    _artifact_docs_root,
    _artifact_for_context,
    _build_candidate_entries,
    _build_compatibility_entries,
    _build_content_index_entries,
    _build_mount_entries,
    _build_redirect_resolution_index,
    _build_route_entries,
    _build_translation_entries,
    _latest_candidate_summary,
    _latest_release_summary,
    _load_unit_contribution_manifests,
    _normalize_page_contribution,
    _parse_timestamp,
    _provider_mapping,
    _provider_record_for_context,
    _required_context_ref,
    _required_context_version,
    _required_origin,
    _resolve_redirect_target_url,
    _serialize_item,
    _support_status_for_context,
    _support_window_for_context,
    _translations_by_page,
    _validated_unit_manifest_path,
)
from apache_buildish_site_pipeline.staging.worker_protocol import (
    ContributionFileRefs,
    StagedPageContributionWire,
    UnitContributionManifestWire,
    WorkerResultWire,
    write_unit_manifest,
)
from tests.support.staging import _work_layout


class AggregateHelperTests(unittest.TestCase):
    def _contribution(self, **overrides) -> StagedPageContributionWire:
        payload = {
            "stage_relative_path": "content/components/spark/guide.md",
            "component_slug": "spark",
            "artifact_key": "runtime",
            "section": "docs",
            "page_kind": "docs-page",
            "public_path": "/spark/guide",
            "public_url": "https://docs.example.org/spark/guide",
            "component_path": "/spark/",
            "component_url": "https://docs.example.org/spark/",
            "origin_key": "docs",
            "source_path": "components/runtime/docs/guide.md",
            "canonical_url": "https://docs.example.org/spark/guide",
        }
        payload.update(overrides)
        return StagedPageContributionWire(**payload)

    def _provider_record(self, kind: RecordKind, **overrides) -> IndexedProviderRecord:
        payload = {
            "provider": "github",
            "kind": kind,
            "component_slug": "spark",
            "artifact_key": "runtime",
            "external_id": "123",
            "external_url": "https://example.invalid/releases/123",
            "version": "4.0.0",
            "display_version": "4.0.0",
            "tag": "v4.0.0",
            "ref": "refs/tags/v4.0.0",
            "commit_sha": "abc123",
            "named_ref_key": None,
            "release_line": "4.x",
            "release_line_ancestors": (),
            "support_status": None,
            "publication_state": PublicationState.PUBLISHED,
            "maturity": "ga",
            "candidate_sequence": None,
            "vote_status": None,
            "created_at": "2024-01-01T00:00:00Z",
            "published_at": "2024-01-02T00:00:00Z",
            "updated_at": None,
            "urls": {},
            "assets": (),
        }
        payload.update(overrides)
        return IndexedProviderRecord(**payload)

    def _context(self, **overrides) -> SimpleNamespace:
        payload = {
            "component_slug": "spark",
            "artifact_key": "runtime",
            "kind": RecordKind.RELEASED,
            "version": "4.0.0",
            "ref": "refs/tags/v4.0.0",
            "named_ref_key": None,
            "release_line": "4.x",
            "display_version": "4.0.0",
            "maturity": "ga",
            "provider_record": self._provider_record(RecordKind.RELEASED),
        }
        payload.update(overrides)
        return SimpleNamespace(**payload)

    def test_translation_helpers_group_links_per_page_and_emit_sorted_sets(self) -> None:
        contributions = (
            self._contribution(
                stage_relative_path="content/components/spark/guide-en.md",
                locale="en",
                translation_key="guide.install",
                title="Guide",
            ),
            self._contribution(
                stage_relative_path="content/components/spark/guide-de.md",
                locale="de",
                translation_key="guide.install",
                title="Anleitung",
                public_path="/de/spark/guide",
                public_url="https://docs.example.org/de/spark/guide",
                canonical_url="https://docs.example.org/de/spark/guide",
            ),
            self._contribution(
                stage_relative_path="content/components/spark/guide-fr.md",
                locale="fr",
                translation_key="guide.install",
                title="Guide FR",
                public_path="/fr/spark/guide",
                public_url="https://docs.example.org/fr/spark/guide",
                canonical_url="https://docs.example.org/fr/spark/guide",
            ),
            self._contribution(locale=None, translation_key="ignored"),
        )

        links_by_page = _translations_by_page(contributions)
        sets = _build_translation_entries(contributions)

        self.assertEqual(
            [link.locale for link in links_by_page[("spark", "runtime", "content/components/spark/guide-en.md")]],
            ["de", "fr"],
        )
        self.assertEqual(
            [link.locale for link in sets[0].entries],
            ["de", "en", "fr"],
        )

    def test_route_and_redirect_helpers_cover_docs_routes_external_targets_and_unknown_origins(self) -> None:
        origin = ResolvedOrigin(
            key="docs",
            base_url="https://docs.example.org",
            hostname="docs.example.org",
            canonical=True,
        )
        publication = ResolvedPublicationPolicy(
            origin=origin,
            component_path="/spark/",
            development_path="/spark/dev/",
            docs_path="/spark/docs/",
            assets_path="/spark/assets/",
            component_url="https://docs.example.org/spark/",
            development_url="https://docs.example.org/spark/dev/",
            docs_url="https://docs.example.org/spark/docs/",
            assets_url="https://docs.example.org/spark/assets/",
            canonical_path=None,
            aliases=(),
            redirects=(),
        )
        build_plan = SimpleNamespace(
            site=SimpleNamespace(
                origins={"docs": origin},
                components=(SimpleNamespace(slug="spark", publication=publication),),
            ),
            selected_versions=(),
        )

        routes = _build_route_entries(build_plan)
        routes_by_lookup_key, targets_by_reference = _build_redirect_resolution_index(build_plan)

        self.assertTrue(any(entry.section == "docs" for entry in routes))
        self.assertEqual(routes_by_lookup_key[("docs", "/spark/docs/")], ("docs", "/spark/docs/"))
        self.assertEqual(
            _resolve_redirect_target_url(
                target="https://downloads.example.org/spark",
                source_origin_key="docs",
                routes_by_lookup_key=routes_by_lookup_key,
                targets_by_reference=targets_by_reference,
                origins_by_key={"docs": origin},
            ),
            "https://downloads.example.org/spark",
        )
        with self.assertRaisesRegex(StageIntegrityError, "Unknown publication origin"):
            _required_origin({}, "missing")

    def test_candidate_entries_and_latest_summaries_choose_highest_signal_context(self) -> None:
        candidate_one = self._context(
            kind=RecordKind.CANDIDATE,
            version="4.1.0-rc1",
            provider_record=self._provider_record(
                RecordKind.CANDIDATE,
                version="4.1.0-rc1",
                display_version="4.1.0 RC1",
                candidate_sequence=1,
                vote_status="open",
            ),
        )
        candidate_two = self._context(
            kind=RecordKind.CANDIDATE,
            version="4.1.0-rc2",
            provider_record=self._provider_record(
                RecordKind.CANDIDATE,
                version="4.1.0-rc2",
                display_version="4.1.0 RC2",
                candidate_sequence=2,
                vote_status="passed",
            ),
        )
        released_old = self._context(
            version="4.0.0",
            provider_record=self._provider_record(
                RecordKind.RELEASED,
                version="4.0.0",
                published_at="2024-01-02T00:00:00Z",
            ),
        )
        released_new = self._context(
            version="4.1.0",
            provider_record=self._provider_record(
                RecordKind.RELEASED,
                version="4.1.0",
                display_version="4.1.0",
                published_at="2024-02-01T00:00:00Z",
            ),
        )

        entries = _build_candidate_entries(
            SimpleNamespace(selected_versions=(candidate_one, released_old, candidate_two))
        )

        self.assertEqual([entry.version for entry in entries], ["4.1.0-rc1", "4.1.0-rc2"])
        self.assertIsNone(_latest_release_summary([]))
        self.assertEqual(_latest_release_summary([released_old, released_new]).version, "4.1.0")
        self.assertIsNone(_latest_candidate_summary([]))
        self.assertEqual(_latest_candidate_summary([candidate_one, candidate_two]).version, "4.1.0-rc2")

    def test_compatibility_and_mount_entries_cover_component_and_artifact_owned_values(self) -> None:
        component_assertion = CompatibilityAssertionConfig(
            subject_ref="component:spark",
            target_ref="route:/spark/",
            relation="supports",
        )
        artifact_assertion = CompatibilityAssertionConfig(
            subject_ref="release:spark/runtime@4.0.0",
            target_ref="line:spark/runtime@4.x",
            relation="supersedes",
        )
        component_mount = MountConfig(
            source="generated/component-assets",
            mount_path="/spark/component-assets/",
            kind="generatedAssets",
            trust_class=TrustClass.PASSIVE,
            index_behavior=IndexBehavior.METADATA_ONLY,
        )
        artifact_mount = MountConfig(
            source="generated/api",
            mount_path="/spark/api/",
            kind="generatedApi",
            trust_class=TrustClass.ACTIVE,
            ownership="custom:api",
        )
        artifact = SimpleNamespace(
            key="runtime",
            authored=SimpleNamespace(
                compatibility=(artifact_assertion,),
                mounts=(artifact_mount,),
            ),
        )
        build_plan = SimpleNamespace(
            site=SimpleNamespace(
                components=(
                    SimpleNamespace(
                        slug="spark",
                        authored=SimpleNamespace(
                            compatibility=(component_assertion,),
                            mounts=(component_mount,),
                        ),
                        artifacts=(artifact,),
                    ),
                )
            )
        )

        compatibility_entries = _build_compatibility_entries(build_plan)
        mount_entries = _build_mount_entries(build_plan)

        self.assertEqual(compatibility_entries[0].subject_id, "component:spark")
        self.assertEqual(
            compatibility_entries[1].subject_id,
            "artifact:spark:runtime:release:spark/runtime@4.0.0",
        )
        self.assertEqual(mount_entries[0].owner_id, "component:spark")
        self.assertEqual(mount_entries[1].owner_id, "custom:api")

    def test_content_index_entries_and_provider_mapping_cover_url_and_provider_edges(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            source_path = workspace_root / "components/runtime/docs/guide.md"
            source_path.parent.mkdir(parents=True, exist_ok=True)
            source_path.write_text("guide\n", encoding="utf-8")
            build_plan = SimpleNamespace(workspace_root=workspace_root)

            entries = _build_content_index_entries(
                build_plan=build_plan,
                page_contributions=(
                    self._contribution(
                        source_path=str(source_path),
                        version_context={
                            "provider": {
                                "key": "github",
                                "externalId": "123",
                                "ignored": 7,
                            }
                        },
                        version_kind=RecordKind.RELEASED,
                        version="4.0.0",
                    ),
                ),
            )

        self.assertEqual(entries[0].source_path, "components/runtime/docs/guide.md")
        self.assertEqual((entries[0].provider, entries[0].external_id), ("github", "123"))
        self.assertEqual(entries[0].version_kind, RecordKind.RELEASED)
        self.assertIsNone(_provider_mapping({"provider": "github"}))
        self.assertEqual(
            _provider_mapping({"provider": {"key": "github", "externalId": "123", "ignored": 7}}),
            {"key": "github", "externalId": "123"},
        )
        with self.assertRaisesRegex(StageIntegrityError, "missing a public URL"):
            _build_content_index_entries(
                build_plan=SimpleNamespace(workspace_root=Path("/workspace")),
                page_contributions=(
                    self._contribution(public_url=None, canonical_url=None),
                ),
            )

    def test_support_and_context_helpers_cover_exact_line_and_missing_metadata_paths(self) -> None:
        exact_support_window = SupportWindow(end_of_support_date="2025-01-01T00:00:00Z")
        line_support_window = SupportWindow(end_of_support_date="2026-01-01T00:00:00Z")
        artifact = SimpleNamespace(
            key="runtime",
            lifecycle=ArtifactLifecycleConfig(
                release_lines=[
                    ReleaseLineConfig(
                        key="4.x",
                        latest="4.1.0",
                        support_status="maintenance",
                        support_window=line_support_window,
                    )
                ],
                releases=[
                    ExactReleaseConfig(
                        version="4.0.0",
                        release_line="4.x",
                        support_status="active",
                        support_window=exact_support_window,
                    )
                ],
            ),
            authored=SimpleNamespace(),
            docs_root=Path("/workspace/components/runtime/docs"),
        )
        exact_context = self._context(version="4.0.0")
        line_context = self._context(version="4.1.0")

        self.assertEqual(_support_status_for_context(artifact, exact_context), "active")
        self.assertEqual(_support_window_for_context(artifact, exact_context), exact_support_window)
        self.assertEqual(_support_status_for_context(artifact, line_context), "maintenance")
        self.assertEqual(_support_window_for_context(artifact, line_context), line_support_window)
        self.assertIsNone(_support_status_for_context(SimpleNamespace(lifecycle=None), exact_context))
        self.assertIsNone(_support_window_for_context(SimpleNamespace(lifecycle=None), exact_context))
        with self.assertRaisesRegex(ValueError, "Artifact runtime not found"):
            _artifact_for_context(SimpleNamespace(slug="spark", artifacts=()), exact_context)
        with self.assertRaisesRegex(StageIntegrityError, "missing provider metadata"):
            _provider_record_for_context(self._context(provider_record=None))
        with self.assertRaisesRegex(StageIntegrityError, "missing version"):
            _required_context_version(self._context(version=None))
        with self.assertRaisesRegex(StageIntegrityError, "missing ref"):
            _required_context_ref(self._context(ref=None))

    def test_artifact_docs_root_parse_timestamp_and_serialize_item_cover_fallback_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            authored_path_artifact = SimpleNamespace(
                key="runtime",
                authored=SimpleNamespace(docs_root=Path("docs/rendered")),
                docs_root=workspace_root / "generated/docs",
            )
            authored_string_artifact = SimpleNamespace(
                key="runtime",
                authored=SimpleNamespace(docs_root="docs/from-string"),
                docs_root=workspace_root / "generated/docs",
            )
            relative_artifact = SimpleNamespace(
                key="runtime",
                authored=SimpleNamespace(),
                docs_root=workspace_root / "components/runtime/docs",
            )
            outside_artifact = SimpleNamespace(
                key="runtime",
                authored=SimpleNamespace(),
                docs_root=Path("/outside/docs"),
            )

            self.assertEqual(_artifact_docs_root(authored_path_artifact, workspace_root), "docs/rendered")
            self.assertEqual(_artifact_docs_root(authored_string_artifact, workspace_root), "docs/from-string")
            self.assertEqual(_artifact_docs_root(relative_artifact, workspace_root), "components/runtime/docs")
            with self.assertRaisesRegex(StageIntegrityError, "repo-relative"):
                _artifact_docs_root(outside_artifact, workspace_root)

        now = datetime(2024, 1, 1, tzinfo=UTC)
        self.assertIs(_parse_timestamp(now), now)
        self.assertEqual(_parse_timestamp("2024-01-02T00:00:00Z"), datetime(2024, 1, 2, tzinfo=UTC))
        self.assertIn('"hello": "world"', _serialize_item(_ModelDumpOnly(), indent="  "))
        self.assertIn('"answer": 42', _serialize_item({"answer": 42}, indent=""))

    def test_manifest_loading_normalizes_absolute_stage_paths_and_rejects_non_files(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            layout = _work_layout(workspace_root)
            absolute_stage_path = layout.next_stage_root / "content/components/spark/guide.md"
            absolute_stage_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path = layout.fragments_root / "component_spark.json"
            write_unit_manifest(
                manifest_path,
                UnitContributionManifestWire(
                    unit_id="component:spark",
                    pages=(
                        self._contribution(stage_relative_path=str(absolute_stage_path)),
                    ),
                ),
            )

            manifests = _load_unit_contribution_manifests(
                layout=layout,
                worker_results=(
                    WorkerResultWire(
                        unit_id="component:spark",
                        contribution_files=ContributionFileRefs(unit_manifest=str(manifest_path)),
                    ),
                    WorkerResultWire(unit_id="component:skip"),
                ),
                retained_unit_manifests=(UnitContributionManifestWire(unit_id="retained"),),
            )

            self.assertEqual(manifests[0].unit_id, "retained")
            self.assertEqual(
                manifests[1].pages[0].stage_relative_path,
                "content/components/spark/guide.md",
            )
            relative = self._contribution(stage_relative_path="content/components/spark/guide.md")
            self.assertIs(_normalize_page_contribution(layout=layout, contribution=relative), relative)

            manifest_path.unlink()
            manifest_path.mkdir()
            with self.assertRaisesRegex(StageIntegrityError, "normal file"):
                _validated_unit_manifest_path(
                    layout=layout,
                    result=WorkerResultWire(
                        unit_id="component:spark",
                        contribution_files=ContributionFileRefs(unit_manifest=str(manifest_path)),
                    ),
                )


class _ModelDumpOnly:
    def model_dump(self, **_: object) -> dict[str, str]:
        return {"hello": "world"}