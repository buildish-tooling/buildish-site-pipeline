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

"""Normalized external provider snapshot documents."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import model_validator

from .base import SitePipelineBaseModel
from .enums import PublicationState, RecordKind
from .scalars import (
    ArtifactKey,
    Identifier,
    NonEmptyString,
    NonNegativeInteger,
    ProviderBaseUrl,
    ProviderKey,
    RefString,
    Slug,
    SourceKey,
    TimestampString,
    UrlString,
    VersionString,
)


class ProviderDescriptor(SitePipelineBaseModel):
    """Descriptor for one loaded provider."""

    key: ProviderKey
    type: NonEmptyString
    display_name: NonEmptyString | None = None
    base_url: ProviderBaseUrl | None = None
    fetched_at: TimestampString


class ProviderAsset(SitePipelineBaseModel):
    """Optional file-level metadata attached to a provider record."""

    name: NonEmptyString
    url: UrlString
    kind: NonEmptyString | None = None
    media_type: NonEmptyString | None = None
    size: NonNegativeInteger | None = None
    checksums: dict[Identifier, NonEmptyString] | None = None
    signature_url: UrlString | None = None
    sbom_url: UrlString | None = None
    provenance_url: UrlString | None = None


class ProviderRecord(SitePipelineBaseModel):
    """Normalized release, candidate, or ref record from a provider."""

    provider: ProviderKey
    kind: RecordKind
    component_slug: Slug
    artifact_key: ArtifactKey
    source_key: SourceKey | None = None
    external_id: NonEmptyString | None = None
    external_url: UrlString | None = None
    version: VersionString | None = None
    display_version: NonEmptyString | None = None
    tag: NonEmptyString | None = None
    ref: RefString | None = None
    commit_sha: NonEmptyString | None = None
    named_ref_key: NonEmptyString | None = None
    release_line: NonEmptyString | None = None
    release_line_ancestors: list[NonEmptyString] | None = None
    support_status: NonEmptyString | None = None
    publication_state: PublicationState | None = None
    maturity: NonEmptyString | None = None
    candidate_sequence: NonNegativeInteger | None = None
    vote_status: NonEmptyString | None = None
    created_at: TimestampString | None = None
    published_at: TimestampString | None = None
    updated_at: TimestampString | None = None
    urls: dict[NonEmptyString, UrlString] | None = None
    assets: list[ProviderAsset] | None = None

    @model_validator(mode="after")
    def ensure_stable_locator_exists(self) -> Self:
        if all(
            locator is None
            for locator in (self.external_id, self.version, self.tag, self.ref)
        ):
            raise ValueError(
                "Provider records must include at least one of externalId, version, tag, or ref",
            )
        return self


class ProviderSnapshotV1(SitePipelineBaseModel):
    """Normalized external release-provider input."""

    schema_version: Literal[1]
    providers: list[ProviderDescriptor]
    records: list[ProviderRecord]

    @model_validator(mode="after")
    def ensure_provider_cross_references_and_uniqueness(self) -> Self:
        provider_keys: set[str] = set()
        for provider in self.providers:
            if provider.key in provider_keys:
                raise ValueError(f"Duplicate provider key {provider.key!r}")
            provider_keys.add(provider.key)

        seen_provider_external_ids: set[tuple[str, str]] = set()
        for record in self.records:
            if record.provider not in provider_keys:
                raise ValueError(
                    f"Unknown provider key {record.provider!r} in records[]"
                )
            if record.external_id is None:
                continue

            identity = (record.provider, record.external_id)
            if identity in seen_provider_external_ids:
                raise ValueError(
                    "Duplicate provider record for the same (provider, externalId) pair",
                )
            seen_provider_external_ids.add(identity)

        return self
