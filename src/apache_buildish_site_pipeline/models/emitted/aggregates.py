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

"""Public staged aggregate entry models."""

from __future__ import annotations

from typing import Self

from pydantic import Field, model_validator

from ..documentation import PipelineDerivedModel as SitePipelineBaseModel
from ..enums import (
    IndexBehavior,
    PublicationState,
    RecordKind,
    TrustClass,
    WithdrawalBehavior,
)
from ..scalars import (
    ArtifactKey,
    ExtensionsObject,
    Identifier,
    MountSourceRef,
    NonEmptyString,
    OriginKey,
    ProviderBaseUrl,
    ProviderKey,
    PublicPath,
    ReferenceString,
    RefString,
    RepoRelativePath,
    Slug,
    SourceKey,
    TimestampString,
    UrlString,
    VersionString,
)
from ..validation.extensions import serialize_extensions_object
from ..authored.component_metadata import SupportStatusDefinition
from ..authored.site_catalog import ArtifactVersioningConfig, SupportWindow
from ..provider.provider_snapshot import ProviderAsset
from .staged_front_matter import (
    ArtifactFrontMatterSummary,
    ReleaseLineSummary,
    ResolvedPublication,
    TranslationLinkSummary,
)

_ALLOWED_REDIRECT_STATUS_CODES = frozenset({301, 302, 307, 308})
_WITHDRAWN_PUBLICATION_STATES = frozenset(
    {PublicationState.WITHDRAWN, PublicationState.TOMBSTONED}
)
_ALLOWED_REF_KINDS = frozenset(
    {RecordKind.DEVELOPMENT, RecordKind.NAMED_REF, RecordKind.LINE_HEAD}
)
_MAX_MOUNT_METADATA_BYTES = 16 * 1024


def _ensure_unique_strings(values: list[str], *, type_name: str) -> None:
    seen_values: set[str] = set()
    for value in values:
        if value in seen_values:
            raise ValueError(f"Duplicate {type_name} {value!r}")
        seen_values.add(value)


def _build_expected_url(base_url: str, public_path: str) -> str:
    return f"{base_url.rstrip('/')}{public_path}"


class ProvidersDataEntry(SitePipelineBaseModel):
    """Entry in ``data/providers.json``."""

    key: ProviderKey
    type: NonEmptyString
    display_name: NonEmptyString | None = None
    base_url: ProviderBaseUrl | None = None
    fetched_at: TimestampString


class ComponentsDataEntry(SitePipelineBaseModel):
    """Entry in ``data/components.json``."""

    slug: Slug
    display_name: NonEmptyString | None = None
    weight: int | None = Field(
        default=None,
        strict=True,
        description="Optional ordering hint copied from the authored catalog for consumer-rendered component lists.",
    )
    group: Identifier | None = None
    origin_key: OriginKey
    publication: ResolvedPublication
    provider_keys: list[ProviderKey] | None = None
    artifacts: list[ArtifactFrontMatterSummary] | None = None

    @model_validator(mode="after")
    def ensure_origin_key_and_provider_keys_are_consistent(self) -> Self:
        if self.origin_key != self.publication.origin.key:
            raise ValueError("originKey must match publication.origin.key")
        if self.provider_keys is not None:
            _ensure_unique_strings(self.provider_keys, type_name="provider key")
        return self


class LatestReleaseSummary(SitePipelineBaseModel):
    """Compact latest-release summary embedded in artifact aggregates."""

    version: VersionString
    display_version: NonEmptyString | None = None
    tag: NonEmptyString | None = None
    publication_state: PublicationState | None = None
    published_at: TimestampString | None = None


class LatestCandidateSummary(SitePipelineBaseModel):
    """Compact latest-candidate summary embedded in artifact aggregates."""

    version: VersionString | None = None
    display_version: NonEmptyString | None = None
    candidate_sequence: int | None = Field(default=None, strict=True, ge=1)
    vote_status: NonEmptyString | None = None


