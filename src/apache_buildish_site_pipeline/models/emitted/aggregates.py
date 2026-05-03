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

from ...docs.documentation import PipelineDerivedModel as SitePipelineBaseModel
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

    key: ProviderKey = Field(
        description="Stable provider identifier used by aggregate entries that originate from this provider.",
        examples=["github-releases"],
    )
    type: NonEmptyString = Field(
        description="Provider implementation type, such as `github` or another fetcher backend label.",
        examples=["github"],
    )
    display_name: NonEmptyString | None = Field(
        default=None,
        description="Human-readable provider label shown in generated metadata or diagnostics.",
        examples=["GitHub Releases"],
    )
    base_url: ProviderBaseUrl | None = Field(
        default=None,
        description="Base URL of the provider service when records can link back to a human-browsable upstream origin.",
    )
    fetched_at: TimestampString = Field(
        description="Timestamp when this provider descriptor was fetched or refreshed."
    )


class ComponentsDataEntry(SitePipelineBaseModel):
    """Entry in ``data/components.json``."""

    slug: Slug = Field(
        description="Stable component slug used by routes, aggregates, and typed references.",
        examples=["spark"],
    )
    display_name: NonEmptyString | None = Field(
        default=None,
        description="Human-readable component name shown in navigation, listings, and generated metadata.",
        examples=["Apache Spark"],
    )
    latest_stable: VersionString | None = Field(
        default=None,
        description="Most recent stable version recommended for the component as a whole when one shared release line is enough.",
        examples=["4.0.1"],
    )
    weight: int | None = Field(
        default=None,
        strict=True,
        description="Optional ordering hint copied from the authored catalog for consumer-rendered component lists.",
    )
    group: Identifier | None = Field(
        default=None,
        description="Optional group key copied from the authored catalog to support grouped rendering or filtering.",
        examples=["data-platform"],
    )
    origin_key: OriginKey = Field(
        description="Origin key selected for this component's primary published route set.",
        examples=["archive"],
    )
    publication: ResolvedPublication = Field(
        description="Resolved publication roots and URLs for the component."
    )
    provider_keys: list[ProviderKey] | None = Field(
        default=None,
        description="Provider keys that contributed version metadata for this component's artifacts.",
        examples=[["github-releases"]],
    )
    artifacts: list[ArtifactFrontMatterSummary] | None = Field(
        default=None,
        description="Compact artifact summaries used by component listings and page chrome."
    )

    @model_validator(mode="after")
    def ensure_origin_key_and_provider_keys_are_consistent(self) -> Self:
        if self.origin_key != self.publication.origin.key:
            raise ValueError("originKey must match publication.origin.key")
        if self.provider_keys is not None:
            _ensure_unique_strings(self.provider_keys, type_name="provider key")
        return self


class LatestReleaseSummary(SitePipelineBaseModel):
    """Compact latest-release summary embedded in artifact aggregates."""

    version: VersionString = Field(
        description="Exact version string of the latest known release.",
        examples=["4.0.1"],
    )
    display_version: NonEmptyString | None = Field(
        default=None,
        description="Human-readable label for the latest release when it should differ from the raw version string.",
    )
    tag: NonEmptyString | None = Field(
        default=None,
        description="Tag associated with the latest release, if known.",
        examples=["v4.0.1"],
    )
    publication_state: PublicationState | None = Field(
        default=None,
        description="Publication-state label for the latest release, such as published or withdrawn."
    )
    published_at: TimestampString | None = Field(
        default=None,
        description="Timestamp when the latest release became publicly available."
    )


class LatestCandidateSummary(SitePipelineBaseModel):
    """Compact latest-candidate summary embedded in artifact aggregates."""

    version: VersionString | None = Field(
        default=None,
        description="Candidate version string when the provider exposes one.",
        examples=["4.1.0-rc1"],
    )
    display_version: NonEmptyString | None = Field(
        default=None,
        description="Human-readable candidate label when it should differ from the raw version string."
    )
    candidate_sequence: int | None = Field(
        default=None,
        strict=True,
        ge=1,
        description="Numeric ordering hint for the candidate, usually the `rc` sequence number.",
        examples=[1],
    )
    vote_status: NonEmptyString | None = Field(
        default=None,
        description="Vote-status label for the latest candidate when it is known.",
        examples=["passed"],
    )


