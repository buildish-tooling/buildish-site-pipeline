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

from typing import ClassVar, Literal, Self

from pydantic import Field, model_validator

from ...docs.documentation import (
    ContractDocumentation,
    ProviderDerivedModel as SitePipelineBaseModel,
)
from ..enums import PublicationState, RecordKind
from ..scalars import (
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
    """Metadata about one provider that contributed records to the snapshot."""

    key: ProviderKey = Field(
        description="Stable provider identifier referenced by every record emitted from this provider.",
        examples=["github-releases"],
    )
    type: NonEmptyString = Field(
        description="Provider implementation type, such as `github`, `git`, or another fetcher-specific backend name.",
        examples=["github"],
    )
    display_name: NonEmptyString | None = Field(
        default=None,
        description="Human-readable provider label shown in diagnostics or rendered metadata.",
        examples=["GitHub Releases"],
    )
    base_url: ProviderBaseUrl | None = Field(
        default=None,
        description="Base URL for the provider service when records can link back to a human-browsable origin.",
        examples=["https://github.com/apache"],
    )
    fetched_at: TimestampString = Field(
        description="Timestamp when this provider snapshot section was fetched or refreshed.",
        examples=["2026-04-03T18:00:00Z"],
    )


class ProviderAsset(SitePipelineBaseModel):
    """Downloadable asset attached to one provider release or candidate record."""

    name: NonEmptyString = Field(
        description="Filename or display label of the downloadable asset.",
        examples=["spark-4.0.0-bin.tgz"],
    )
    url: UrlString = Field(
        description="Canonical download URL for the asset.",
        examples=["https://downloads.example.org/spark-4.0.0-bin.tgz"],
    )
    kind: NonEmptyString | None = Field(
        default=None,
        description="Short asset kind label, for example `binary`, `source`, `signature`, or `sbom`.",
        examples=["binary"],
    )
    media_type: NonEmptyString | None = Field(
        default=None,
        description="Declared media type for the asset payload when the provider exposes it.",
        examples=["application/gzip"],
    )
    size: NonNegativeInteger | None = Field(
        default=None,
        description="Asset size in bytes when the provider exposes it.",
        examples=[125004321],
    )
    checksums: dict[Identifier, NonEmptyString] | None = Field(
        default=None,
        description="Checksum values keyed by algorithm name, such as `sha512` or `sha256`.",
    )
    signature_url: UrlString | None = Field(
        default=None,
        description="URL of the detached signature file, if available.",
    )
    sbom_url: UrlString | None = Field(
        default=None,
        description="URL of the asset's software bill of materials, if available.",
    )
    provenance_url: UrlString | None = Field(
        default=None,
        description="URL of provenance or attestation metadata associated with this asset, if available.",
    )


class ProviderRecord(SitePipelineBaseModel):
    """Normalized provider fact about one release, candidate, or ref context."""

    provider: ProviderKey = Field(
        description="Provider key that identifies which fetched provider emitted this record.",
        examples=["github-releases"],
    )
    kind: RecordKind = Field(
        description="Record kind, such as exact release, release candidate, development ref, line head, or named ref.",
    )
    component_slug: Slug = Field(
        description="Component slug that this provider record belongs to.",
        examples=["spark"],
    )
    artifact_key: ArtifactKey = Field(
        description="Artifact key that this provider record belongs to.",
        examples=["runtime"],
    )
    source_key: SourceKey | None = Field(
        default=None,
        description="Optional source binding key when the provider record came from one named catalog source.",
        examples=["apache-spark"],
    )
    external_id: NonEmptyString | None = Field(
        default=None,
        description="Provider-specific stable identifier used to deduplicate and revisit the same upstream record.",
        examples=["github:release:runtime-4.0.0"],
    )
    external_url: UrlString | None = Field(
        default=None,
        description="Human-browsable upstream URL for the release, tag, or ref record.",
    )
    version: VersionString | None = Field(
        default=None,
        description="Exact version string for release and candidate records when the provider exposes one.",
        examples=["4.0.0"],
    )
    display_version: NonEmptyString | None = Field(
        default=None,
        description="Human-readable version label when the raw version string needs a friendlier presentation.",
        examples=["4.0.0 GA"],
    )
    tag: NonEmptyString | None = Field(
        default=None,
        description="Exact provider tag associated with this record when tags are available.",
        examples=["v4.0.0"],
    )
    ref: RefString | None = Field(
        default=None,
        description="Exact source-control ref associated with this record, especially for development, line-head, or named-ref contexts.",
        examples=["refs/heads/main"],
    )
    commit_sha: NonEmptyString | None = Field(
        default=None,
        description="Resolved commit SHA for the record when the provider exposes it.",
        examples=["6f0fd1f7b2c4a6d8e9f00123456789abcdef0123"],
    )
    named_ref_key: NonEmptyString | None = Field(
        default=None,
        description="Catalog-authored named-ref key that this provider record enriches when the record represents a named ref.",
        examples=["preview"],
    )
    release_line: NonEmptyString | None = Field(
        default=None,
        description="Release-line key that groups this record with related versions such as `4.0`.",
        examples=["4.0"],
    )
    release_line_ancestors: list[NonEmptyString] | None = Field(
        default=None,
        description="Ancestor release-line keys, ordered from nearest to farthest, used when lineage matters to selection or rendering.",
        examples=[["4.x", "stable"]],
    )
    support_status: NonEmptyString | None = Field(
        default=None,
        description="Support-status key or label associated with this record.",
        examples=["supported"],
    )
    publication_state: PublicationState | None = Field(
        default=None,
        description="Publication state for the record, such as published, withdrawn, or tombstoned.",
    )
    maturity: NonEmptyString | None = Field(
        default=None,
        description="Maturity label such as preview, beta, or stable that readers can use to judge readiness.",
        examples=["stable"],
    )
    candidate_sequence: NonNegativeInteger | None = Field(
        default=None,
        description="Numeric ordering hint for release candidates, usually the `rc` sequence number.",
        examples=[1],
    )
    vote_status: NonEmptyString | None = Field(
        default=None,
        description="Vote status label for a candidate release when the provider exposes release-vote state.",
        examples=["passed"],
    )
    created_at: TimestampString | None = Field(
        default=None,
        description="Timestamp when the upstream record was first created.",
    )
    published_at: TimestampString | None = Field(
        default=None,
        description="Timestamp when the upstream record became publicly available.",
    )
    updated_at: TimestampString | None = Field(
        default=None,
        description="Timestamp of the most recent upstream update observed for this record.",
    )
    urls: dict[NonEmptyString, UrlString] | None = Field(
        default=None,
        description="Additional named URLs related to the record, such as notes, signatures, vote threads, or changelogs.",
    )
    assets: list[ProviderAsset] | None = Field(
        default=None,
        description="Downloadable assets attached to the record, including checksums and related provenance links when available.",
    )

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


class ProviderSnapshotDocumentV1(SitePipelineBaseModel):
    """Provider-derived normalized snapshot from ``site/provider-snapshot.json``."""

    contract_documentation: ClassVar[ContractDocumentation] = ContractDocumentation(
        category="provider",
        ownership="provider-derived",
        summary="Normalized provider inventory of releases, candidates, refs, and downloadable assets.",
        file_path="site/provider-snapshot.json",
    )

    schema_version: Literal[1] = Field(
        description="Schema version for the provider snapshot document."
    )
    providers: list[ProviderDescriptor] = Field(
        description="Provider descriptors for every provider that contributed records to this snapshot."
    )
    records: list[ProviderRecord] = Field(
        description="Normalized provider records for releases, candidates, tags, refs, and related downloadable assets."
    )

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
