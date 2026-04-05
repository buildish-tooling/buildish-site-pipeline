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

"""Provider snapshot indexing for deterministic planning."""

from __future__ import annotations

from dataclasses import dataclass, field

from apache_buildish_site_pipeline.models.enums import RecordKind
from apache_buildish_site_pipeline.models.provider_snapshot import ProviderSnapshotV1

from .types import (
    IndexedProviderRecord,
    ProviderContextIndex,
    ProviderSnapshotIndex,
    ResolvedSiteConfig,
)

_MAX_PROVIDER_SNAPSHOT_BYTES = 16 * 1024 * 1024
_MAX_PROVIDER_RECORDS = 50_000


@dataclass(slots=True)
class _MutableProviderContextBucket:
    released_by_version: dict[str, list[IndexedProviderRecord]] = field(
        default_factory=dict
    )
    candidates_by_version: dict[str, list[IndexedProviderRecord]] = field(
        default_factory=dict
    )
    named_refs_by_key: dict[str, list[IndexedProviderRecord]] = field(
        default_factory=dict
    )
    refs_by_ref: dict[str, list[IndexedProviderRecord]] = field(default_factory=dict)
    line_heads_by_release_line: dict[str, list[IndexedProviderRecord]] = field(
        default_factory=dict
    )
    development_records: list[IndexedProviderRecord] = field(default_factory=list)


def build_provider_snapshot_index(
    *,
    provider_snapshot: ProviderSnapshotV1,
    site: ResolvedSiteConfig,
) -> ProviderSnapshotIndex:
    """Index provider records by artifact and selection identity."""

    encoded_size = len(
        provider_snapshot.model_dump_json(by_alias=True, exclude_none=True).encode(
            "utf-8"
        )
    )
    if encoded_size > _MAX_PROVIDER_SNAPSHOT_BYTES:
        raise ValueError("Provider snapshot exceeds the 16 MiB planning ceiling")
    if len(provider_snapshot.records) > _MAX_PROVIDER_RECORDS:
        raise ValueError("Provider snapshot exceeds the 50,000 record planning ceiling")

    known_artifacts = {
        (component.slug, artifact.key)
        for component in site.components
        for artifact in component.artifacts
    }
    contexts_by_artifact: dict[tuple[str, str], _MutableProviderContextBucket] = {}
    by_external_id: dict[tuple[str, str], IndexedProviderRecord] = {}

    for record in provider_snapshot.records:
        artifact_identity = (record.component_slug, record.artifact_key)
        if artifact_identity not in known_artifacts:
            raise ValueError(
                f"Provider record references unknown artifact {record.component_slug}:{record.artifact_key}",
            )

        indexed_record = IndexedProviderRecord(
            provider=record.provider,
            kind=record.kind,
            component_slug=record.component_slug,
            artifact_key=record.artifact_key,
            external_id=record.external_id,
            external_url=str(record.external_url)
            if record.external_url is not None
            else None,
            version=record.version,
            display_version=record.display_version,
            tag=record.tag,
            ref=record.ref,
            commit_sha=record.commit_sha,
            named_ref_key=record.named_ref_key,
            release_line=record.release_line,
            release_line_ancestors=tuple(record.release_line_ancestors or ()),
            support_status=record.support_status,
            publication_state=record.publication_state,
            maturity=record.maturity,
            candidate_sequence=record.candidate_sequence,
            vote_status=record.vote_status,
            created_at=record.created_at,
            published_at=record.published_at,
            updated_at=record.updated_at,
            urls=dict(record.urls or {}),
            assets=tuple(record.assets or ()),
        )
        if indexed_record.external_id is not None:
            by_external_id[(indexed_record.provider, indexed_record.external_id)] = (
                indexed_record
            )

        artifact_bucket = contexts_by_artifact.setdefault(
            artifact_identity, _MutableProviderContextBucket()
        )
        _add_to_context_bucket(artifact_bucket, indexed_record)

    return ProviderSnapshotIndex(
        providers={provider.key: provider for provider in provider_snapshot.providers},
        contexts_by_artifact={
            key: ProviderContextIndex(
                released_by_version={
                    version: tuple(records)
                    for version, records in value.released_by_version.items()
                },
                candidates_by_version={
                    version: tuple(records)
                    for version, records in value.candidates_by_version.items()
                },
                named_refs_by_key={
                    named_ref: tuple(records)
                    for named_ref, records in value.named_refs_by_key.items()
                },
                refs_by_ref={
                    ref: tuple(records) for ref, records in value.refs_by_ref.items()
                },
                line_heads_by_release_line={
                    line: tuple(records)
                    for line, records in value.line_heads_by_release_line.items()
                },
                development_records=tuple(value.development_records),
            )
            for key, value in contexts_by_artifact.items()
        },
        by_external_id=by_external_id,
        snapshot_bytes=encoded_size,
        record_count=len(provider_snapshot.records),
    )


def _add_to_context_bucket(
    artifact_bucket: _MutableProviderContextBucket,
    indexed_record: IndexedProviderRecord,
) -> None:
    if (
        indexed_record.version is not None
        and indexed_record.kind is RecordKind.RELEASED
    ):
        artifact_bucket.released_by_version.setdefault(
            indexed_record.version, []
        ).append(indexed_record)
    if (
        indexed_record.version is not None
        and indexed_record.kind is RecordKind.CANDIDATE
    ):
        artifact_bucket.candidates_by_version.setdefault(
            indexed_record.version, []
        ).append(indexed_record)
    if indexed_record.named_ref_key is not None:
        artifact_bucket.named_refs_by_key.setdefault(
            indexed_record.named_ref_key, []
        ).append(indexed_record)
    if indexed_record.ref is not None:
        artifact_bucket.refs_by_ref.setdefault(indexed_record.ref, []).append(
            indexed_record
        )
    if (
        indexed_record.release_line is not None
        and indexed_record.kind is RecordKind.LINE_HEAD
    ):
        artifact_bucket.line_heads_by_release_line.setdefault(
            indexed_record.release_line, []
        ).append(indexed_record)
    if indexed_record.kind is RecordKind.DEVELOPMENT:
        artifact_bucket.development_records.append(indexed_record)