class ArtifactsDataEntry(SitePipelineBaseModel):
    """Entry in ``data/artifacts.json``."""

    component_slug: Slug = Field(
        description="Owning component slug for the artifact.",
        examples=["spark"],
    )
    key: ArtifactKey = Field(
        description="Stable artifact key used by routes, aggregates, and typed references.",
        examples=["runtime"],
    )
    display_name: NonEmptyString | None = Field(
        default=None,
        description="Human-readable artifact label shown in navigation and metadata.",
        examples=["Runtime"],
    )
    source_key: SourceKey | None = Field(
        default=None,
        description="Named source binding that owns the artifact's docs and assets.",
        examples=["apache-spark"],
    )
    docs_root: RepoRelativePath | None = Field(
        default=None,
        description="Repository-relative docs root for the artifact when it differs from the component default.",
        examples=["docs/runtime"],
    )
    provider_keys: list[ProviderKey] | None = Field(
        default=None,
        description="Provider keys that contributed version metadata for this artifact.",
        examples=[["github-releases"]],
    )
    versioning: ArtifactVersioningConfig | None = Field(
        default=None,
        description="Version-discovery rules that explain how development refs, tags, and named refs are derived for the artifact."
    )
    latest_stable: VersionString | None = Field(
        default=None,
        description="Most recent stable version recommended for readers.",
        examples=["4.0.1"],
    )
    latest_release: LatestReleaseSummary | None = Field(
        default=None,
        description="Compact summary of the latest known release for the artifact."
    )
    latest_candidate: LatestCandidateSummary | None = Field(
        default=None,
        description="Compact summary of the latest known release candidate for the artifact."
    )
    release_lines: list[ReleaseLineSummary] | None = Field(
        default=None,
        description="Release-line summaries associated with the artifact."
    )
    named_refs: list[RefAggregateEntry] | None = Field(
        default=None,
        description="Published development, line-head, or named-ref contexts associated with the artifact."
    )
    support_status_vocabulary: dict[NonEmptyString, SupportStatusDefinition] | None = (
        Field(
            default=None,
            description="Reusable support-status definitions that release lines and releases for this artifact can refer to by key.",
        )
    )
    support_policy_url: UrlString | None = Field(
        default=None,
        description="Canonical URL for the support policy document associated with this artifact."
    )

    @model_validator(mode="after")
    def ensure_provider_keys_are_unique(self) -> Self:
        if self.provider_keys is not None:
            _ensure_unique_strings(self.provider_keys, type_name="provider key")
        return self


class ReleaseAggregateEntry(SitePipelineBaseModel):
    """Entry in ``data/releases.json``."""

    provider: ProviderKey | None = Field(
        default=None,
        description="Provider key for the upstream system that supplied this release record.",
        examples=["github-releases"],
    )
    external_id: NonEmptyString | None = Field(
        default=None,
        description="Provider-specific stable identifier for the upstream release record.",
        examples=["github:release:runtime-4.0.0"],
    )
    external_url: UrlString | None = Field(
        default=None,
        description="Human-browsable upstream URL for the release record."
    )
    component_slug: Slug = Field(
        description="Owning component slug for the release.",
        examples=["spark"],
    )
    artifact_key: ArtifactKey = Field(
        description="Owning artifact key for the release.",
        examples=["runtime"],
    )
    version: VersionString = Field(
        description="Exact released version represented by this aggregate entry.",
        examples=["4.0.0"],
    )
    display_version: NonEmptyString | None = Field(
        default=None,
        description="Human-readable version label when it should differ from the raw version string."
    )
    tag: NonEmptyString | None = Field(
        default=None,
        description="Exact tag associated with the release, if known.",
        examples=["v4.0.0"],
    )
    release_line: NonEmptyString | None = Field(
        default=None,
        description="Release-line key that groups this release with related versions.",
        examples=["4.0"],
    )
    release_line_ancestors: list[NonEmptyString] | None = Field(
        default=None,
        description="Ancestor release-line keys ordered from nearest to farthest.",
        examples=[["4.x", "stable"]],
    )
    support_status: NonEmptyString | None = Field(
        default=None,
        description="Support-status key or label associated with the release.",
        examples=["supported"],
    )
    support_window: SupportWindow | None = Field(
        default=None,
        description="Lifecycle dates and support notes associated with the release."
    )
    publication_state: PublicationState | None = Field(
        default=None,
        description="Publication-state label for the release, such as published, withdrawn, or tombstoned."
    )
    withdrawal_behavior: WithdrawalBehavior | None = Field(
        default=None,
        description="Behavior that readers should experience when the release has been withdrawn."
    )
    redirect_target: ReferenceString | UrlString | None = Field(
        default=None,
        description="Replacement route or external URL used when a withdrawn release redirects readers elsewhere.",
        examples=["route:/spark/releases/4.0.1/"],
    )
    maturity: NonEmptyString | None = Field(
        default=None,
        description="Maturity label such as stable, preview, or beta.",
        examples=["stable"],
    )
    published_at: TimestampString | None = Field(
        default=None,
        description="Timestamp when the release became publicly available."
    )
    assets: list[ProviderAsset] | None = Field(
        default=None,
        description="Downloadable assets attached to the release."
    )
    urls: dict[NonEmptyString, UrlString] | None = Field(
        default=None,
        description="Additional named URLs related to the release, such as notes, downloads, or verification material."
    )

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

    provider: ProviderKey | None = Field(default=None, description="Provider key for the upstream system that supplied this candidate record.")
    external_id: NonEmptyString | None = Field(default=None, description="Provider-specific stable identifier for the upstream candidate record.")
    external_url: UrlString | None = Field(default=None, description="Human-browsable upstream URL for the candidate record.")
    component_slug: Slug = Field(description="Owning component slug for the candidate.", examples=["spark"])
    artifact_key: ArtifactKey = Field(description="Owning artifact key for the candidate.", examples=["runtime"])
    version: VersionString = Field(description="Candidate version string represented by this aggregate entry.", examples=["4.1.0-rc1"])
    display_version: NonEmptyString | None = Field(default=None, description="Human-readable candidate label when it should differ from the raw version string.")
    candidate_sequence: int | None = Field(default=None, strict=True, ge=1, description="Numeric ordering hint for the candidate, usually the `rc` sequence number.", examples=[1])
    release_line: NonEmptyString | None = Field(default=None, description="Release-line key that the candidate belongs to, if known.", examples=["4.1"])
    maturity: NonEmptyString | None = Field(default=None, description="Maturity label associated with the candidate.", examples=["preview"])
    vote_status: NonEmptyString | None = Field(default=None, description="Vote-status label for the candidate, if known.", examples=["passed"])
    created_at: TimestampString | None = Field(default=None, description="Timestamp when the candidate record was first created.")
    published_at: TimestampString | None = Field(default=None, description="Timestamp when the candidate became publicly visible.")
    assets: list[ProviderAsset] | None = Field(default=None, description="Downloadable assets attached to the candidate.")


