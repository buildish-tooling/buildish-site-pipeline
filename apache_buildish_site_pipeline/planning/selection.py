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

"""Deterministic version-context selection for planning."""

from __future__ import annotations

import re

from apache_buildish_site_pipeline.models.catalog import PublicationSelectionPolicy
from apache_buildish_site_pipeline.models.enums import (
    CandidateSelectionMode,
    LineHeadSelectionMode,
    RecordKind,
    ReleaseSelectionMode,
)

from .types import ProviderContextIndex, ProviderSnapshotIndex, ResolvedSiteConfig, SelectedVersionContext, SelectedVersionSet

_MAX_SELECTED_CONTEXTS = 512
_SEMVER_PATTERN = re.compile(r"^[0-9]+(?:\.[0-9]+)*(?:[-+][A-Za-z0-9.-]+)?$")


def select_version_contexts(*, site: ResolvedSiteConfig, provider_index: ProviderSnapshotIndex) -> SelectedVersionSet:
    """Select the effective version contexts across all resolved artifacts."""

    selected_contexts: list[SelectedVersionContext] = []
    deterministic = True
    for component in site.components:
        for artifact in component.artifacts:
            effective_policy = artifact.publication_selection or component.publication_selection or _default_publication_selection_policy()
            provider_context = provider_index.contexts_by_artifact.get((component.slug, artifact.key))
            selected_contexts.extend(_select_development_context(component.slug, artifact, provider_context, effective_policy))
            line_head_contexts = _select_line_head_contexts(component.slug, artifact, provider_context, effective_policy)
            selected_contexts.extend(line_head_contexts)
            selected_contexts.extend(_select_release_contexts(component.slug, artifact, provider_context, effective_policy))
            selected_contexts.extend(_select_named_ref_contexts(component.slug, artifact, provider_context, effective_policy))
            candidate_contexts = _select_candidate_contexts(component.slug, artifact, provider_context, effective_policy)
            selected_contexts.extend(candidate_contexts)
            deterministic = deterministic and all(context.deterministic for context in line_head_contexts + candidate_contexts)

    if len(selected_contexts) > _MAX_SELECTED_CONTEXTS:
        raise ValueError("Planning selected more than the 512 version-context ceiling")
    ordered_contexts = tuple(sorted(selected_contexts, key=_context_sort_key))
    return SelectedVersionSet(contexts=ordered_contexts, deterministic=deterministic and all(context.deterministic for context in ordered_contexts))


def _default_publication_selection_policy() -> PublicationSelectionPolicy:
    return PublicationSelectionPolicy(
        development=True,
        line_heads={"mode": "allAuthored"},
        releases={"mode": "latestPerLine"},
        named_refs=[],
        candidates={"mode": "none"},
    )


def _select_development_context(component_slug: str, artifact: object, provider_context: ProviderContextIndex | None, policy: PublicationSelectionPolicy) -> list[SelectedVersionContext]:
    if not policy.development:
        return []
    provider_record = None
    deterministic = True
    if provider_context is not None:
        matching_records = [
            record
            for record in provider_context.development_records
            if record.ref == artifact.versioning.development_ref
        ]
        if matching_records:
            provider_record = _choose_best_record(matching_records)
            deterministic = len(matching_records) == 1
    return [
        SelectedVersionContext(
            component_slug=component_slug,
            artifact_key=artifact.key,
            kind=RecordKind.DEVELOPMENT,
            source_binding=artifact.source_binding,
            docs_root=artifact.docs_root,
            assets_root=artifact.assets_root,
            display_version=provider_record.display_version if provider_record else None,
            ref=artifact.versioning.development_ref,
            commit_sha=provider_record.commit_sha if provider_record else None,
            provider_record=provider_record,
            deterministic=deterministic,
        )
    ]


