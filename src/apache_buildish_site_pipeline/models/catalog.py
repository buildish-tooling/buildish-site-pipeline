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

"""Consumer-authored catalog document models."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import Field, model_validator

from .base import SitePipelineBaseModel
from .component_repository import SupportStatusDefinition
from .enums import (
    CandidateSelectionMode,
    IndexBehavior,
    LineHeadSelectionMode,
    PublicationState,
    ReleaseSelectionMode,
    RouteMode,
    TrustClass,
    WithdrawalBehavior,
)
from .scalars import (
    ArtifactKey,
    ExtensionsObject,
    Identifier,
    MountSourceRef,
    NonEmptyString,
    OriginKey,
    PositiveInteger,
    PublicPath,
    ReferenceString,
    RefString,
    RegexString,
    RepoRelativePath,
    Slug,
    SourceKey,
    TimestampString,
    UrlString,
    VersionString,
)
from .validation.extensions import serialize_extensions_object

_ALLOWED_REDIRECT_STATUS_CODES = frozenset({301, 302, 307, 308})
_WITHDRAWN_PUBLICATION_STATES = frozenset({PublicationState.WITHDRAWN, PublicationState.TOMBSTONED})
_MAX_MOUNT_METADATA_BYTES = 16 * 1024


def _ensure_unique_strings(values: list[str], *, type_name: str) -> None:
    seen_values: set[str] = set()
    for value in values:
        if value in seen_values:
            raise ValueError(f"Duplicate {type_name} {value!r}")
        seen_values.add(value)


class CatalogDefaults(SitePipelineBaseModel):
    """Shared defaults applied before per-component overrides."""

    metadata_file: RepoRelativePath | None = Field(default=None, description="Default location of `site/component.yaml` within each source tree.")
    pages_root: RepoRelativePath | None = Field(default=None, description="Default repository-relative root for non-versioned component pages.")
    docs_root: RepoRelativePath | None = Field(default=None, description="Default repository-relative root for component docs content.")
    assets_root: RepoRelativePath | None = Field(default=None, description="Default repository-relative root for component static assets.")
    publication: PublicationDefaults | None = Field(default=None, description="Shared publication defaults inherited by components unless they override them.")
    localization: LocalizationConfig | None = Field(default=None, description="Shared localization defaults inherited by components unless they override them.")


class SiteContentConfig(SitePipelineBaseModel):
    """Consumer-owned top-level site pages, assets, and vendor assets."""

    pages_root: RepoRelativePath | None = Field(default=None, description="Repository-relative root for consumer-owned top-level site pages.")
    assets_root: RepoRelativePath | None = Field(default=None, description="Repository-relative root for consumer-owned top-level static assets.")
    vendor_assets: list[TopLevelAssetConfig] | None = Field(default=None, description="Additional imported asset trees mounted into the top-level site assets area.")


class TopLevelAssetConfig(SitePipelineBaseModel):
    """Top-level imported asset tree mounted under site assets."""

    source: RepoRelativePath
    mount_path: PublicPath | None = None
    kind: NonEmptyString | None = None
    ownership: NonEmptyString | None = None


class PublicationDefaults(SitePipelineBaseModel):
    """Default routing segments used to derive publication paths."""

    origin: OriginKey | None = Field(default=None, description="Default publication origin used for component routes when no nearer override is present.")
    development_segment: NonEmptyString | None = Field(default=None, description="Default path segment appended below the component root for moving development/latest docs.")
    docs_segment: NonEmptyString | None = Field(default=None, description="Optional extra path segment appended below the latest docs root when docs should live under an additional nested path.")
    assets_segment: NonEmptyString | None = Field(default=None, description="Default path segment appended below the component root for static assets.")


class LocalizationConfig(SitePipelineBaseModel):
    """Locale and translation defaults."""

    default_locale: NonEmptyString | None = Field(default=None, description="Default locale used when a page does not declare a more specific locale." )
    supported_locales: list[NonEmptyString] | None = Field(default=None, description="Supported locale keys for this site or component.")
    route_mode: RouteMode | None = Field(default=None, description="How localized pages should be routed within the published URL space.")
    fallback_locale: NonEmptyString | None = Field(default=None, description="Fallback locale used when a requested translation is unavailable.")

    @model_validator(mode="after")
    def ensure_locale_membership_and_uniqueness(self) -> Self:
        if self.supported_locales is not None:
            _ensure_unique_strings(self.supported_locales, type_name="supported locale")
            supported_locale_set = set(self.supported_locales)
            if self.default_locale is not None and self.default_locale not in supported_locale_set:
                raise ValueError("defaultLocale must be present in supportedLocales when both are set")
            if self.fallback_locale is not None and self.fallback_locale not in supported_locale_set:
                raise ValueError("fallbackLocale must be present in supportedLocales when both are set")
        return self


class OriginConfig(SitePipelineBaseModel):
    """Named publication origin."""

    base_url: UrlString = Field(description="Base public URL for this publication origin.")
    canonical: bool | None = Field(default=None, description="Whether this origin should be treated as canonical when multiple origins publish the same target.")
    labels: list[NonEmptyString] | None = Field(default=None, description="Optional human-readable labels for renderer or deployment tooling.")


class SourceConfig(SitePipelineBaseModel):
    """Repository or checkout definition."""

    local_dir: RepoRelativePath = Field(description="Workspace-relative checkout or source directory.")
    repository: UrlString | None = Field(default=None, description="Optional remote repository URL associated with this source.")
    default_branch: RefString | None = Field(default=None, description="Optional default branch or ref for this source.")
    metadata_file: RepoRelativePath | None = Field(default=None, description="Optional override for the component metadata file inside this source tree.")


class GroupConfig(SitePipelineBaseModel):
    """Reusable defaults for a set of components."""

    display_name: NonEmptyString | None = Field(default=None, description="Human-readable group name for renderers or generated navigation.")
    path_prefix: PublicPath | None = Field(default=None, description="Shared public path prefix applied to grouped component publication roots.")
    navigation_section: NonEmptyString | None = Field(default=None, description="Optional renderer-facing grouping label for navigation or listings.")
    weight: int | None = Field(default=None, strict=True, description="Optional ordering hint shared by components in this group.")
    publication: PublicationConfig | None = Field(default=None, description="Publication defaults inherited by grouped components unless they override them.")


class ComponentContentSelection(SitePipelineBaseModel):
    """Selection of the source that owns shared component content."""

    source: SourceKey | None = Field(default=None, description="Named source that owns shared component pages, docs, and assets roots.")


class RouteAliasConfig(SitePipelineBaseModel):
    """Additional route resolving to the same published target."""

    path: PublicPath
    origin: OriginKey | None = None
    label: NonEmptyString | None = None


class RedirectRuleConfig(SitePipelineBaseModel):
    """Authored redirect rule resolved into deployment-neutral redirect metadata."""

    from_path: PublicPath
    from_origin: OriginKey | None = None
    target: ReferenceString | UrlString
    status: int | None = Field(default=None, strict=True)
    reason: NonEmptyString | None = None

    @model_validator(mode="after")
    def ensure_redirect_status_is_allowed(self) -> Self:
        if self.status is not None and self.status not in _ALLOWED_REDIRECT_STATUS_CODES:
            raise ValueError("Redirect status must be one of 301, 302, 307, or 308")
        return self


class PublicationConfig(SitePipelineBaseModel):
    """Explicit publication configuration or inherited publication defaults."""

    origin: OriginKey | None = Field(default=None, description="Publication origin key to use for this component or artifact.")
    path_segment: NonEmptyString | None = Field(default=None, description="Path segment appended below an inherited path prefix or mount root.")
    mount_path: PublicPath | None = Field(default=None, description="Explicit public root path for the component publication surface.")
    component_path: PublicPath | None = Field(default=None, description="Explicit public path for the component landing page or overview root.")
    development_path: PublicPath | None = Field(default=None, description="Explicit public path for the moving latest/development docs surface.")
    docs_path: PublicPath | None = Field(default=None, description="Explicit public docs landing path exposed to downstream consumers; defaults to the development/latest path unless an additional docs segment or override is configured.")
    assets_path: PublicPath | None = Field(default=None, description="Explicit public path for static assets below the component root.")
    canonical_path: PublicPath | None = Field(default=None, description="Optional canonical public path used when aliases or multiple origins are present.")
    aliases: list[RouteAliasConfig] | None = Field(default=None, description="Additional public aliases that should resolve to the same published target.")
    redirects: list[RedirectRuleConfig] | None = Field(default=None, description="Redirect rules to emit for legacy or moved routes.")


class NamedRefConfig(SitePipelineBaseModel):
    """Authored named ref intentionally exposed as a publishable version context."""

    key: Identifier
    ref: RefString
    display_name: NonEmptyString | None = None
    maturity: NonEmptyString | None = None
    description: NonEmptyString | None = None


class LineHeadSelectionPolicy(SitePipelineBaseModel):
    """Selection policy for release-line head refs."""

    mode: LineHeadSelectionMode
    keys: list[NonEmptyString] | None = None

    @model_validator(mode="after")
    def ensure_explicit_keys_match_mode(self) -> Self:
        if self.mode is LineHeadSelectionMode.EXPLICIT:
            if not self.keys:
                raise ValueError("Line-head selection mode explicit requires non-empty keys")
        elif self.keys is not None:
            raise ValueError("Line-head selection keys are only allowed when mode is explicit")
        return self


class ReleaseSelectionPolicy(SitePipelineBaseModel):
    """Selection policy for exact released versions."""

    mode: ReleaseSelectionMode
    count: PositiveInteger | None = None
    versions: list[VersionString] | None = None

    @model_validator(mode="after")
    def ensure_mode_specific_fields(self) -> Self:
        if self.mode is ReleaseSelectionMode.LATEST_N:
            if self.count is None:
                raise ValueError("Release selection mode latestN requires count")
            if self.versions is not None:
                raise ValueError("Release selection versions are only allowed for explicit mode")
            return self

        if self.mode is ReleaseSelectionMode.EXPLICIT:
            if not self.versions:
                raise ValueError("Release selection mode explicit requires versions")
            if self.count is not None:
                raise ValueError("Release selection count is only allowed for latestN mode")
            return self

        if self.count is not None:
            raise ValueError("Release selection count is only allowed for latestN mode")
        if self.versions is not None:
            raise ValueError("Release selection versions are only allowed for explicit mode")
        return self


class CandidateSelectionPolicy(SitePipelineBaseModel):
    """Selection policy for release candidates."""

    mode: CandidateSelectionMode
    versions: list[VersionString] | None = None
    external_ids: list[NonEmptyString] | None = None

    @model_validator(mode="after")
    def ensure_mode_specific_fields(self) -> Self:
        if self.mode is CandidateSelectionMode.EXPLICIT:
            if not self.versions:
                raise ValueError("Candidate selection mode explicit requires versions")
            return self

        if self.versions is not None or self.external_ids is not None:
            raise ValueError(
                "Candidate selection versions and externalIds are only allowed for explicit mode",
            )
        return self


class PublicationSelectionPolicy(SitePipelineBaseModel):
    """Planning-time policy for which version contexts are staged and surfaced."""

    development: bool | None = None
    line_heads: LineHeadSelectionPolicy | None = None
    releases: ReleaseSelectionPolicy | None = None
    named_refs: list[Identifier] | None = None
    candidates: CandidateSelectionPolicy | None = None

    @model_validator(mode="after")
    def ensure_named_refs_are_unique(self) -> Self:
        if self.named_refs is not None:
            _ensure_unique_strings(self.named_refs, type_name="publication selected namedRef")
        return self


class ArtifactVersioningConfig(SitePipelineBaseModel):
    """Artifact-specific version-discovery configuration."""

    development_ref: RefString
    maintenance_ref_pattern: NonEmptyString | None = None
    tag_pattern: RegexString
    named_refs: list[NamedRefConfig] | None = None

    @model_validator(mode="after")
    def ensure_named_ref_keys_are_unique(self) -> Self:
        if self.named_refs is None:
            return self

        _ensure_unique_strings([named_ref.key for named_ref in self.named_refs], type_name="named ref key")
        return self


class SupportWindow(SitePipelineBaseModel):
    """Structured support-window metadata for a line or exact release."""

    release_date: TimestampString | None = None
    maintenance_phase: NonEmptyString | None = None
    end_of_active_support_date: TimestampString | None = None
    end_of_support_date: TimestampString | None = None
    end_of_life_date: TimestampString | None = None
    support_policy_url: UrlString | None = None
    notes: NonEmptyString | None = None

    @model_validator(mode="after")
    def ensure_dates_are_in_order(self) -> Self:
        ordered_dates = [
            ("releaseDate", self.release_date),
            ("endOfActiveSupportDate", self.end_of_active_support_date),
            ("endOfSupportDate", self.end_of_support_date),
            ("endOfLifeDate", self.end_of_life_date),
        ]
        previous_name: str | None = None
        previous_value = None
        for current_name, current_value in ordered_dates:
            if current_value is None:
                continue
            if previous_value is not None and current_value < previous_value:
                raise ValueError(f"Support-window dates must be ordered: {previous_name} <= {current_name}")
            previous_name = current_name
            previous_value = current_value
        return self


class ReleaseLineConfig(SitePipelineBaseModel):
    """Artifact-authored release-line definition."""

    key: NonEmptyString
    display_name: NonEmptyString | None = None
    parent: NonEmptyString | None = None
    latest: VersionString
    support_status: NonEmptyString | None = None
    aliases: list[NonEmptyString] | None = None
    maintenance_ref: RefString | None = None
    support_window: SupportWindow | None = None


class ExactReleaseConfig(SitePipelineBaseModel):
    """Authored exact-release metadata or publication override for one version."""

    version: VersionString
    release_line: NonEmptyString | None = None
    support_status: NonEmptyString | None = None
    support_window: SupportWindow | None = None
    publication_state: PublicationState | None = None
    withdrawal_behavior: WithdrawalBehavior | None = None
    redirect_target: ReferenceString | UrlString | None = None
    reason: NonEmptyString | None = None

    @model_validator(mode="after")
    def ensure_withdrawal_fields_are_consistent(self) -> Self:
        if self.withdrawal_behavior is None:
            if self.redirect_target is not None:
                raise ValueError("redirectTarget requires withdrawalBehavior: redirect")
            return self

        if self.publication_state not in _WITHDRAWN_PUBLICATION_STATES:
            raise ValueError(
                "withdrawalBehavior is only allowed when publicationState is withdrawn or tombstoned",
            )
        if self.withdrawal_behavior is WithdrawalBehavior.REDIRECT and self.redirect_target is None:
            raise ValueError("withdrawalBehavior redirect requires redirectTarget")
        if self.withdrawal_behavior is not WithdrawalBehavior.REDIRECT and self.redirect_target is not None:
            raise ValueError("redirectTarget is only allowed when withdrawalBehavior is redirect")
        return self


class MountConfig(SitePipelineBaseModel):
    """Generated or imported subtree mounted into the publication surface."""

    source: MountSourceRef
    mount_path: PublicPath
    kind: NonEmptyString
    trust_class: TrustClass
    version_scope: NonEmptyString | None = None
    index_behavior: IndexBehavior | None = None
    ownership: NonEmptyString | None = None
    metadata: ExtensionsObject | None = None

    @model_validator(mode="after")
    def ensure_metadata_stays_below_the_hard_ceiling(self) -> Self:
        if self.metadata is None:
            return self
        metadata_size_bytes = len(serialize_extensions_object(self.metadata).encode("utf-8"))
        if metadata_size_bytes > _MAX_MOUNT_METADATA_BYTES:
            raise ValueError("Mount metadata must not exceed 16 KiB after JSON serialization")
        return self


class CompatibilityAssertionConfig(SitePipelineBaseModel):
    """Authored compatibility relationship between published identities."""

    subject_ref: ReferenceString
    target_ref: ReferenceString
    relation: NonEmptyString
    scope: NonEmptyString | None = None
    confidence: NonEmptyString | None = None
    notes: NonEmptyString | None = None


class ArtifactLifecycleConfig(SitePipelineBaseModel):
    """Artifact-authored lifecycle metadata."""

    latest_stable: VersionString | None = None
    release_lines: list[ReleaseLineConfig] | None = None
    releases: list[ExactReleaseConfig] | None = None
    support_status_vocabulary: dict[Identifier, SupportStatusDefinition] | None = None
    support_policy_url: UrlString | None = None
    default_support_window: SupportWindow | None = None

    @model_validator(mode="after")
    def ensure_release_lines_and_versions_are_unique_and_acyclic(self) -> Self:
        if self.releases is not None:
            _ensure_unique_strings([release.version for release in self.releases], type_name="exact release version")

        if self.release_lines is None:
            return self

        release_line_keys = [release_line.key for release_line in self.release_lines]
        _ensure_unique_strings(release_line_keys, type_name="release-line key")
        known_release_line_keys = set(release_line_keys)

        for release_line in self.release_lines:
            if release_line.parent is not None and release_line.parent not in known_release_line_keys:
                raise ValueError(f"Unknown release-line parent {release_line.parent!r}")

        visiting: set[str] = set()
        visited: set[str] = set()
        parents_by_key = {release_line.key: release_line.parent for release_line in self.release_lines}

        def visit(release_line_key: str) -> None:
            if release_line_key in visited:
                return
            if release_line_key in visiting:
                raise ValueError("Release-line parent chains must not contain cycles")

            visiting.add(release_line_key)
            parent_key = parents_by_key[release_line_key]
            if parent_key is not None:
                visit(parent_key)
            visiting.remove(release_line_key)
            visited.add(release_line_key)

        for release_line_key in release_line_keys:
            visit(release_line_key)

        return self


class ArtifactConfig(SitePipelineBaseModel):
    """Independently versioned release unit within a component."""

    key: ArtifactKey
    display_name: NonEmptyString | None = None
    source: SourceKey
    docs_root: RepoRelativePath | None = None
    assets_root: RepoRelativePath | None = None
    versioning: ArtifactVersioningConfig
    publication_selection: PublicationSelectionPolicy | None = None
    lifecycle: ArtifactLifecycleConfig | None = None
    compatibility: list[CompatibilityAssertionConfig] | None = None
    mounts: list[MountConfig] | None = None


class ComponentCatalogEntry(SitePipelineBaseModel):
    """One component entry in the consumer catalog."""

    slug: Slug = Field(description="Stable component identifier.")
    display_name: NonEmptyString | None = Field(default=None, description="Human-readable component name override or convenience value.")
    local_dir: RepoRelativePath | None = Field(default=None, description="Simple shorthand for binding the component to one workspace-local checkout directory.")
    weight: int | None = Field(
        default=None,
        strict=True,
        description="Optional ordering hint for component listings, menus, and other consumer-rendered component collections.",
    )
    group: Identifier | None = Field(default=None, description="Optional group key for inherited defaults and renderer grouping.")
    content: ComponentContentSelection | None = Field(default=None, description="Shared content-source selection for component pages, docs, and assets.")
    publication: PublicationConfig | None = Field(default=None, description="Explicit publication configuration for this component.")
    publication_selection: PublicationSelectionPolicy | None = Field(default=None, description="Default version-context selection policy inherited by contained artifacts unless they override it.")
    localization: LocalizationConfig | None = Field(default=None, description="Component-specific localization overrides.")
    compatibility: list[CompatibilityAssertionConfig] | None = Field(default=None, description="Component-level compatibility assertions emitted into staged metadata.")
    mounts: list[MountConfig] | None = Field(default=None, description="Component-level generated or imported documentation mounts.")
    artifacts: list[ArtifactConfig] | None = Field(default=None, description="Independently versioned artifacts belonging to this component.")

    @model_validator(mode="after")
    def ensure_artifact_keys_are_unique(self) -> Self:
        if self.artifacts is None:
            return self
        _ensure_unique_strings([artifact.key for artifact in self.artifacts], type_name="artifact key")
        return self


class CatalogDocumentV1(SitePipelineBaseModel):
    """Consumer-authored component catalog document."""

    schema_version: Literal[1] = Field(description="Schema version for the catalog format.")
    defaults: CatalogDefaults | None = Field(default=None, description="Shared default settings applied before per-component overrides.")
    site: SiteContentConfig | None = Field(default=None, description="Consumer-owned top-level site pages, assets, and vendor-asset declarations.")
    origins: dict[OriginKey, OriginConfig] | None = Field(default=None, description="Named publication origins that components can target.")
    sources: dict[SourceKey, SourceConfig] | None = Field(default=None, description="Named repository or checkout bindings used by components and artifacts.")
    groups: dict[Identifier, GroupConfig] | None = Field(default=None, description="Optional grouping defaults shared by multiple components.")
    components: list[ComponentCatalogEntry] = Field(description="Participating components in this consumer-authored catalog.")

    @model_validator(mode="after")
    def ensure_document_cross_references(self) -> Self:
        _ensure_unique_strings([component.slug for component in self.components], type_name="component slug")

        origin_keys = set(self.origins or {})
        source_keys = set(self.sources or {})
        group_keys = set(self.groups or {})

        def validate_origin_reference(origin: OriginKey | None, *, location: str) -> None:
            if origin is None:
                return
            if origin not in origin_keys:
                raise ValueError(f"Unknown origin key {origin!r} referenced by {location}")

        def validate_publication_origins(publication: PublicationConfig | None, *, location: str) -> None:
            if publication is None:
                return
            validate_origin_reference(publication.origin, location=f"{location}.origin")
            if publication.aliases is not None:
                for index, alias in enumerate(publication.aliases):
                    validate_origin_reference(alias.origin, location=f"{location}.aliases[{index}].origin")
            if publication.redirects is not None:
                for index, redirect in enumerate(publication.redirects):
                    validate_origin_reference(
                        redirect.from_origin,
                        location=f"{location}.redirects[{index}].fromOrigin",
                    )

        if self.defaults is not None:
            validate_origin_reference(
                self.defaults.publication.origin if self.defaults.publication is not None else None,
                location="defaults.publication.origin",
            )

        if self.groups is not None:
            for group_key, group in self.groups.items():
                validate_publication_origins(group.publication, location=f"groups[{group_key!r}].publication")

        for component in self.components:
            if component.group is not None and component.group not in group_keys:
                raise ValueError(f"Unknown group key {component.group!r} referenced by component {component.slug!r}")

            if component.content is not None and component.content.source is not None and component.content.source not in source_keys:
                raise ValueError(
                    f"Unknown source key {component.content.source!r} referenced by component {component.slug!r}",
                )

            validate_publication_origins(component.publication, location=f"component {component.slug!r}.publication")

            if component.artifacts is None:
                continue

            for artifact in component.artifacts:
                if artifact.source not in source_keys:
                    raise ValueError(
                        f"Unknown source key {artifact.source!r} referenced by artifact {artifact.key!r}",
                    )
                self._validate_publication_selection_references(component, artifact)

        return self

    def _validate_publication_selection_references(
        self,
        component: ComponentCatalogEntry,
        artifact: ArtifactConfig,
    ) -> None:
        for location, selection in (
            (f"component {component.slug!r}.publicationSelection", component.publication_selection),
            (f"artifact {component.slug!r}/{artifact.key!r}.publicationSelection", artifact.publication_selection),
        ):
            if selection is None:
                continue
            self._validate_named_ref_selection(selection, artifact, location=location)
            self._validate_line_head_selection(selection, artifact, location=location)

    def _validate_named_ref_selection(
        self,
        selection: PublicationSelectionPolicy,
        artifact: ArtifactConfig,
        *,
        location: str,
    ) -> None:
        if selection.named_refs is None:
            return
        known_named_ref_keys = {
            named_ref.key for named_ref in (artifact.versioning.named_refs or [])
        }
        for named_ref_key in selection.named_refs:
            if named_ref_key not in known_named_ref_keys:
                raise ValueError(f"Unknown namedRef key {named_ref_key!r} referenced by {location}")

    def _validate_line_head_selection(
        self,
        selection: PublicationSelectionPolicy,
        artifact: ArtifactConfig,
        *,
        location: str,
    ) -> None:
        if selection.line_heads is None or selection.line_heads.keys is None:
            return
        known_release_line_keys = {
            release_line.key for release_line in (artifact.lifecycle.release_lines or [])
        } if artifact.lifecycle is not None else set()
        for release_line_key in selection.line_heads.keys:
            if release_line_key not in known_release_line_keys:
                raise ValueError(f"Unknown release-line key {release_line_key!r} referenced by {location}")