class RefAggregateEntry(SitePipelineBaseModel):
    """Entry in ``data/refs.json``."""

    provider: ProviderKey | None = Field(default=None, description="Provider key for the upstream system that supplied this ref record.")
    external_id: NonEmptyString | None = Field(default=None, description="Provider-specific stable identifier for the upstream ref record.")
    external_url: UrlString | None = Field(default=None, description="Human-browsable upstream URL for the ref record.")
    component_slug: Slug = Field(description="Owning component slug for the ref context.", examples=["spark"])
    artifact_key: ArtifactKey = Field(description="Owning artifact key for the ref context.", examples=["runtime"])
    kind: RecordKind = Field(description="Ref context kind, limited to development, named-ref, and line-head entries.")
    named_ref_key: NonEmptyString | None = Field(default=None, description="Catalog-authored named-ref key when this entry represents a named ref.", examples=["preview"])
    ref: RefString = Field(description="Exact source-control ref for the published ref context.", examples=["refs/heads/main"])
    display_version: NonEmptyString | None = Field(default=None, description="Human-readable label for the ref context.", examples=["main"])
    release_line: NonEmptyString | None = Field(default=None, description="Release-line key when the ref context represents a line head.", examples=["4.0"])
    maturity: NonEmptyString | None = Field(default=None, description="Maturity label associated with the ref context.", examples=["preview"])

    @model_validator(mode="after")
    def ensure_kind_stays_within_the_ref_subset(self) -> Self:
        if self.kind not in _ALLOWED_REF_KINDS:
            raise ValueError(
                "Ref aggregate kind must be development, namedRef, or lineHead"
            )
        return self


class RouteAggregateEntry(SitePipelineBaseModel):
    """Entry in ``data/routes.json``."""

    origin_key: OriginKey = Field(description="Origin key that this public route belongs to.", examples=["archive"])
    base_url: UrlString = Field(description="Base URL for the route's origin.")
    path: PublicPath = Field(description="Public path for the route.", examples=["/spark/4.0.0/docs/"])
    url: UrlString = Field(description="Absolute URL for the route after joining `baseUrl` and `path`.")
    component_slug: Slug = Field(description="Owning component slug for the route.", examples=["spark"])
    artifact_key: ArtifactKey | None = Field(default=None, description="Owning artifact key when the route belongs to a specific artifact.", examples=["runtime"])
    section: NonEmptyString | None = Field(default=None, description="Higher-level section label for the route, if present.", examples=["documentation"])
    canonical: bool | None = Field(default=None, description="Whether this route should be treated as the canonical route among equivalent alternatives.")
    route_kind: NonEmptyString | None = Field(default=None, description="Short route-kind label such as component root, docs root, alias, or release page.", examples=["docsRoot"])
    target_id: NonEmptyString | None = Field(default=None, description="Stable target identifier used to correlate equivalent routes or aliases.", examples=["spark-runtime-4.0.0-docs"])
    label: NonEmptyString | None = Field(default=None, description="Human-readable label for the route, if present.", examples=["4.0 docs"])
    locale: NonEmptyString | None = Field(default=None, description="Locale key when the route belongs to a localized page family.", examples=["en"])

    @model_validator(mode="after")
    def ensure_route_urls_are_consistent(self) -> Self:
        if self.url != _build_expected_url(self.base_url, self.path):
            raise ValueError("Route url must equal baseUrl joined with path")
        return self