def _select_line_head_contexts(component_slug: str, artifact: object, provider_context: ProviderContextIndex | None, policy: PublicationSelectionPolicy) -> list[SelectedVersionContext]:
    line_head_policy = policy.line_heads
    if line_head_policy is None or line_head_policy.mode is LineHeadSelectionMode.NONE:
        return []

    authored_release_lines = {line.key: line for line in artifact.lifecycle.release_lines or ()} if artifact.lifecycle else {}
    if line_head_policy.mode is LineHeadSelectionMode.EXPLICIT:
        selected_line_keys = tuple(line_head_policy.keys or ())
    else:
        selected_line_keys = tuple(authored_release_lines)

    selected_contexts = []
    for line_key in selected_line_keys:
        authored_line = authored_release_lines[line_key]
        provider_record = None
        deterministic = True
        if provider_context is not None:
            provider_records = list(provider_context.line_heads_by_release_line.get(line_key, ()))
            if provider_records:
                provider_record = _choose_best_record(provider_records)
                deterministic = len(provider_records) == 1
        selected_contexts.append(
            SelectedVersionContext(
                component_slug=component_slug,
                artifact_key=artifact.key,
                kind=RecordKind.LINE_HEAD,
                source_binding=artifact.source_binding,
                docs_root=artifact.docs_root,
                assets_root=artifact.assets_root,
                release_line=line_key,
                ref=authored_line.maintenance_ref or (provider_record.ref if provider_record else None),
                commit_sha=provider_record.commit_sha if provider_record else None,
                support_status=authored_line.support_status or (provider_record.support_status if provider_record else None),
                provider_record=provider_record,
                deterministic=deterministic,
            )
        )
    return selected_contexts


def _select_release_contexts(component_slug: str, artifact: object, provider_context: ProviderContextIndex | None, policy: PublicationSelectionPolicy) -> list[SelectedVersionContext]:
    release_policy = policy.releases
    if release_policy is None:
        return []

    authored_releases = {release.version: release for release in artifact.lifecycle.releases or ()} if artifact.lifecycle else {}
    known_versions = set(authored_releases)
    if provider_context is not None:
        known_versions.update(provider_context.released_by_version)

    if release_policy.mode is ReleaseSelectionMode.EXPLICIT:
        selected_versions = tuple(release_policy.versions or ())
    elif release_policy.mode is ReleaseSelectionMode.ALL_KNOWN:
        selected_versions = tuple(sorted(known_versions, key=_descending_version_sort_key))
    elif release_policy.mode is ReleaseSelectionMode.LATEST_N:
        sorted_versions = sorted(known_versions, key=_descending_version_sort_key)
        selected_versions = tuple(sorted_versions[: release_policy.count or 0])
    else:
        selected_versions = tuple(line.latest for line in artifact.lifecycle.release_lines or () if line.latest is not None) if artifact.lifecycle else ()

    selected_contexts = []
    for version in selected_versions:
        provider_records = list(provider_context.released_by_version.get(version, ())) if provider_context is not None else []
        provider_record = _choose_best_record(provider_records) if provider_records else None
        authored_release = authored_releases.get(version)
        selected_contexts.append(
            SelectedVersionContext(
                component_slug=component_slug,
                artifact_key=artifact.key,
                kind=RecordKind.RELEASED,
                source_binding=artifact.source_binding,
                docs_root=artifact.docs_root,
                assets_root=artifact.assets_root,
                version=version,
                display_version=provider_record.display_version if provider_record else version,
                tag=(provider_record.tag if provider_record else None) or (authored_release.tag if authored_release else None),
                publication_state=provider_record.publication_state if provider_record else (authored_release.publication_state if authored_release else None),
                withdrawal_behavior=authored_release.withdrawal_behavior if authored_release else None,
                redirect_target=authored_release.redirect_target if authored_release else None,
                provider_record=provider_record,
                deterministic=len(provider_records) <= 1,
            )
        )
    return selected_contexts


