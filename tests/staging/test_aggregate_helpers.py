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

"""Direct coverage for staging aggregate helper branches."""

from __future__ import annotations

from datetime import UTC, datetime
from dataclasses import replace
from urllib.parse import quote
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from buildish_site_pipeline.cli.errors import StageIntegrityError
from buildish_site_pipeline.models.authored.site_catalog import (
    CompatibilityAssertionConfig,
    MountConfig,
)
from buildish_site_pipeline.models.authored.artifacts import (
    ArtifactLifecycleConfig,
    ExactReleaseConfig,
    ReleaseLineConfig,
    SupportWindow,
)
from buildish_site_pipeline.models.authored.component_metadata import (
    SupportStatusDefinition,
)
from buildish_site_pipeline.models.enums import (
    IndexBehavior,
    ContextAction,
    PublicationState,
    RecordKind,
    TrustClass,
)
from buildish_site_pipeline.planning.types import (
    IndexedProviderRecord,
    SelectedVersionContext,
    ResolvedOrigin,
    ResolvedPublicationPolicy,
)
from buildish_site_pipeline.staging.aggregates import (
    _artifact_docs_root,
    _artifact_for_context,
    _build_candidate_entries,
    _build_compatibility_entries,
    _build_components_entries,
    _build_content_index_entries,
    _build_artifacts_entries,
    _build_ref_entries,
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
from buildish_site_pipeline.staging.worker_protocol import (
    ContributionFileRefs,
    StagedPageContributionWire,
    UnitContributionManifestWire,
    WorkerResultWire,
    write_unit_manifest,
)
from buildish_site_pipeline.models.provider.provider_snapshot import DocsSource
from buildish_site_pipeline.staging.ownership import (
    OwnedContextInput, build_owned_units, source_root_for_context,
)
from buildish_site_pipeline.staging.page_provenance import build_page_source_index
from tests.support.staging import _work_layout


class AggregateHelperTests(unittest.TestCase):
    def _context_sources(self, build_plan, context):
        unit = replace(
            build_owned_units(build_plan)[0],
            contexts=(OwnedContextInput(
                context_id="chosen-by-coordinator", context=context,
                content_stage_root=Path("content/spark"), static_stage_root=Path("static/spark"),
            ),),
        )
        return build_page_source_index(build_plan, (unit,))[unit.unit_id]

    def test_docs_context_provenance_matrix_ignores_worker_version_labels(self):
        for kind in RecordKind:
            for original_root in (None, ".", "old/manual"):
                with self.subTest(kind=kind, original_root=original_root), tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    plan = self._source_build_plan(root)
                    mapping = None if original_root is None else DocsSource(
                        repository="https://forge.example/upstream", root=original_root, ref="release/4.0",
                    )
                    context = replace(
                        plan.selected_versions[0], kind=kind, version="4.0.0",
                        named_ref_key="preview", release_line="4.0",
                        provider_record=self._provider_record(kind, docs_source=mapping),
                    )
                    physical_root = source_root_for_context(context.docs_root, context)
                    result = _normalize_page_contribution(
                        layout=_work_layout(root), build_plan=plan,
                        sources=self._context_sources(plan, context),
                        contribution=self._contribution(
                            source_path=str(physical_root / "guide.md"),
                            version_kind="wrong", version_context={"tag": "false", "kind": "development"},
                            source={"key": "poison", "path": "poison.md", "viewRef": "main"},
                        ),
                    ).source
                    if mapping is None:
                        if kind is RecordKind.DEVELOPMENT:
                            self.assertEqual(result.path, "docs/guide.md")
                            self.assertEqual((result.view_ref, result.edit_ref), ("main", "main"))
                        else:
                            self.assertIsNone(result)
                    else:
                        self.assertEqual(result.model_dump(by_alias=True, exclude_none=True), {
                            "key": "runtime", "repository": "https://forge.example/upstream",
                            "path": "guide.md" if original_root == "." else "old/manual/guide.md",
                            "viewRef": "release/4.0",
                        })

    def test_direct_development_edit_links_require_a_declared_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = self._source_build_plan(root)
            for ref, edit in ((None, None), ("refs/heads/topic/docs", "refs/heads/topic/docs"), ("v4.0.0", None), ("arbitrary-bare-ref", None)):
                with self.subTest(ref=ref):
                    context = replace(plan.selected_versions[0], ref=ref)
                    result = _normalize_page_contribution(
                        layout=_work_layout(root), build_plan=plan,
                        sources=self._context_sources(plan, context), contribution=self._contribution(),
                    ).source
                    self.assertEqual((result.view_ref, result.edit_ref), (ref, edit))

    def test_provenance_rejects_mismatched_owned_file_associations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = self._source_build_plan(root)
            sources = self._context_sources(plan, plan.selected_versions[0])
            for overrides, message in (
                ({"component_slug": "other"}, "component"),
                ({"artifact_key": "unknown"}, "artifact"),
                ({"stage_relative_path": "content/spark/other.md"}, "filename"),
                ({"stage_relative_path": "content/outside/guide.md"}, "destination"),
                ({"stage_relative_path": "content/spark/../guide.md"}, "destination"),
                ({"stage_relative_path": "/outside/stage/guide.md"}, "destination"),
            ):
                for retained in (False, True):
                    with self.subTest(overrides=overrides, retained=retained), self.assertRaisesRegex(StageIntegrityError, message):
                        contribution = self._contribution(**overrides)
                        if retained:
                            _load_unit_contribution_manifests(
                                layout=_work_layout(root), build_plan=plan, worker_results=(),
                                retained_unit_manifests=(UnitContributionManifestWire(unit_id="component:spark", pages=(contribution,)),),
                            )
                        else:
                            _normalize_page_contribution(layout=_work_layout(root), build_plan=plan, sources=sources, contribution=contribution)
            with self.assertRaisesRegex(StageIntegrityError, "Unknown.*unit"):
                _load_unit_contribution_manifests(
                    layout=_work_layout(root), build_plan=plan, worker_results=(),
                    retained_unit_manifests=(UnitContributionManifestWire(unit_id="unknown", pages=()),),
                )

    def test_provenance_omits_cross_context_sources_and_coordinator_notices(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = self._source_build_plan(root)
            context = replace(plan.selected_versions[0], kind=RecordKind.RELEASED, version="4.0.0")
            # A valid development source does not belong to this release destination.
            result = _normalize_page_contribution(
                layout=_work_layout(root), build_plan=plan,
                sources=self._context_sources(plan, context), contribution=self._contribution(),
            )
            self.assertIsNone(result.source)
            context = replace(context, action=ContextAction.NOTICE)
            result = _normalize_page_contribution(
                layout=_work_layout(root), build_plan=plan,
                sources=self._context_sources(plan, context), contribution=self._contribution(
                    source_path=str(context.docs_root / "releases/4.0.0/guide.md"),
                ),
            )
            self.assertIsNone(result.source)

    def test_provenance_rejects_unresolved_context_ambiguity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = self._source_build_plan(root)
            unit = build_owned_units(plan)[0]
            unit = replace(unit, contexts=unit.contexts * 2)
            with self.assertRaisesRegex(StageIntegrityError, "Ambiguous"):
                _normalize_page_contribution(
                    layout=_work_layout(root), build_plan=plan,
                    sources=build_page_source_index(plan, (unit,))[unit.unit_id],
                    contribution=self._contribution(),
                )

    def test_nested_context_matches_exact_input_before_static_ancestor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = self._source_build_plan(root)
            parent = plan.selected_versions[0]
            child = replace(
                parent, kind=RecordKind.LINE_HEAD, release_line="4.0",
                provider_record=self._provider_record(RecordKind.LINE_HEAD, docs_source=DocsSource(
                    repository="https://github.com/example/original", root="manual", ref="maintenance/4.0",
                )),
            )
            unit = build_owned_units(plan)[0]
            unit = replace(unit, contexts=(*unit.contexts, OwnedContextInput(
                context_id="child", context=child, content_stage_root=Path("content/spark/4.0"), static_stage_root=Path("static/spark/4.0"),
            )))
            sources = build_page_source_index(plan, (unit,))[unit.unit_id]
            result = _normalize_page_contribution(
                layout=_work_layout(root), build_plan=plan, sources=sources,
                contribution=self._contribution(
                    source_path=str(child.docs_root / "maintenance/4.0/guide.md"),
                    stage_relative_path="content/spark/4.0/guide.md",
                    version_context={"kind": "development"},
                ),
            )
            self.assertEqual(result.source.path, "manual/guide.md")
            self.assertEqual(result.source.view_ref, "maintenance/4.0")
            self.assertIsNone(result.source.edit_ref)
            # An artifactless/static claim cannot attribute that file to the
            # component pages root, whose suffix would be maintenance/4.0/guide.md.
            with self.assertRaisesRegex(StageIntegrityError, "filename"):
                _normalize_page_contribution(
                    layout=_work_layout(root), build_plan=plan, sources=sources,
                    contribution=self._contribution(
                        artifact_key=None,
                        source_path=str(child.docs_root / "maintenance/4.0/guide.md"),
                        stage_relative_path="content/spark/4.0/guide.md",
                    ),
                )

    def test_custom_physical_root_localized_suffix_and_consumer_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = self._source_build_plan(root)
            context = replace(
                plan.selected_versions[0], docs_root=root / "components/runtime/exported/manual",
                kind=RecordKind.RELEASED, version="4.0.0",
                provider_record=self._provider_record(RecordKind.RELEASED, docs_source=DocsSource(
                    repository="https://github.com/example/original", root="manual/überblick", ref="releases/4.0",
                )),
            )
            result = _normalize_page_contribution(
                layout=_work_layout(root), build_plan=plan,
                sources=self._context_sources(plan, context),
                contribution=self._contribution(
                    source_path=str(context.docs_root / "releases/4.0.0/de/_index.md"),
                    stage_relative_path="content/spark/de/_index.md", locale="de",
                ),
            ).source
            self.assertEqual(result.path, "manual/überblick/de/_index.md")
            # Consumer recipe assertion only: this does not execute Hugo. Its
            # source-link partial escapes segments while preserving separators.
            url = f"{result.repository}/blob/{quote(result.view_ref, safe='/')}/{quote(result.path, safe='/')}"
            self.assertEqual(url, "https://github.com/example/original/blob/releases/4.0/manual/%C3%BCberblick/de/_index.md")
            self.assertIsNone(result.edit_ref)

    def _contribution(self, **overrides) -> StagedPageContributionWire:
        payload = {
            "stage_relative_path": "content/spark/guide.md",
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

    @staticmethod
    def _source_build_plan(workspace_root: Path) -> SimpleNamespace:
        source_binding = SimpleNamespace(
            key="runtime",
            local_dir=workspace_root / "components/runtime",
            repository="https://github.com/example/runtime",
            default_branch="main",
        )
        publication = SimpleNamespace(artifact_routing="shared", default_artifact=None, artifact_publications=(), component_path="/spark/", development_path="/spark/", docs_path="/spark/", assets_path="/spark/assets/")
        component = SimpleNamespace(
            slug="spark", content_source=source_binding,
            pages_root=source_binding.local_dir / "docs", assets_root=None,
            publication=publication,
            artifacts=(SimpleNamespace(key="runtime", source_binding=source_binding),),
        )
        retained = SimpleNamespace(**vars(component))
        retained.slug = "retained"
        retained.publication = SimpleNamespace(artifact_routing="shared", default_artifact=None, artifact_publications=(), component_path="/retained/", assets_path="/retained/assets/")
        return SimpleNamespace(
            workspace_root=workspace_root,
            selected_versions=(SelectedVersionContext(
                component_slug="spark", artifact_key="runtime", kind=RecordKind.DEVELOPMENT,
                source_binding=source_binding, docs_root=source_binding.local_dir / "docs",
                assets_root=None, ref="main",
            ),),
            site=SimpleNamespace(
                sources={"runtime": source_binding}, components=(component, retained),
                site_pages_root=None, site_assets_root=None, vendor_assets=(),
            ),
        )

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
            "tag": "v4.0.0",
            "publication_state": PublicationState.PUBLISHED,
            "identity_verified": True,
            "provider_record": self._provider_record(RecordKind.RELEASED),
        }
        payload.update(overrides)
        return SimpleNamespace(**payload)

    def test_translation_helpers_group_links_per_page_and_emit_sorted_sets(self) -> None:
        contributions = (
            self._contribution(
                stage_relative_path="content/spark/guide-en.md",
                locale="en",
                translation_key="guide.install",
                title="Guide",
            ),
            self._contribution(
                stage_relative_path="content/spark/guide-de.md",
                locale="de",
                translation_key="guide.install",
                title="Anleitung",
                public_path="/de/spark/guide",
                public_url="https://docs.example.org/de/spark/guide",
                canonical_url="https://docs.example.org/de/spark/guide",
            ),
            self._contribution(
                stage_relative_path="content/spark/guide-fr.md",
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
            [link.locale for link in links_by_page[("spark", "runtime", "content/spark/guide-en.md")]],
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
                desired_versions=(),
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

    def test_build_ref_entries_skips_component_owned_development_contexts_without_artifacts(self) -> None:
        build_plan = SimpleNamespace(
                desired_versions=(),
            site=SimpleNamespace(
                components=(SimpleNamespace(slug="spark"),),
            ),
            selected_versions=(
                self._context(
                    kind=RecordKind.DEVELOPMENT,
                    artifact_key=None,
                    ref=None,
                    provider_record=None,
                ),
            ),
        )

        entries = _build_ref_entries(build_plan)

        self.assertEqual(entries, [])

    def test_component_and_artifact_entries_preserve_repository_metadata(self) -> None:
        publication = SimpleNamespace(artifact_routing="shared", default_artifact=None, artifact_publications=(),
            origin=SimpleNamespace(
                key="docs",
                base_url="https://docs.example.org",
                hostname="docs.example.org",
            ),
            component_path="/spark/",
            development_path="/spark/development/",
            docs_path="/spark/development/",
            assets_path="/spark/assets/",
            component_url="https://docs.example.org/spark/",
            development_url="https://docs.example.org/spark/development/",
            docs_url="https://docs.example.org/spark/development/",
            assets_url="https://docs.example.org/spark/assets/",
        )
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            component = SimpleNamespace(
                slug="spark",
                authored=SimpleNamespace(display_name=None, weight=100, group="data-platform"),
                repository_document=SimpleNamespace(
                    component=SimpleNamespace(display_name="Apache Spark"),
                    lifecycle=SimpleNamespace(latest_stable="4.0.0"),
                ),
                publication=publication,
                artifacts=(
                    SimpleNamespace(
                        key="runtime",
                        authored=SimpleNamespace(display_name="Runtime", docs_root=Path("docs/runtime")),
                        source_binding=SimpleNamespace(key="apache-spark"),
                        docs_root=workspace_root / "generated/runtime-docs",
                        versioning=None,
                        lifecycle=SimpleNamespace(
                            latest_stable="4.0.0",
                            support_policy_url="https://docs.example.org/support",
                            release_lines=None,
                            releases=None,
                        ),
                        support_status_vocabulary={
                            "active": SupportStatusDefinition(display_name="Active", order=10),
                        },
                    ),
                ),
            )
            build_plan = SimpleNamespace(
                desired_versions=(),
                workspace_root=workspace_root,
                site=SimpleNamespace(components=(component,)),
                selected_versions=(),
            )

            component_entries = _build_components_entries(build_plan)
            artifact_entries = _build_artifacts_entries(build_plan)

        self.assertEqual(component_entries[0].display_name, "Apache Spark")
        self.assertEqual(component_entries[0].latest_stable, "4.0.0")
        self.assertEqual(artifact_entries[0].support_status_vocabulary["active"].display_name, "Active")

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

    def test_compatibility_and_mount_entries_cover_component_and_artifact_owned_values(
        self,
    ) -> None:
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
            binding=SimpleNamespace(
                compatibility=(artifact_assertion,),
                mounts=(artifact_mount,),
            ),
        )
        build_plan = SimpleNamespace(
            desired_versions=(),
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
            ),
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
            build_plan = self._source_build_plan(workspace_root)

            entries = _build_content_index_entries(
                build_plan=build_plan,
                page_contributions=(
                    self._contribution(
                        description="Install the runtime guide.",
                        source_path=str(source_path),
                        source={
                            "key": "runtime",
                            "path": "docs/guide.md",
                            "repository": "https://github.com/example/runtime",
                            "viewRef": "main",
                            "editRef": "main",
                        },
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

        self.assertEqual(entries[0].source.path, "docs/guide.md")
        self.assertEqual(entries[0].source.repository, "https://github.com/example/runtime")
        self.assertEqual(entries[0].description, "Install the runtime guide.")
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
                authored=SimpleNamespace(docs_root=None),
                docs_root=workspace_root / "components/runtime/docs",
            )
            outside_artifact = SimpleNamespace(
                key="runtime",
                authored=SimpleNamespace(docs_root=None),
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
            build_plan = self._source_build_plan(workspace_root)
            absolute_stage_path = layout.next_stage_root / "content/spark/guide.md"
            absolute_stage_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path = layout.fragments_root / "component_spark.json"
            write_unit_manifest(
                manifest_path,
                UnitContributionManifestWire(
                    unit_id="component:spark",
                    pages=(
                        self._contribution(
                            stage_relative_path=str(absolute_stage_path),
                            source_path=str(
                                workspace_root / "components/runtime/docs/guide.md"
                            ),
                        ),
                    ),
                ),
            )

            manifests = _load_unit_contribution_manifests(
                layout=layout,
                build_plan=build_plan,
                worker_results=(
                    WorkerResultWire(
                        unit_id="component:spark",
                        contribution_files=ContributionFileRefs(unit_manifest=str(manifest_path)),
                    ),
                    WorkerResultWire(unit_id="component:skip"),
                ),
                retained_unit_manifests=(
                    UnitContributionManifestWire(
                        unit_id="component:retained",
                        pages=(
                            self._contribution(
                                component_slug="retained",
                                artifact_key=None,
                                stage_relative_path="content/retained/guide.md",
                                source_path="/outside/generated/guide.md",
                                source={
                                    "key": "untrusted",
                                    "path": "private.md",
                                    "repository": "https://example.invalid/untrusted",
                                },
                            ),
                        ),
                    ),
                ),
            )

            self.assertEqual(manifests[0].unit_id, "component:retained")
            self.assertIsNone(manifests[0].pages[0].source_path)
            self.assertIsNone(manifests[0].pages[0].source)
            self.assertEqual(
                manifests[1].pages[0].stage_relative_path,
                "content/spark/guide.md",
            )
            self.assertEqual(
                manifests[1].pages[0].source_path,
                "components/runtime/docs/guide.md",
            )
            self.assertEqual(manifests[1].pages[0].source.path, "docs/guide.md")
            self.assertEqual(manifests[1].pages[0].source.view_ref, "main")
            relative = self._contribution(stage_relative_path="content/spark/guide.md")
            normalized = _normalize_page_contribution(
                layout=layout,
                build_plan=build_plan,
                sources=build_page_source_index(build_plan, build_owned_units(build_plan))["component:spark"],
                contribution=relative,
            )
            self.assertEqual(normalized.source_path, relative.source_path)
            self.assertEqual(normalized.source.path, "docs/guide.md")

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

    def test_source_provenance_overwrites_untrusted_retained_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            build_plan = self._source_build_plan(workspace_root)
            normalized = _normalize_page_contribution(
                layout=_work_layout(workspace_root),
                build_plan=build_plan,
                sources=build_page_source_index(build_plan, build_owned_units(build_plan))["component:spark"],
                contribution=self._contribution(
                    source={
                        "key": "stale",
                        "path": "old/guide.md",
                        "repository": "https://example.invalid/stale",
                        "viewRef": "old",
                        "editRef": "old",
                    },
                ),
            )

            self.assertEqual(
                normalized.source.model_dump(by_alias=True, exclude_none=True),
                {
                    "key": "runtime",
                    "path": "docs/guide.md",
                    "repository": "https://github.com/example/runtime",
                    "viewRef": "main",
                    "editRef": "main",
                },
            )

    def test_source_provenance_handles_local_only_and_shorthand_bindings(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            build_plan = self._source_build_plan(workspace_root)
            source_binding = build_plan.site.sources["runtime"]
            source_binding.repository = None
            source_binding.default_branch = None
            normalized = _normalize_page_contribution(
                layout=_work_layout(workspace_root),
                build_plan=build_plan,
                sources=build_page_source_index(build_plan, build_owned_units(build_plan))["component:spark"],
                contribution=self._contribution(),
            )

            self.assertEqual(normalized.source.key, "runtime")
            self.assertEqual(normalized.source.path, "docs/guide.md")
            self.assertIsNone(normalized.source.repository)
            self.assertIsNone(normalized.source.view_ref)
            self.assertIsNone(normalized.source.edit_ref)

            shorthand_binding = SimpleNamespace(
                key="component:spark",
                local_dir=workspace_root / "components/runtime",
                repository=None,
                default_branch=None,
            )
            build_plan.site.sources = {}
            build_plan.site.components[0].content_source = shorthand_binding
            normalized_shorthand = _normalize_page_contribution(
                layout=_work_layout(workspace_root),
                build_plan=build_plan,
                sources=build_page_source_index(build_plan, build_owned_units(build_plan))["component:spark"],
                contribution=self._contribution(artifact_key=None),
            )

            self.assertIsNone(normalized_shorthand.source)


class _ModelDumpOnly:
    def model_dump(self, **_: object) -> dict[str, str]:
        return {"hello": "world"}