class ArtifactsDataEntry(SitePipelineBaseModel):
    """Entry in ``data/artifacts.json``."""

    component_slug: Slug
    key: ArtifactKey
    display_name: NonEmptyString | None = None
    source_key: SourceKey | None = None
    docs_root: RepoRelativePath | None = None
    provider_keys: list[ProviderKey] | None = None
    versioning: ArtifactVersioningConfig | None = None
    latest_stable: VersionString | None = None
    latest_release: LatestReleaseSummary | None = None
    latest_candidate: LatestCandidateSummary | None = None
    release_lines: list[ReleaseLineSummary] | None = None
    named_refs: list[RefAggregateEntry] | None = None
    support_status_vocabulary: dict[NonEmptyString, SupportStatusDefinition] | None = (
        None
    )
    support_policy_url: UrlString | None = None

    @model_validator(mode="after")
    def ensure_provider_keys_are_unique(self) -> Self:
        if self.provider_keys is not None:
            _ensure_unique_strings(self.provider_keys, type_name="provider key")
        return self


class ReleaseAggregateEntry(SitePipelineBaseModel):
    """Entry in ``data/releases.json``."""

    provider: ProviderKey | None = None
    external_id: NonEmptyString | None = None
    external_url: UrlString | None = None
    component_slug: Slug
    artifact_key: ArtifactKey
    version: VersionString
    display_version: NonEmptyString | None = None
    tag: NonEmptyString | None = None
    release_line: NonEmptyString | None = None
    release_line_ancestors: list[NonEmptyString] | None = None
    support_status: NonEmptyString | None = None
    support_window: SupportWindow | None = None
    publication_state: PublicationState | None = None
    withdrawal_behavior: WithdrawalBehavior | None = None
    redirect_target: ReferenceString | UrlString | None = None
    maturity: NonEmptyString | None = None
    published_at: TimestampString | None = None
    assets: list[ProviderAsset] | None = None
    urls: dict[NonEmptyString, UrlString] | None = None

    @model_validator(mode="after")
    def ensure_release_redirect_fields_are_consistent(self) -> Self:
        if self.release_line_ancestors is not None:
            _ensure_unique_strings(
                self.release_line_ancestors, type_name="release-line ancestor"
            )

        if self.withdrawal_behavior is None:
            if self.redirect_target is not None:
                raise ValueError("redirectTarget requires withdrawalBehavior: redirect")
            return self

        if self.publication_state not in _WITHDRAWN_PUBLICATION_STATES:
            raise ValueError(
                "withdrawalBehavior is only allowed when publicationState is withdrawn or tombstoned",
            )
        if (
            self.withdrawal_behavior is WithdrawalBehavior.REDIRECT
            and self.redirect_target is None
        ):
            raise ValueError("withdrawalBehavior redirect requires redirectTarget")
        if (
            self.withdrawal_behavior is not WithdrawalBehavior.REDIRECT
            and self.redirect_target is not None
        ):
            raise ValueError(
                "redirectTarget is only allowed when withdrawalBehavior is redirect"
            )
        return self


class CandidateAggregateEntry(SitePipelineBaseModel):
    """Entry in ``data/candidates.json``."""

    provider: ProviderKey | None = None
    external_id: NonEmptyString | None = None
    external_url: UrlString | None = None
    component_slug: Slug
    artifact_key: ArtifactKey
    version: VersionString
    display_version: NonEmptyString | None = None
    candidate_sequence: int | None = Field(default=None, strict=True, ge=1)
    release_line: NonEmptyString | None = None
    maturity: NonEmptyString | None = None
    vote_status: NonEmptyString | None = None
    created_at: TimestampString | None = None
    published_at: TimestampString | None = None
    assets: list[ProviderAsset] | None = None


class RefAggregateEntry(SitePipelineBaseModel):
    """Entry in ``data/refs.json``."""

    provider: ProviderKey | None = None
    external_id: NonEmptyString | None = None
    external_url: UrlString | None = None
    component_slug: Slug
    artifact_key: ArtifactKey
    kind: RecordKind
    named_ref_key: NonEmptyString | None = None
    ref: RefString
    display_version: NonEmptyString | None = None
    release_line: NonEmptyString | None = None
    maturity: NonEmptyString | None = None

    @model_validator(mode="after")
    def ensure_kind_stays_within_the_ref_subset(self) -> Self:
        if self.kind not in _ALLOWED_REF_KINDS:
            raise ValueError(
                "Ref aggregate kind must be development, namedRef, or lineHead"
            )
        return self


class RouteAggregateEntry(SitePipelineBaseModel):
    """Entry in ``data/routes.json``."""

    origin_key: OriginKey
    base_url: UrlString
    path: PublicPath
    url: UrlString
    component_slug: Slug
    artifact_key: ArtifactKey | None = None
    section: NonEmptyString | None = None
    canonical: bool | None = None
    route_kind: NonEmptyString | None = None
    target_id: NonEmptyString | None = None
    label: NonEmptyString | None = None
    locale: NonEmptyString | None = None

    @model_validator(mode="after")
    def ensure_route_urls_are_consistent(self) -> Self:
        if self.url != _build_expected_url(self.base_url, self.path):
            raise ValueError("Route url must equal baseUrl joined with path")
        return self