class RedirectAggregateEntry(SitePipelineBaseModel):
    """Entry in ``data/redirects.json``."""

    from_url: UrlString = Field(description="Absolute source URL that should redirect.")
    to_url: UrlString = Field(description="Absolute destination URL that the redirect should send readers to.")
    status: int = Field(strict=True, description="HTTP redirect status code emitted for this redirect.", examples=[308])
    reason: NonEmptyString | None = Field(default=None, description="Short explanation of why the redirect exists.")
    source_kind: NonEmptyString | None = Field(default=None, description="Short label describing where the redirect originated, such as an alias or withdrawn release rule.", examples=["withdrawnRelease"])

    @model_validator(mode="after")
    def ensure_status_is_allowed(self) -> Self:
        if self.status not in _ALLOWED_REDIRECT_STATUS_CODES:
            raise ValueError("Redirect status must be one of 301, 302, 307, or 308")
        return self


class TranslationSetAggregateEntry(SitePipelineBaseModel):
    """Entry in ``data/translations.json``."""

    translation_key: NonEmptyString = Field(description="Shared key that ties all translated sibling pages in this set together.", examples=["spark-overview"])
    component_slug: Slug = Field(description="Owning component slug for the translation set.", examples=["spark"])
    artifact_key: ArtifactKey | None = Field(default=None, description="Owning artifact key when the translation set belongs to a specific artifact.", examples=["runtime"])
    entries: list[TranslationLinkSummary] = Field(min_length=1, description="Translated sibling pages that belong to the same translation set.")

    @model_validator(mode="after")
    def ensure_locale_entries_are_unique(self) -> Self:
        _ensure_unique_strings(
            [entry.locale for entry in self.entries], type_name="translation locale"
        )
        return self


class CompatibilityAggregateEntry(SitePipelineBaseModel):
    """Entry in ``data/compatibility.json``."""

    subject_id: NonEmptyString = Field(description="Typed reference or aggregate identifier for the subject of the compatibility statement.", examples=["artifact:spark/runtime"])
    target_id: NonEmptyString = Field(description="Typed reference or aggregate identifier for the target of the compatibility statement.", examples=["artifact:spark/operator"])
    relation: NonEmptyString = Field(description="Relationship label that names the compatibility statement.", examples=["testedWith"])
    scope: NonEmptyString | None = Field(default=None, description="Optional scope label that narrows the compatibility statement.", examples=["kubernetes"])
    confidence: NonEmptyString | None = Field(default=None, description="Optional confidence label that explains how strong the supporting evidence is.", examples=["verified"])
    notes: NonEmptyString | None = Field(default=None, description="Additional human-readable explanation, caveats, or migration advice for the compatibility statement.")
    evidence: list[NonEmptyString] | None = Field(default=None, description="Named evidence pointers or short evidence labels that support the compatibility statement.")

    @model_validator(mode="after")
    def ensure_evidence_entries_are_unique(self) -> Self:
        if self.evidence is not None:
            _ensure_unique_strings(
                self.evidence, type_name="compatibility evidence entry"
            )
        return self


