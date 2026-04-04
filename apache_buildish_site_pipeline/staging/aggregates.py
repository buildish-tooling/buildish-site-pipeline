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

"""Aggregate builders for finalized stage data files and page metadata."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from datetime import UTC, datetime
import os
from pathlib import Path
import tempfile
from typing import Any

from apache_buildish_site_pipeline.cli_errors import StageIntegrityError
from apache_buildish_site_pipeline.models.aggregates import (
    ArtifactsDataEntry,
    CandidateAggregateEntry,
    CompatibilityAggregateEntry,
    ComponentsDataEntry,
    ContentIndexEntry,
    LatestCandidateSummary,
    LatestReleaseSummary,
    MountAggregateEntry,
    ProvidersDataEntry,
    RedirectAggregateEntry,
    RefAggregateEntry,
    ReleaseAggregateEntry,
    RouteAggregateEntry,
    TranslationSetAggregateEntry,
)
from apache_buildish_site_pipeline.models.catalog import CompatibilityAssertionConfig, MountConfig
from apache_buildish_site_pipeline.models.enums import RecordKind
from apache_buildish_site_pipeline.models.planning_stage_contract import PipelineDiagnosticEntry, StageDataFiles, StageManifestV1, StageRoots
from apache_buildish_site_pipeline.models.planning_stage_contract import StageCommand
from apache_buildish_site_pipeline.models.provider_snapshot import ProviderSnapshotV1
from apache_buildish_site_pipeline.models.staged_front_matter import PipelineComponentFrontMatter, TranslationLinkSummary
from apache_buildish_site_pipeline.planning.types import IndexedProviderRecord, ResolvedArtifactConfig, ResolvedComponentConfig, SelectedVersionContext

from .front_matter import build_component_front_matter, build_page_front_matter, build_translation_link, finalize_staged_page
from .public_safety import public_source_path, sanitize_public_diagnostics
from .publication_paths import public_path_for_context, target_id_for_context
from .types import EffectiveBuildPlan, WorkRootLayout
from .worker_protocol import StagedPageContributionWire, WorkerResultWire, read_unit_manifest


def finalize_pages_and_write_aggregates(
    *,
    layout: WorkRootLayout,
    command: StageCommand,
    build_plan: EffectiveBuildPlan,
    diagnostics: tuple[Any, ...],
    provider_snapshot: ProviderSnapshotV1,
    worker_results: tuple[WorkerResultWire, ...],
) -> StageManifestV1:
    """Finalize page metadata, write aggregate files, and emit the stage manifest."""

    page_contributions = _load_page_contributions(layout=layout, worker_results=worker_results)
    component_front_matter_by_slug = {
        component.slug: build_component_front_matter(component, build_plan.selected_versions)
        for component in build_plan.site.components
    }
    _finalize_staged_pages(
        layout=layout,
        page_contributions=page_contributions,
        component_front_matter_by_slug=component_front_matter_by_slug,
    )
    data_files = _write_aggregate_files(
        layout=layout,
        build_plan=build_plan,
        diagnostics=diagnostics,
        provider_snapshot=provider_snapshot,
        page_contributions=page_contributions,
    )
    manifest = StageManifestV1(
        schema_version=1,
        stage_layout_version=1,
        generated_at=datetime.now(UTC),
        command=command,
        front_matter_format="yaml",
        aggregate_format="json",
        roots=StageRoots(content="content", static="static", data="data"),
        data_files=data_files,
    )
    _write_json_file(layout.next_stage_root / "manifest.json", manifest)
    return manifest


def _finalize_staged_pages(
    *,
    layout: WorkRootLayout,
    page_contributions: tuple[StagedPageContributionWire, ...],
    component_front_matter_by_slug: Mapping[str, PipelineComponentFrontMatter],
) -> None:
    translation_links = _translations_by_page(page_contributions)
    for contribution in page_contributions:
        staged_page_path = _normalized_stage_relative_path(layout, contribution.stage_relative_path)
        finalize_staged_page(
            staged_page_path=staged_page_path,
            page=build_page_front_matter(
                contribution=contribution,
                translations=translation_links.get(_page_identity(contribution)),
            ),
            component=component_front_matter_by_slug.get(contribution.component_slug),
        )


def _translations_by_page(
    page_contributions: tuple[StagedPageContributionWire, ...],
) -> dict[tuple[str, str | None, str], list[TranslationLinkSummary]]:
    grouped: dict[tuple[str, str | None, str], list[StagedPageContributionWire]] = defaultdict(list)
    for contribution in page_contributions:
        if contribution.translation_key is None or contribution.locale is None or contribution.public_url is None:
            continue
        grouped[(contribution.component_slug, contribution.artifact_key, contribution.translation_key)].append(contribution)

    links_by_page: dict[tuple[str, str | None, str], list[TranslationLinkSummary]] = {}
    for group in grouped.values():
        links = [build_translation_link(contribution) for contribution in sorted(group, key=lambda item: item.locale or "")]
        for contribution in group:
            links_by_page[_page_identity(contribution)] = [link for link in links if link.locale != contribution.locale]
    return links_by_page


def _write_aggregate_files(
    *,
    layout: WorkRootLayout,
    build_plan: EffectiveBuildPlan,
    diagnostics: tuple[PipelineDiagnosticEntry, ...],
    provider_snapshot: ProviderSnapshotV1,
    page_contributions: tuple[StagedPageContributionWire, ...],
) -> StageDataFiles:
    data_root = layout.data_root
    components_path = _write_items_file(data_root / "components.json", _build_components_entries(build_plan))
    artifacts_path = _write_items_file(data_root / "artifacts.json", _build_artifacts_entries(build_plan))
    routes_path = _write_items_file(data_root / "routes.json", _build_route_entries(build_plan))
    redirects_path = _write_items_file(data_root / "redirects.json", _build_redirect_entries(build_plan))
    providers_path = (
        _write_items_file(data_root / "providers.json", _build_provider_entries(provider_snapshot))
        if provider_snapshot.providers
        else None
    )

    releases = _build_release_entries(build_plan)
    candidates = _build_candidate_entries(build_plan)
    refs = _build_ref_entries(build_plan)
    translations = _build_translation_entries(page_contributions)
    compatibility = _build_compatibility_entries(build_plan)
    mounts = _build_mount_entries(build_plan)
    content_index = _build_content_index_entries(build_plan, page_contributions)

    releases_path = _write_items_file(data_root / "releases.json", releases) if releases else None
    candidates_path = _write_items_file(data_root / "candidates.json", candidates) if candidates else None
    refs_path = _write_items_file(data_root / "refs.json", refs) if refs else None
    translations_path = _write_items_file(data_root / "translations.json", translations) if translations else None
    compatibility_path = _write_items_file(data_root / "compatibility.json", compatibility) if compatibility else None
    mounts_path = _write_items_file(data_root / "mounts.json", mounts) if mounts else None
    content_index_path = _write_items_file(data_root / "content-index.json", content_index) if content_index else None

    public_diagnostics = sanitize_public_diagnostics(
        diagnostics,
        workspace_root=build_plan.workspace_root,
        private_roots=(layout.work_root, layout.fragments_root, layout.units_root, layout.next_stage_root),
    )

    diagnostics_path = None
    if public_diagnostics:
        diagnostics_path = data_root / "diagnostics.json"
        _write_json_file(diagnostics_path, list(public_diagnostics))

    return StageDataFiles(
        components=components_path,
        artifacts=artifacts_path,
        routes=routes_path,
        redirects=redirects_path,
        providers=providers_path,
        releases=releases_path,
        candidates=candidates_path,
        refs=refs_path,
        translations=translations_path,
        compatibility=compatibility_path,
        mounts=mounts_path,
        content_index=content_index_path,
        diagnostics=str(diagnostics_path.relative_to(layout.next_stage_root)) if diagnostics_path is not None else None,
    )


def _build_components_entries(build_plan: EffectiveBuildPlan) -> list[ComponentsDataEntry]:
    provider_keys_by_component: dict[str, set[str]] = defaultdict(set)
    for context in build_plan.selected_versions:
        if context.provider_record is not None:
            provider_keys_by_component[context.component_slug].add(context.provider_record.provider)
    entries = []
    for component in build_plan.site.components:
        entries.append(
            ComponentsDataEntry(
                slug=component.slug,
                display_name=component.authored.display_name,
                group=component.authored.group,
                origin_key=component.publication.origin.key,
                publication=build_component_front_matter(component, build_plan.selected_versions).publication,
                provider_keys=sorted(provider_keys_by_component.get(component.slug) or ()) or None,
                artifacts=build_component_front_matter(component, build_plan.selected_versions).artifacts,
            ),
        )
    return entries


def _build_artifacts_entries(build_plan: EffectiveBuildPlan) -> list[ArtifactsDataEntry]:
    selected_by_artifact: dict[tuple[str, str], list[SelectedVersionContext]] = defaultdict(list)
    for context in build_plan.selected_versions:
        selected_by_artifact[(context.component_slug, context.artifact_key)].append(context)

    entries: list[ArtifactsDataEntry] = []
    for component in build_plan.site.components:
        component_contexts = [context for context in build_plan.selected_versions if context.component_slug == component.slug]
        artifact_front_matter_by_key = {
            item.key: item for item in (build_component_front_matter(component, tuple(component_contexts)).artifacts or ())
        }
        for artifact in component.artifacts:
            contexts = selected_by_artifact.get((component.slug, artifact.key), [])
            released_contexts = [context for context in contexts if context.kind is RecordKind.RELEASED]
            candidate_contexts = [context for context in contexts if context.kind is RecordKind.CANDIDATE]
            named_refs = [context for context in contexts if context.kind in {RecordKind.NAMED_REF, RecordKind.LINE_HEAD, RecordKind.DEVELOPMENT}]
            latest_release = _latest_release_summary(released_contexts)
            latest_candidate = _latest_candidate_summary(candidate_contexts)
            artifact_front_matter = artifact_front_matter_by_key.get(artifact.key)
            entries.append(
                ArtifactsDataEntry(
                    component_slug=component.slug,
                    key=artifact.key,
                    display_name=_artifact_display_name(artifact),
                    source_key=artifact.source_binding.key,
                    docs_root=_artifact_docs_root(artifact, build_plan.workspace_root),
                    provider_keys=sorted({context.provider_record.provider for context in contexts if context.provider_record is not None}) or None,
                    versioning=artifact.versioning,
                    latest_stable=artifact.lifecycle.latest_stable if artifact.lifecycle is not None else None,
                    latest_release=latest_release,
                    latest_candidate=latest_candidate,
                    release_lines=artifact_front_matter.release_lines if artifact_front_matter is not None else None,
                    named_refs=[_ref_entry(component, context) for context in named_refs] or None,
                    support_status_vocabulary=artifact.lifecycle.support_status_vocabulary if artifact.lifecycle is not None else None,
                    support_policy_url=artifact.lifecycle.support_policy_url if artifact.lifecycle is not None else None,
                ),
            )
    return entries


def _build_route_entries(build_plan: EffectiveBuildPlan) -> list[RouteAggregateEntry]:
    component_by_slug = {component.slug: component for component in build_plan.site.components}
    entries: list[RouteAggregateEntry] = []
    for component in build_plan.site.components:
        publication = component.publication
        entries.extend(
            [
                _route_entry(component.slug, publication.origin.key, publication.origin.base_url, publication.component_path, section="component", target_id=f"component:{component.slug}", canonical=publication.component_path == publication.canonical_path),
                _route_entry(component.slug, publication.origin.key, publication.origin.base_url, publication.development_path, section="development", target_id=f"development:{component.slug}"),
                _route_entry(component.slug, publication.origin.key, publication.origin.base_url, publication.docs_path, section="docs", target_id=f"docs:{component.slug}"),
                _route_entry(component.slug, publication.origin.key, publication.origin.base_url, publication.assets_path, section="assets", target_id=f"assets:{component.slug}"),
            ],
        )
        for alias in publication.aliases:
            entries.append(
                _route_entry(
                    component.slug,
                    alias.origin or publication.origin.key,
                    publication.origin.base_url,
                    alias.path,
                    target_id=f"route-alias:{component.slug}:{alias.path}",
                    canonical=False,
                    label=alias.label,
                ),
            )
    for context in build_plan.selected_versions:
        publication = component_by_slug[context.component_slug].publication
        entries.append(
            _route_entry(
                context.component_slug,
                publication.origin.key,
                publication.origin.base_url,
                public_path_for_context(publication=publication, context=context),
                artifact_key=context.artifact_key,
                section=context.kind.value,
                target_id=target_id_for_context(context),
            ),
        )
    return entries


def _build_redirect_entries(build_plan: EffectiveBuildPlan) -> list[RedirectAggregateEntry]:
    entries: list[RedirectAggregateEntry] = []
    for component in build_plan.site.components:
        origin = component.publication.origin
        for redirect in component.publication.redirects:
            to_url = redirect.target if str(redirect.target).startswith("http") else f"{origin.base_url.rstrip('/')}{redirect.target}"
            entries.append(
                RedirectAggregateEntry(
                    from_url=f"{origin.base_url.rstrip('/')}{redirect.from_path}",
                    to_url=to_url,
                    status=redirect.status or 302,
                    reason=redirect.reason,
                    source_kind="catalog",
                ),
            )
    return entries


def _build_provider_entries(provider_snapshot: ProviderSnapshotV1) -> list[ProvidersDataEntry]:
    return [
        ProvidersDataEntry(
            key=provider.key,
            type=str(provider.type),
            display_name=provider.display_name,
            base_url=provider.base_url,
            fetched_at=provider.fetched_at,
        )
        for provider in provider_snapshot.providers
    ]


def _build_release_entries(build_plan: EffectiveBuildPlan) -> list[ReleaseAggregateEntry]:
    component_by_slug = {component.slug: component for component in build_plan.site.components}
    entries = []
    for context in build_plan.selected_versions:
        if context.kind is not RecordKind.RELEASED:
            continue
        provider_record = _provider_record_for_context(context)
        artifact = _artifact_for_context(component_by_slug[context.component_slug], context)
        entries.append(
            ReleaseAggregateEntry(
                provider=provider_record.provider,
                external_id=provider_record.external_id,
                external_url=provider_record.external_url,
                component_slug=context.component_slug,
                artifact_key=context.artifact_key,
                version=_required_context_version(context),
                display_version=provider_record.display_version,
                release_line=provider_record.release_line,
                tag=provider_record.tag,
                publication_state=provider_record.publication_state,
                published_at=_parse_timestamp(provider_record.published_at),
                support_status=_support_status_for_context(artifact, context),
                support_window=_support_window_for_context(artifact, context),
                release_line_ancestors=list(provider_record.release_line_ancestors or ()),
                withdrawal_behavior=context.withdrawal_behavior,
                redirect_target=context.redirect_target,
                maturity=provider_record.maturity,
                assets=list(provider_record.assets) if provider_record.assets is not None else None,
                urls=provider_record.urls,
            ),
        )
    return entries


def _build_candidate_entries(build_plan: EffectiveBuildPlan) -> list[CandidateAggregateEntry]:
    entries = []
    for context in build_plan.selected_versions:
        if context.kind is not RecordKind.CANDIDATE:
            continue
        provider_record = _provider_record_for_context(context)
        entries.append(
            CandidateAggregateEntry(
                provider=provider_record.provider,
                external_id=provider_record.external_id,
                external_url=provider_record.external_url,
                component_slug=context.component_slug,
                artifact_key=context.artifact_key,
                version=_required_context_version(context),
                display_version=provider_record.display_version,
                candidate_sequence=provider_record.candidate_sequence,
                vote_status=provider_record.vote_status,
                release_line=provider_record.release_line,
                maturity=provider_record.maturity,
                created_at=_parse_timestamp(provider_record.created_at),
                published_at=_parse_timestamp(provider_record.published_at),
                assets=list(provider_record.assets) if provider_record.assets is not None else None,
            ),
        )
    return entries


def _build_ref_entries(build_plan: EffectiveBuildPlan) -> list[RefAggregateEntry]:
    component_by_slug = {component.slug: component for component in build_plan.site.components}
    entries = []
    for context in build_plan.selected_versions:
        if context.kind not in {RecordKind.NAMED_REF, RecordKind.LINE_HEAD, RecordKind.DEVELOPMENT}:
            continue
        entries.append(_ref_entry(component_by_slug[context.component_slug], context))
    return entries


def _ref_entry(component: ResolvedComponentConfig, context: SelectedVersionContext) -> RefAggregateEntry:
    provider_record = _provider_record_for_context(context)
    return RefAggregateEntry(
        provider=provider_record.provider,
        external_id=provider_record.external_id,
        external_url=provider_record.external_url,
        component_slug=context.component_slug,
        artifact_key=context.artifact_key,
        ref=_required_context_ref(context),
        named_ref_key=context.named_ref_key,
        kind=context.kind,
        display_version=context.display_version,
        release_line=context.release_line,
        maturity=context.maturity,
    )


def _build_translation_entries(page_contributions: tuple[StagedPageContributionWire, ...]) -> list[TranslationSetAggregateEntry]:
    groups: dict[tuple[str, str | None, str], list[StagedPageContributionWire]] = defaultdict(list)
    for contribution in page_contributions:
        if contribution.translation_key is None or contribution.locale is None or contribution.public_url is None:
            continue
        groups[(contribution.component_slug, contribution.artifact_key, contribution.translation_key)].append(contribution)
    entries = []
    for (component_slug, artifact_key, translation_key), group in sorted(groups.items()):
        ordered_group = sorted(group, key=lambda item: item.locale or "")
        entries.append(
            TranslationSetAggregateEntry(
                component_slug=component_slug,
                artifact_key=artifact_key,
                translation_key=translation_key,
                entries=[build_translation_link(item) for item in ordered_group],
            ),
        )
    return entries


def _build_compatibility_entries(build_plan: EffectiveBuildPlan) -> list[CompatibilityAggregateEntry]:
    entries = []
    for component in build_plan.site.components:
        for assertion in component.authored.compatibility or ():
            entries.append(_compatibility_entry(component.slug, None, assertion))
        for artifact in component.artifacts:
            for assertion in _artifact_compatibility_entries(artifact):
                entries.append(_compatibility_entry(component.slug, artifact.key, assertion))
    return entries


def _build_mount_entries(build_plan: EffectiveBuildPlan) -> list[MountAggregateEntry]:
    entries = []
    for component in build_plan.site.components:
        for mount in component.authored.mounts or ():
            entries.append(_mount_entry(component.slug, None, mount))
        for artifact in component.artifacts:
            for mount in _artifact_mount_entries(artifact):
                entries.append(_mount_entry(component.slug, artifact.key, mount))
    return entries


def _build_content_index_entries(
    build_plan: EffectiveBuildPlan,
    page_contributions: tuple[StagedPageContributionWire, ...],
) -> list[ContentIndexEntry]:
    workspace_root = build_plan.workspace_root.resolve(strict=False)
    entries = []
    for contribution in page_contributions:
        page_url = contribution.public_url or contribution.canonical_url
        if page_url is None:
            raise StageIntegrityError(f"Content index entry is missing a public URL: {contribution.stage_relative_path}")
        provider_context = _provider_mapping(contribution.version_context)
        entries.append(
            ContentIndexEntry(
                id=f"{contribution.component_slug}:{contribution.artifact_key or 'component'}:{contribution.public_path}",
                component_slug=contribution.component_slug,
                artifact_key=contribution.artifact_key,
                page_kind=contribution.page_kind,
                section=contribution.section,
                title=contribution.title or contribution.link_title or contribution.public_path,
                link_title=contribution.link_title,
                path=contribution.public_path,
                url=page_url,
                canonical_url=contribution.canonical_url,
                source_path=public_source_path(source_path=contribution.source_path, workspace_root=workspace_root),
                origin_key=contribution.origin_key,
                provider=(provider_context.get("key") if provider_context is not None else None),
                external_id=(provider_context.get("externalId") if provider_context is not None else None),
                locale=contribution.locale,
                default_locale=contribution.default_locale if contribution.locale is not None else None,
                translation_key=contribution.translation_key,
                version_kind=RecordKind(contribution.version_kind) if contribution.version_kind is not None else None,
                version_label=contribution.version,
            ),
        )
    return entries


def _compatibility_entry(component_slug: str, artifact_key: str | None, assertion: CompatibilityAssertionConfig) -> CompatibilityAggregateEntry:
    subject_id = assertion.subject_ref if artifact_key is None else f"artifact:{component_slug}:{artifact_key}:{assertion.subject_ref}"
    target_id = assertion.target_ref if artifact_key is None else f"artifact:{component_slug}:{artifact_key}:{assertion.target_ref}"
    return CompatibilityAggregateEntry(
        subject_id=subject_id,
        target_id=target_id,
        relation=assertion.relation,
        scope=assertion.scope,
        confidence=assertion.confidence,
        notes=assertion.notes,
        evidence=None,
    )


def _mount_entry(component_slug: str, artifact_key: str | None, mount: MountConfig) -> MountAggregateEntry:
    owner_id = mount.ownership or (f"artifact:{component_slug}:{artifact_key}" if artifact_key is not None else f"component:{component_slug}")
    return MountAggregateEntry(
        mount_id=f"{owner_id}:{mount.mount_path}",
        owner_id=owner_id,
        kind=mount.kind,
        version_context=mount.version_scope,
        public_path=mount.mount_path,
        source_ref=mount.source,
        trust_class=mount.trust_class,
        index_behavior=mount.index_behavior,
        metadata=mount.metadata,
    )


def _latest_release_summary(contexts: list[SelectedVersionContext]) -> LatestReleaseSummary | None:
    if not contexts:
        return None
    context = max(contexts, key=lambda item: ((_provider_record_for_context(item).published_at or ""), item.version or ""))
    provider_record = _provider_record_for_context(context)
    return LatestReleaseSummary(
        version=_required_context_version(context),
        display_version=provider_record.display_version,
        tag=provider_record.tag,
        publication_state=provider_record.publication_state,
        published_at=_parse_timestamp(provider_record.published_at),
    )


def _latest_candidate_summary(contexts: list[SelectedVersionContext]) -> LatestCandidateSummary | None:
    if not contexts:
        return None
    context = max(contexts, key=lambda item: (_provider_record_for_context(item).candidate_sequence or 0, item.version or ""))
    provider_record = _provider_record_for_context(context)
    return LatestCandidateSummary(
        version=_required_context_version(context),
        display_version=provider_record.display_version,
        candidate_sequence=provider_record.candidate_sequence,
        vote_status=provider_record.vote_status,
    )


def _artifact_for_context(component: ResolvedComponentConfig, context: SelectedVersionContext) -> ResolvedArtifactConfig:
    for artifact in component.artifacts:
        if artifact.key == context.artifact_key:
            return artifact
    raise ValueError(f"Artifact {context.artifact_key} not found for component {component.slug}")


def _support_status_for_context(artifact: ResolvedArtifactConfig, context: SelectedVersionContext) -> str | None:
    provider_record = context.provider_record
    if artifact.lifecycle is None:
        return None
    for release in artifact.lifecycle.releases or ():
        if release.version == context.version and release.support_status is not None:
            return release.support_status
    for release_line in artifact.lifecycle.release_lines or ():
        if provider_record is not None and release_line.key == provider_record.release_line and release_line.support_status is not None:
            return release_line.support_status
    return None


def _support_window_for_context(artifact: ResolvedArtifactConfig, context: SelectedVersionContext):
    provider_record = context.provider_record
    if artifact.lifecycle is None:
        return None
    for release in artifact.lifecycle.releases or ():
        if release.version == context.version and release.support_window is not None:
            return release.support_window
    for release_line in artifact.lifecycle.release_lines or ():
        if provider_record is not None and release_line.key == provider_record.release_line and release_line.support_window is not None:
            return release_line.support_window
    return None


def _artifact_display_name(artifact: ResolvedArtifactConfig) -> str | None:
    display_name = getattr(artifact.authored, "display_name", None)
    return display_name if isinstance(display_name, str) else None


def _artifact_docs_root(artifact: ResolvedArtifactConfig, workspace_root: Path) -> str:
    docs_root = getattr(artifact.authored, "docs_root", None)
    if isinstance(docs_root, Path):
        return docs_root.as_posix()
    if isinstance(docs_root, str):
        return docs_root
    if artifact.docs_root.is_relative_to(workspace_root):
        return artifact.docs_root.relative_to(workspace_root).as_posix()
    raise StageIntegrityError(f"Artifact docs root must remain repo-relative: {artifact.key}")


def _artifact_compatibility_entries(artifact: ResolvedArtifactConfig) -> tuple[CompatibilityAssertionConfig, ...]:
    compatibility = getattr(artifact.authored, "compatibility", None)
    return tuple(item for item in compatibility or () if isinstance(item, CompatibilityAssertionConfig))


def _artifact_mount_entries(artifact: ResolvedArtifactConfig) -> tuple[MountConfig, ...]:
    mounts = getattr(artifact.authored, "mounts", None)
    return tuple(item for item in mounts or () if isinstance(item, MountConfig))


def _provider_record_for_context(context: SelectedVersionContext) -> IndexedProviderRecord:
    if context.provider_record is None:
        raise StageIntegrityError(f"Selected version context is missing provider metadata: {context.component_slug}:{context.artifact_key}")
    return context.provider_record


def _required_context_version(context: SelectedVersionContext) -> str:
    if context.version is None:
        raise StageIntegrityError(f"Selected version context is missing version: {context.component_slug}:{context.artifact_key}")
    return context.version


def _required_context_ref(context: SelectedVersionContext) -> str:
    if context.ref is None:
        raise StageIntegrityError(f"Selected version context is missing ref: {context.component_slug}:{context.artifact_key}")
    return context.ref


def _provider_mapping(version_context: dict[str, object] | None) -> dict[str, str] | None:
    if version_context is None:
        return None
    provider = version_context.get("provider")
    if not isinstance(provider, dict):
        return None
    normalized: dict[str, str] = {}
    for key, value in provider.items():
        if isinstance(key, str) and isinstance(value, str):
            normalized[key] = value
    return normalized or None


def _parse_timestamp(value: datetime | str | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _load_page_contributions(layout: WorkRootLayout, worker_results: tuple[WorkerResultWire, ...]) -> tuple[StagedPageContributionWire, ...]:
    contributions: list[StagedPageContributionWire] = []
    for result in worker_results:
        manifest_path = _validated_unit_manifest_path(layout=layout, result=result)
        if manifest_path is None:
            continue
        manifest = read_unit_manifest(manifest_path)
        for page in manifest.pages:
            contribution = page
            if Path(contribution.stage_relative_path).is_absolute():
                contribution = contribution.model_copy(
                    update={
                        "stage_relative_path": str(Path(contribution.stage_relative_path).relative_to(layout.next_stage_root)),
                    },
                )
            contributions.append(contribution)
    return tuple(contributions)


def _validated_unit_manifest_path(layout: WorkRootLayout, result: WorkerResultWire) -> Path | None:
    manifest_path_value = result.contribution_files.unit_manifest
    if manifest_path_value is None:
        return None

    raw_manifest_path = Path(manifest_path_value)
    if raw_manifest_path.is_symlink():
        raise StageIntegrityError(f"Worker contribution manifest must be one normal file: {raw_manifest_path}")

    fragments_root = layout.fragments_root.resolve(strict=False)
    expected_path = (layout.fragments_root / f"{result.unit_id.replace(':', '_')}.json").resolve(strict=False)
    manifest_path = raw_manifest_path.resolve(strict=False)
    if manifest_path != expected_path:
        raise StageIntegrityError(
            "Worker contribution manifest path does not match the coordinator-owned location: "
            f"{manifest_path}",
        )
    if not manifest_path.is_relative_to(fragments_root):
        raise StageIntegrityError(f"Worker contribution manifest escapes the private fragment root: {manifest_path}")
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise StageIntegrityError(f"Worker contribution manifest must be one normal file: {manifest_path}")
    return manifest_path


def _page_identity(contribution: StagedPageContributionWire) -> tuple[str, str | None, str]:
    return (contribution.component_slug, contribution.artifact_key, contribution.stage_relative_path)


def _normalized_stage_relative_path(layout: WorkRootLayout, stage_relative_path: str) -> Path:
    return layout.next_stage_root / stage_relative_path


def _route_entry(
    component_slug: str,
    origin_key: str,
    base_url: str,
    path_value: str,
    *,
    artifact_key: str | None = None,
    section: str | None = None,
    target_id: str | None = None,
    canonical: bool | None = None,
    label: str | None = None,
) -> RouteAggregateEntry:
    return RouteAggregateEntry(
        origin_key=origin_key,
        base_url=base_url,
        path=path_value,
        url=f"{base_url.rstrip('/')}{path_value}",
        component_slug=component_slug,
        artifact_key=artifact_key,
        section=section,
        canonical=canonical,
        route_kind=section,
        target_id=target_id,
        label=label,
    )


def _write_items_file(path: Path, items: list[Any]) -> str:
    _write_json_file(path, {"items": items})
    return str(Path("data") / path.name)


def _write_json_file(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(value, "model_dump_json"):
        serialized = value.model_dump_json(indent=2, exclude_none=True, by_alias=True)
    elif isinstance(value, dict) and "items" in value:
        serialized = "{\n  \"items\": [\n"
        serialized += ",\n".join(_serialize_item(item, indent="    ") for item in value["items"])
        serialized += "\n  ]\n}"
    else:
        serialized = "[\n" + ",\n".join(_serialize_item(item, indent="") for item in value) + "\n]"
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_file.write(serialized + "\n")
            temp_file.flush()
            os.fsync(temp_file.fileno())
            temp_path = Path(temp_file.name)
        os.replace(temp_path, path)
    except OSError as exc:
        raise StageIntegrityError(f"Could not write stage JSON file {path}: {exc}") from exc
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink(missing_ok=True)


def _serialize_item(item: Any, *, indent: str) -> str:
    if hasattr(item, "model_dump_json"):
        try:
            text = item.model_dump_json(indent=2, exclude_none=True, by_alias=True)
        except TypeError:
            text = item.model_dump_json(indent=2, exclude_none=True)
    elif hasattr(item, "model_dump"):
        import json

        text = json.dumps(item.model_dump(mode="json", exclude_none=True, by_alias=True), indent=2, ensure_ascii=False)
    else:
        import json

        text = json.dumps(item, indent=2, ensure_ascii=False)
    return "\n".join(f"{indent}{line}" for line in text.splitlines())