class RedirectAggregateEntry(SitePipelineBaseModel):
    """Entry in ``data/redirects.json``."""

    from_url: UrlString
    to_url: UrlString
    status: int = Field(strict=True)
    reason: NonEmptyString | None = None
    source_kind: NonEmptyString | None = None

    @model_validator(mode="after")
    def ensure_status_is_allowed(self) -> Self:
        if self.status not in _ALLOWED_REDIRECT_STATUS_CODES:
            raise ValueError("Redirect status must be one of 301, 302, 307, or 308")
        return self


class TranslationSetAggregateEntry(SitePipelineBaseModel):
    """Entry in ``data/translations.json``."""

    translation_key: NonEmptyString
    component_slug: Slug
    artifact_key: ArtifactKey | None = None
    entries: list[TranslationLinkSummary] = Field(min_length=1)

    @model_validator(mode="after")
    def ensure_locale_entries_are_unique(self) -> Self:
        _ensure_unique_strings(
            [entry.locale for entry in self.entries], type_name="translation locale"
        )
        return self


class CompatibilityAggregateEntry(SitePipelineBaseModel):
    """Entry in ``data/compatibility.json``."""

    subject_id: NonEmptyString
    target_id: NonEmptyString
    relation: NonEmptyString
    scope: NonEmptyString | None = None
    confidence: NonEmptyString | None = None
    notes: NonEmptyString | None = None
    evidence: list[NonEmptyString] | None = None

    @model_validator(mode="after")
    def ensure_evidence_entries_are_unique(self) -> Self:
        if self.evidence is not None:
            _ensure_unique_strings(
                self.evidence, type_name="compatibility evidence entry"
            )
        return self


class MountAggregateEntry(SitePipelineBaseModel):
    """Entry in ``data/mounts.json``."""

    mount_id: NonEmptyString
    owner_id: NonEmptyString
    kind: NonEmptyString
    trust_class: TrustClass
    public_path: PublicPath
    source_ref: MountSourceRef
    version_context: NonEmptyString | None = None
    index_behavior: IndexBehavior | None = None
    metadata: ExtensionsObject | None = None

    @model_validator(mode="after")
    def ensure_metadata_stays_below_the_hard_ceiling(self) -> Self:
        if self.metadata is None:
            return self
        metadata_size_bytes = len(
            serialize_extensions_object(self.metadata).encode("utf-8")
        )
        if metadata_size_bytes > _MAX_MOUNT_METADATA_BYTES:
            raise ValueError(
                "Mount metadata must not exceed 16 KiB after JSON serialization"
            )
        return self


class ContentIndexEntry(SitePipelineBaseModel):
    """Entry in ``data/content-index.json``."""

    id: NonEmptyString
    component_slug: Slug
    artifact_key: ArtifactKey | None = None
    page_kind: NonEmptyString
    section: NonEmptyString | None = None
    origin_key: OriginKey
    path: PublicPath
    url: UrlString
    canonical_url: UrlString | None = None
    title: NonEmptyString | None = None
    link_title: NonEmptyString | None = None
    description: NonEmptyString | None = None
    summary: NonEmptyString | None = None
    weight: int | None = Field(default=None, strict=True)
    parent_id: NonEmptyString | None = None
    ancestor_ids: list[NonEmptyString] | None = None
    source_path: RepoRelativePath | None = None
    version_kind: RecordKind | None = None
    version_label: NonEmptyString | None = None
    release_line: NonEmptyString | None = None
    support_status: NonEmptyString | None = None
    publication_state: PublicationState | None = None
    locale: NonEmptyString | None = None
    default_locale: bool | None = None
    translation_key: NonEmptyString | None = None
    provider: ProviderKey | None = None
    external_id: NonEmptyString | None = None
    maturity: NonEmptyString | None = None
    candidate_sequence: int | None = Field(default=None, strict=True, ge=1)
    vote_status: NonEmptyString | None = None

    @model_validator(mode="after")
    def ensure_ancestors_are_unique(self) -> Self:
        if self.ancestor_ids is not None:
            _ensure_unique_strings(self.ancestor_ids, type_name="ancestor page id")
        return self