class MountAggregateEntry(SitePipelineBaseModel):
    """Entry in ``data/mounts.json``."""

    mount_id: NonEmptyString = Field(description="Stable aggregate identifier for the mount entry.", examples=["spark-runtime-generated-api"])
    owner_id: NonEmptyString = Field(description="Aggregate identifier for the component or artifact that owns the mount.", examples=["artifact:spark/runtime"])
    kind: NonEmptyString = Field(description="Short mount kind label that tells consumers what sort of subtree this is.", examples=["generatedApi"])
    trust_class: TrustClass = Field(description="Trust level assigned to the mounted content.")
    public_path: PublicPath = Field(description="Public path where the mounted subtree is published.", examples=["/spark/api/"])
    source_ref: MountSourceRef = Field(description="Typed source reference for the generated or imported subtree being mounted.", examples=["generated/api"])
    version_context: NonEmptyString | None = Field(default=None, description="Optional version-context label that scopes the mount to one publication context.", examples=["release"])
    index_behavior: IndexBehavior | None = Field(default=None, description="How the mounted subtree should participate in generated indexes or listings.")
    metadata: ExtensionsObject | None = Field(default=None, description="Small JSON-like extension object for extra mount metadata consumed by downstream tooling.")

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

    id: NonEmptyString = Field(description="Stable identifier for the indexed page entry.", examples=["spark-runtime-4.0.0-getting-started"])
    component_slug: Slug = Field(description="Owning component slug for the indexed page.", examples=["spark"])
    artifact_key: ArtifactKey | None = Field(default=None, description="Owning artifact key when the page belongs to a specific artifact.", examples=["runtime"])
    page_kind: NonEmptyString = Field(description="Short page-kind label used for filtering and presentation.", examples=["docsPage"])
    section: NonEmptyString | None = Field(default=None, description="Higher-level section label used for navigation or filtering.", examples=["documentation"])
    origin_key: OriginKey = Field(description="Origin key that this indexed page belongs to.", examples=["archive"])
    path: PublicPath = Field(description="Published public path for the page.", examples=["/spark/4.0.0/docs/getting-started/"])
    url: UrlString = Field(description="Canonical absolute URL for the page.")
    canonical_url: UrlString | None = Field(default=None, description="Explicit canonical URL when it should differ from `url`.")
    title: NonEmptyString | None = Field(default=None, description="Primary page title shown to readers.", examples=["Getting Started"])
    link_title: NonEmptyString | None = Field(default=None, description="Shorter title variant used in navigation or link lists.", examples=["Start"])
    description: NonEmptyString | None = Field(default=None, description="Longer page description intended for metadata or search snippets.")
    summary: NonEmptyString | None = Field(default=None, description="Short summary used for listings, cards, or lightweight search results.")
    weight: int | None = Field(default=None, strict=True, description="Optional ordering hint used by renderers for listings or navigation.", examples=[100])
    parent_id: NonEmptyString | None = Field(default=None, description="Identifier of the parent indexed page when the page belongs to a hierarchy.", examples=["spark-runtime-4.0.0-docs-root"])
    ancestor_ids: list[NonEmptyString] | None = Field(default=None, description="Ancestor page identifiers ordered from nearest to farthest.", examples=[["spark-runtime-4.0.0-docs-root", "spark-runtime-root"]])
    source_path: RepoRelativePath | None = Field(default=None, description="Repository-relative source file path for the page when it is known.", examples=["docs/runtime/getting-started.md"])
    version_kind: RecordKind | None = Field(default=None, description="Version-context kind attached when the page belongs to a versioned route set.")
    version_label: NonEmptyString | None = Field(default=None, description="Human-readable version label attached to the page, if present.", examples=["4.0.0"])
    release_line: NonEmptyString | None = Field(default=None, description="Release-line key attached to the page, if present.", examples=["4.0"])
    support_status: NonEmptyString | None = Field(default=None, description="Support-status key or label attached to the page's version context.", examples=["supported"])
    publication_state: PublicationState | None = Field(default=None, description="Publication-state label attached to the page's version context.")
    locale: NonEmptyString | None = Field(default=None, description="Locale key for the page when the page participates in localization.", examples=["en"])
    default_locale: bool | None = Field(default=None, description="Whether the page represents the default locale within its translation group.")
    translation_key: NonEmptyString | None = Field(default=None, description="Shared key that ties translated sibling pages together.", examples=["spark-overview"])
    provider: ProviderKey | None = Field(default=None, description="Provider key for the upstream record that informed the page's version metadata.")
    external_id: NonEmptyString | None = Field(default=None, description="Provider-specific stable identifier for the upstream record that informed the page.")
    maturity: NonEmptyString | None = Field(default=None, description="Maturity label such as preview, beta, or stable.", examples=["stable"])
    candidate_sequence: int | None = Field(default=None, strict=True, ge=1, description="Release-candidate sequence number when the page belongs to a candidate context.", examples=[1])
    vote_status: NonEmptyString | None = Field(default=None, description="Vote-status label when the page belongs to a candidate context.", examples=["passed"])

    @model_validator(mode="after")
    def ensure_ancestors_are_unique(self) -> Self:
        if self.ancestor_ids is not None:
            _ensure_unique_strings(self.ancestor_ids, type_name="ancestor page id")
        return self