def _select_named_ref_contexts(component_slug: str, artifact: object, provider_context: ProviderContextIndex | None, policy: PublicationSelectionPolicy) -> list[SelectedVersionContext]:
    selected_keys = tuple(policy.named_refs or ())
    authored_named_refs = {named_ref.key: named_ref for named_ref in artifact.versioning.named_refs or ()}
    selected_contexts = []
    for named_ref_key in selected_keys:
        authored_named_ref = authored_named_refs[named_ref_key]
        provider_record = None
        deterministic = True
        if provider_context is not None:
            provider_records = list(provider_context.named_refs_by_key.get(named_ref_key, ())) or list(provider_context.refs_by_ref.get(authored_named_ref.ref, ()))
            if provider_records:
                provider_record = _choose_best_record(provider_records)
                deterministic = len(provider_records) == 1
        selected_contexts.append(
            SelectedVersionContext(
                component_slug=component_slug,
                artifact_key=artifact.key,
                kind=RecordKind.NAMED_REF,
                source_binding=artifact.source_binding,
                docs_root=artifact.docs_root,
                assets_root=artifact.assets_root,
                display_version=provider_record.display_version if provider_record else authored_named_ref.display_name,
                ref=authored_named_ref.ref,
                commit_sha=provider_record.commit_sha if provider_record else None,
                named_ref_key=named_ref_key,
                maturity=authored_named_ref.maturity,
                provider_record=provider_record,
                deterministic=deterministic,
            )
        )
    return selected_contexts


def _select_candidate_contexts(component_slug: str, artifact: object, provider_context: ProviderContextIndex | None, policy: PublicationSelectionPolicy) -> list[SelectedVersionContext]:
    candidate_policy = policy.candidates
    if candidate_policy is None or candidate_policy.mode is CandidateSelectionMode.NONE or provider_context is None:
        return []

    if candidate_policy.mode is CandidateSelectionMode.EXPLICIT:
        selected_versions = tuple(candidate_policy.versions or ())
    else:
        selected_versions = tuple(sorted(provider_context.candidates_by_version, key=_descending_version_sort_key)[:1])

    selected_contexts = []
    for version in selected_versions:
        provider_records = list(provider_context.candidates_by_version.get(version, ()))
        if candidate_policy.external_ids:
            provider_records = [
                record for record in provider_records if record.external_id in set(candidate_policy.external_ids)
            ]
        if not provider_records:
            continue
        provider_record = _choose_best_record(provider_records)
        selected_contexts.append(
            SelectedVersionContext(
                component_slug=component_slug,
                artifact_key=artifact.key,
                kind=RecordKind.CANDIDATE,
                source_binding=artifact.source_binding,
                docs_root=artifact.docs_root,
                assets_root=artifact.assets_root,
                version=version,
                display_version=provider_record.display_version,
                tag=provider_record.tag,
                commit_sha=provider_record.commit_sha,
                maturity=provider_record.maturity,
                provider_record=provider_record,
                deterministic=len(provider_records) == 1,
            )
        )
    return selected_contexts


def _choose_best_record(records: list[object]) -> object:
    return sorted(records, key=_provider_record_sort_key, reverse=True)[0]


def _provider_record_sort_key(record: object) -> tuple[tuple[object, ...], ...]:
    return (
        (_version_sort_key(record.version) if record.version else ()),
        ((record.candidate_sequence or 0),),
        ((record.updated_at or ""),),
        ((record.published_at or ""),),
        ((record.external_id or ""),),
        ((record.ref or ""),),
    )


def _descending_version_sort_key(version: str) -> tuple[object, ...]:
    return _version_sort_key(version)


def _version_sort_key(version: str) -> tuple[object, ...]:
    if not _SEMVER_PATTERN.fullmatch(version):
        raise ValueError(f"Version {version!r} is not sortable by the conservative planning comparator")
    main_version, _, suffix = version.partition("-")
    number_parts = tuple(int(part) for part in main_version.split("."))
    return number_parts + ((0 if suffix == "" else -1), suffix)


def _context_sort_key(context: SelectedVersionContext) -> tuple[object, ...]:
    return (
        context.component_slug,
        context.artifact_key,
        context.kind.value,
        context.release_line or "",
        context.version or "",
        context.named_ref_key or "",
        context.ref or "",
    )