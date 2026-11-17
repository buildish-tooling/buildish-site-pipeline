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

"""Consumer-authored catalog document models."""

from __future__ import annotations

from typing import ClassVar, Literal, Self

from pydantic import Field, model_validator

from ...docs.documentation import (
    ConsumerOwnedAuthoredModel as SitePipelineBaseModel,
    ContractDocumentation,
    SchemaExample,
    SchemaExportSpecification,
)
from ...docs.reference_docs import (
    ReferenceDocumentation,
    ReferenceMarkdown,
    ReferenceSection,
)
from ...docs.schema_examples import catalog_example_document
from ..enums import (
    SnapshotRequirement,
    CandidateSelectionMode,
    IndexBehavior,
    LinkCheckMode,
    LineHeadSelectionMode,
    PublicationState,
    ReleaseSelectionMode,
    RouteMode,
    TrustClass,
)
from ..scalars import (
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
    RepoRelativePath,
    Slug,
    SourceKey,
    UrlString,
    VersionString,
)
from ..validation.extensions import serialize_extensions_object

_ALLOWED_REDIRECT_STATUS_CODES = frozenset({301, 302, 307, 308})
_WITHDRAWN_PUBLICATION_STATES = frozenset(
    {PublicationState.WITHDRAWN, PublicationState.TOMBSTONED}
)
_MAX_MOUNT_METADATA_BYTES = 16 * 1024


def _ensure_unique_strings(values: list[str], *, type_name: str) -> None:
    seen_values: set[str] = set()
    for value in values:
        if value in seen_values:
            raise ValueError(f"Duplicate {type_name} {value!r}")
        seen_values.add(value)


class CatalogDefaults(SitePipelineBaseModel):
    """Shared defaults applied before per-component overrides."""

    metadata_file: RepoRelativePath | None = Field(
        default=None,
        description="Default location of `site/component.yaml` within each source tree.",
    )
    pages_root: RepoRelativePath | None = Field(
        default=None,
        description="Default repository-relative root for non-versioned component pages.",
    )
    docs_root: RepoRelativePath | None = Field(
        default=None,
        description="Default repository-relative root for component docs content.",
    )
    assets_root: RepoRelativePath | None = Field(
        default=None,
        description="Default repository-relative root for component static assets.",
    )
    publication: PublicationDefaults | None = Field(
        default=None,
        description="Shared publication defaults inherited by components unless they override them.",
    )
    localization: LocalizationConfig | None = Field(
        default=None,
        description="Shared localization defaults inherited by components unless they override them.",
    )


class SiteContentConfig(SitePipelineBaseModel):
    """Top-level pages and asset trees that belong to the site as a whole."""

    pages_root: RepoRelativePath | None = Field(
        default=None,
        description="Repository-relative root for consumer-owned top-level site pages.",
    )
    assets_root: RepoRelativePath | None = Field(
        default=None,
        description="Repository-relative root for consumer-owned top-level static assets.",
    )
    vendor_assets: list[TopLevelAssetConfig] | None = Field(
        default=None,
        description="Additional imported asset trees mounted into the top-level site assets area.",
    )


class LinkCheckConfig(SitePipelineBaseModel):
    """Site-wide policy for internal page-link validation during ``check``."""

    enabled: bool = Field(
        default=True,
        description="Whether the pipeline should validate authored internal page links against resolved public routes.",
    )
    mode: LinkCheckMode = Field(
        default=LinkCheckMode.DIRECTORY,
        description="How authored relative page links should resolve in the published site.",
    )
    check_root_absolute: bool = Field(
        default=False,
        description="Whether root-absolute links such as `/components/foo/` should also be validated when they match declared internal prefixes.",
    )
    internal_prefixes: list[PublicPath] | None = Field(
        default=None,
        description="Root-absolute public-path prefixes that should be treated as internal links when root-absolute checking is enabled.",
        examples=[["/components/", "/docs/"]],
    )

    @model_validator(mode="after")
    def ensure_root_absolute_policy_is_explicit(self) -> Self:
        if self.internal_prefixes is not None:
            _ensure_unique_strings(
                self.internal_prefixes, type_name="link-check internal prefix"
            )
        if self.enabled and self.check_root_absolute and not self.internal_prefixes:
            raise ValueError(
                "linkChecks.internalPrefixes must be set when checkRootAbsolute is enabled"
            )
        return self


class ValidationConfig(SitePipelineBaseModel):
    """Optional site-wide validation policies that affect ``check`` behavior."""

    link_checks: LinkCheckConfig | None = Field(
        default=None,
        description="Optional internal page-link checking policy resolved against staged public routes.",
    )


class TopLevelAssetConfig(SitePipelineBaseModel):
    """Imported asset tree mounted into the shared site asset space."""

    source: RepoRelativePath = Field(
        description="Repository-relative source directory that should be copied or mounted into the published site assets.",
        examples=["vendor/brand"],
    )
    mount_path: PublicPath | None = Field(
        default=None,
        description="Public path below the site asset space where this imported tree should appear.",
        examples=["/assets/vendor/brand/"],
    )
    kind: NonEmptyString | None = Field(
        default=None,
        description="Short renderer-facing kind label that distinguishes this asset tree from other mounted assets.",
        examples=["brandAssets"],
    )
    ownership: NonEmptyString | None = Field(
        default=None,
        description="Logical owner label used by tooling to explain where this imported asset tree came from.",
        examples=["site-branding"],
    )


class PublicationDefaults(SitePipelineBaseModel):
    """Default routing segments used to derive publication paths."""

    origin: OriginKey | None = Field(
        default=None,
        description="Default publication origin used for component routes when no nearer override is present.",
    )
    development_segment: NonEmptyString | None = Field(
        default=None,
        description="Default path segment appended below the component root for moving development docs.",
    )
    docs_segment: NonEmptyString | None = Field(
        default=None,
        description="Optional extra path segment appended below the development docs root when docs should live under an additional nested path.",
    )
    assets_segment: NonEmptyString | None = Field(
        default=None,
        description="Default path segment appended below the component root for static assets.",
    )


class LocalizationConfig(SitePipelineBaseModel):
    """Locale and translation defaults."""

    default_locale: NonEmptyString | None = Field(
        default=None,
        description="Default locale used when a page does not declare a more specific locale.",
    )
    supported_locales: list[NonEmptyString] | None = Field(
        default=None, description="Supported locale keys for this site or component."
    )
    route_mode: RouteMode | None = Field(
        default=None,
        description="How localized pages should be routed within the published URL space.",
    )
    fallback_locale: NonEmptyString | None = Field(
        default=None,
        description="Fallback locale used when a requested translation is unavailable.",
    )

    @model_validator(mode="after")
    def ensure_locale_membership_and_uniqueness(self) -> Self:
        if self.supported_locales is not None:
            _ensure_unique_strings(self.supported_locales, type_name="supported locale")
            supported_locale_set = set(self.supported_locales)
            if (
                self.default_locale is not None
                and self.default_locale not in supported_locale_set
            ):
                raise ValueError(
                    "defaultLocale must be present in supportedLocales when both are set"
                )
            if (
                self.fallback_locale is not None
                and self.fallback_locale not in supported_locale_set
            ):
                raise ValueError(
                    "fallbackLocale must be present in supportedLocales when both are set"
                )
        return self


class OriginConfig(SitePipelineBaseModel):
    """Named public base URL that published routes can resolve against."""

    base_url: UrlString = Field(
        description="Base public URL for this publication origin."
    )
    canonical: bool | None = Field(
        default=None,
        description="Whether this origin should be treated as canonical when multiple origins publish the same target.",
    )
    labels: list[NonEmptyString] | None = Field(
        default=None,
        description="Optional human-readable labels for renderer or deployment tooling.",
    )


class SourceConfig(SitePipelineBaseModel):
    """Named repository or checkout binding reused by components and artifacts."""

    local_dir: RepoRelativePath = Field(
        description="Workspace-relative checkout or source directory."
    )
    repository: UrlString | None = Field(
        default=None,
        description="Optional remote repository URL whose repository root corresponds to this source root.",
    )
    default_branch: RefString | None = Field(
        default=None, description="Optional default branch or ref for this source."
    )
    metadata_file: RepoRelativePath | None = Field(
        default=None,
        description="Optional override for the component metadata file inside this source tree.",
    )


class GroupConfig(SitePipelineBaseModel):
    """Reusable defaults and grouping hints shared by several components."""

    display_name: NonEmptyString | None = Field(
        default=None,
        description="Human-readable group name for renderers or generated navigation.",
    )
    path_prefix: PublicPath | None = Field(
        default=None,
        description="Shared public path prefix applied to grouped component publication roots.",
    )
    navigation_section: NonEmptyString | None = Field(
        default=None,
        description="Optional renderer-facing grouping label for navigation or listings.",
    )
    weight: int | None = Field(
        default=None,
        strict=True,
        description="Optional ordering hint shared by components in this group.",
    )
    publication: PublicationConfig | None = Field(
        default=None,
        description="Publication defaults inherited by grouped components unless they override them.",
    )


class ComponentContentSelection(SitePipelineBaseModel):
    """Source selection for a component's shared pages, docs, and assets."""

    source: SourceKey | None = Field(
        default=None,
        description="Named source that owns shared component pages, docs, and assets roots.",
    )


class RouteAliasConfig(SitePipelineBaseModel):
    """Additional public route that resolves to the same published destination."""

    path: PublicPath = Field(
        description="Alternate public path that should resolve to the same page family or landing target as the primary route.",
        examples=["/spark/stable/"],
    )
    origin: OriginKey | None = Field(
        default=None,
        description="Optional origin override when the alias should only exist on one named publication origin.",
        examples=["archive"],
    )
    label: NonEmptyString | None = Field(
        default=None,
        description="Human-readable label that renderers can use when presenting this alias in navigation or metadata.",
        examples=["stable"],
    )


class RedirectRuleConfig(SitePipelineBaseModel):
    """Redirect rule that sends one published path to another internal or external target."""

    from_path: PublicPath = Field(
        description="Public path that should redirect instead of serving its own content.",
        examples=["/spark/docs/current/"],
    )
    from_origin: OriginKey | None = Field(
        default=None,
        description="Optional origin override when the redirect should only exist on one named publication origin.",
        examples=["archive"],
    )
    target: ReferenceString | UrlString = Field(
        description="Destination of the redirect, either as a typed internal reference string or as a fully qualified external URL.",
        examples=["route:/spark/development/"],
    )
    status: int | None = Field(
        default=None,
        strict=True,
        description="HTTP redirect status to emit; when omitted, downstream tooling applies its default redirect status.",
        examples=[308],
    )
    reason: NonEmptyString | None = Field(
        default=None,
        description="Short explanation of why the redirect exists, for example to describe a rename, consolidation, or withdrawn release route.",
        examples=["Development docs moved to the new route."],
    )

    @model_validator(mode="after")
    def ensure_redirect_status_is_allowed(self) -> Self:
        if (
            self.status is not None
            and self.status not in _ALLOWED_REDIRECT_STATUS_CODES
        ):
            raise ValueError("Redirect status must be one of 301, 302, 307, or 308")
        return self


class PublicationConfig(SitePipelineBaseModel):
    """Resolved-or-authored route layout choices for a component or artifact."""

    origin: OriginKey | None = Field(
        default=None,
        description="Publication origin key to use for this component or artifact.",
    )
    path_segment: NonEmptyString | None = Field(
        default=None,
        description="Path segment appended below an inherited path prefix or mount root.",
    )
    mount_path: PublicPath | None = Field(
        default=None,
        description="Explicit public root path for the component's published content.",
        examples=["/spark/"],
    )
    component_path: PublicPath | None = Field(
        default=None,
        description="Explicit public path for the component landing page or overview root.",
    )
    development_path: PublicPath | None = Field(
        default=None,
        description="Explicit public path for the moving development docs surface.",
    )
    docs_path: PublicPath | None = Field(
        default=None,
        description="Explicit public docs landing path exposed to downstream consumers; defaults to the development path unless an additional docs segment or override is configured.",
    )
    assets_path: PublicPath | None = Field(
        default=None,
        description="Explicit public path for static assets below the component root.",
    )
    canonical_path: PublicPath | None = Field(
        default=None,
        description="Optional canonical public path used when aliases or multiple origins are present.",
    )
    aliases: list[RouteAliasConfig] | None = Field(
        default=None,
        description="Additional public aliases that should resolve to the same published target.",
    )
    redirects: list[RedirectRuleConfig] | None = Field(
        default=None, description="Redirect rules to emit for legacy or moved routes."
    )


class LineHeadSelectionPolicy(SitePipelineBaseModel):
    """Rule for which release-line head refs should appear as publishable contexts."""

    mode: LineHeadSelectionMode = Field(
        description="Selection strategy for release-line head contexts, such as taking all lines or only an explicit subset.",
    )
    keys: list[NonEmptyString] | None = Field(
        default=None,
        description="Explicit release-line keys to publish when `mode` is `explicit`.",
        examples=[["3.5", "4.0"]],
    )

    @model_validator(mode="after")
    def ensure_explicit_keys_match_mode(self) -> Self:
        if self.mode is LineHeadSelectionMode.EXPLICIT:
            if not self.keys:
                raise ValueError(
                    "Line-head selection mode explicit requires non-empty keys"
                )
        elif self.keys is not None:
            raise ValueError(
                "Line-head selection keys are only allowed when mode is explicit"
            )
        return self


class ReleaseSelectionPolicy(SitePipelineBaseModel):
    """Rule for which exact released versions should become published contexts."""

    mode: ReleaseSelectionMode = Field(
        description="Selection strategy for released versions: `none` disables releases; other modes select the latest per line, latest `n`, all known, or explicit versions.",
    )
    count: PositiveInteger | None = Field(
        default=None,
        description="How many most-recent releases to include when `mode` is `latestN`.",
        examples=[3],
    )
    versions: list[VersionString] | None = Field(
        default=None,
        description="Exact released versions to include when `mode` is `explicit`.",
        examples=[["4.0.0", "4.0.1"]],
    )

    @model_validator(mode="after")
    def ensure_mode_specific_fields(self) -> Self:
        if self.mode is ReleaseSelectionMode.LATEST_N:
            if self.count is None:
                raise ValueError("Release selection mode latestN requires count")
            if self.versions is not None:
                raise ValueError(
                    "Release selection versions are only allowed for explicit mode"
                )
            return self

        if self.mode is ReleaseSelectionMode.EXPLICIT:
            if not self.versions:
                raise ValueError("Release selection mode explicit requires versions")
            if self.count is not None:
                raise ValueError(
                    "Release selection count is only allowed for latestN mode"
                )
            return self

        if self.count is not None:
            raise ValueError("Release selection count is only allowed for latestN mode")
        if self.versions is not None:
            raise ValueError(
                "Release selection versions are only allowed for explicit mode"
            )
        return self


class CandidateSelectionPolicy(SitePipelineBaseModel):
    """Rule for which release candidates should become published contexts."""

    mode: CandidateSelectionMode = Field(
        description="Selection strategy for candidate releases, such as disabling them or selecting an explicit set.",
    )
    versions: list[VersionString] | None = Field(
        default=None,
        description="Candidate version strings to include when `mode` is `explicit` and provider versions are available.",
        examples=[["4.1.0-rc1"]],
    )
    external_ids: list[NonEmptyString] | None = Field(
        default=None,
        description="Provider-specific candidate identifiers to include when version strings alone are not enough to identify the desired candidate records.",
        examples=[["github:runtime-4.1.0-rc1"]],
    )

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
    """Version-context selection inherited field by field from built-ins to component to artifact catalog policy.

    Omitted/null fields inherit. Nested mode objects and named-ref lists replace
    atomically; an empty policy inherits all fields.
    """

    development: bool | None = Field(
        default=None,
        description="Whether to publish the moving development context represented by the artifact's `developmentRef`. Omitted/null inherits; false disables only development.",
    )
    line_heads: LineHeadSelectionPolicy | None = Field(
        default=None,
        description="Rule for including release-line head contexts such as `4.0` or `3.5`. Omitted/null inherits; a supplied mode object replaces the inherited rule; mode none disables line heads.",
    )
    releases: ReleaseSelectionPolicy | None = Field(
        default=None,
        description="Rule for including exact released-version contexts such as `4.0.1`. Omitted/null inherits; a supplied mode object replaces the inherited rule; mode none disables releases.",
    )
    named_refs: list[Identifier] | None = Field(
        default=None,
        description="Named ref keys to publish. Omitted/null inherits; a supplied list replaces the inherited list; an empty list disables named refs.",
        examples=[["preview", "stable"]],
    )
    candidates: CandidateSelectionPolicy | None = Field(
        default=None,
        description="Rule for including release-candidate contexts. Omitted/null inherits; a supplied mode object replaces the inherited rule; mode none disables candidates.",
    )

    @model_validator(mode="after")
    def ensure_named_refs_are_unique(self) -> Self:
        if self.named_refs is not None:
            _ensure_unique_strings(
                self.named_refs, type_name="publication selected namedRef"
            )
        return self


class MountConfig(SitePipelineBaseModel):
    """Mounted subtree, such as generated API docs or imported assets, published below one public path."""

    source: MountSourceRef = Field(
        description="Typed source reference that identifies the generated or imported subtree to mount.",
        examples=["generated/api"],
    )
    mount_path: PublicPath = Field(
        description="Public path where the mounted subtree should appear in the published site.",
        examples=["/spark/api/"],
    )
    kind: NonEmptyString = Field(
        description="Short kind label that tells renderers and tooling what sort of mounted content this is.",
        examples=["generatedApi"],
    )
    trust_class: TrustClass = Field(
        description="Trust level for the mounted content, used by downstream tooling to decide how much confidence to place in its structure or metadata.",
    )
    version_scope: NonEmptyString | None = Field(
        default=None,
        description="Optional label describing which version context this mount belongs to, when the same component can expose several mounted trees.",
        examples=["release"],
    )
    index_behavior: IndexBehavior | None = Field(
        default=None,
        description="How the mounted subtree should participate in generated indexes, listings, or navigation structures.",
    )
    ownership: NonEmptyString | None = Field(
        default=None,
        description="Logical owner label used in staged metadata to explain who is responsible for this mounted subtree.",
        examples=["runtime-docs"],
    )
    metadata: ExtensionsObject | None = Field(
        default=None,
        description="Small JSON-like extension object for extra mount metadata that downstream tooling may consume.",
    )

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


class CompatibilityAssertionConfig(SitePipelineBaseModel):
    """Compatibility statement between two published identities, such as an artifact and a supported platform."""

    subject_ref: ReferenceString = Field(
        description="Typed internal reference string for the thing whose compatibility is being described.",
        examples=["artifact:spark/runtime"],
    )
    target_ref: ReferenceString = Field(
        description="Typed internal reference string for the thing that the subject is compatible with or constrained by.",
        examples=["artifact:spark/operator"],
    )
    relation: NonEmptyString = Field(
        description="Relationship label that names the compatibility statement, such as `testedWith`, `requires`, or `incompatibleWith`.",
        examples=["testedWith"],
    )
    scope: NonEmptyString | None = Field(
        default=None,
        description="Optional scope label that narrows the compatibility statement to one subsystem, API surface, or deployment mode.",
        examples=["kubernetes"],
    )
    confidence: NonEmptyString | None = Field(
        default=None,
        description="Optional confidence label that tells readers how strong or direct the supporting evidence is.",
        examples=["verified"],
    )
    notes: NonEmptyString | None = Field(
        default=None,
        description="Additional human-readable explanation, caveats, or migration advice for the compatibility statement.",
    )


class ArtifactConfig(SitePipelineBaseModel):
    """One independently versioned release unit inside a component."""

    key: ArtifactKey = Field(
        description="Stable artifact identifier used in typed references, staged metadata, and provider records.",
        examples=["runtime"],
    )
    source: SourceKey | None = Field(
        default=None,
        description="Optional source binding override; otherwise inherit the component content source.",
    )
    docs_root: RepoRelativePath | None = Field(
        default=None, description="Optional source layout binding for artifact docs."
    )
    assets_root: RepoRelativePath | None = Field(
        default=None, description="Optional source layout binding for artifact assets."
    )
    publication_selection: PublicationSelectionPolicy | None = Field(
        default=None,
        description="Optional consumer publication selection for this component-defined artifact. Non-null fields override component policy; omitted/null fields and an empty policy inherit.",
    )
    compatibility: list[CompatibilityAssertionConfig] | None = Field(
        default=None,
        description="Compatibility statements that should be emitted for this artifact in staged metadata.",
    )
    mounts: list[MountConfig] | None = Field(
        default=None,
        description="Mounted generated or imported subtrees that belong to this artifact's published surface.",
    )


class ComponentProviderSnapshot(SitePipelineBaseModel):
    """Source-relative component provider inventory binding."""

    source: SourceKey = Field(description="Named catalog source containing this component's inventory.")
    path: RepoRelativePath = Field(description="Snapshot file path relative to the named source root.")
    requirement: SnapshotRequirement = Field(default=SnapshotRequirement.PUBLICATION, description="Required for publication by default, always required, or always optional.")


class ComponentCatalogEntry(SitePipelineBaseModel):
    """Component entry in the consumer catalog."""

    provider_snapshot: ComponentProviderSnapshot | None = Field(default=None, description="Optional binding to a component-owned normalized provider inventory.")
    slug: Slug = Field(description="Stable component identifier.")
    display_name: NonEmptyString | None = Field(
        default=None,
        description="Human-readable component name override or convenience value.",
    )
    local_dir: RepoRelativePath | None = Field(
        default=None,
        description="Simple shorthand for binding the component to one workspace-local checkout directory.",
    )
    weight: int | None = Field(
        default=None,
        strict=True,
        description="Optional ordering hint for component listings, menus, and other consumer-rendered component collections.",
    )
    group: Identifier | None = Field(
        default=None,
        description="Optional group key for inherited defaults and renderer grouping.",
    )
    content: ComponentContentSelection | None = Field(
        default=None,
        description="Shared content-source selection for component pages, docs, and assets.",
    )
    publication: PublicationConfig | None = Field(
        default=None,
        description="Explicit publication configuration for this component.",
    )
    publication_selection: PublicationSelectionPolicy | None = Field(
        default=None,
        description="Version-context selection layered over built-in values and inherited by contained artifacts field by field. Omitted/null fields and an empty policy inherit.",
    )
    localization: LocalizationConfig | None = Field(
        default=None, description="Component-specific localization overrides."
    )
    compatibility: list[CompatibilityAssertionConfig] | None = Field(
        default=None,
        description="Component-level compatibility assertions emitted into staged metadata.",
    )
    mounts: list[MountConfig] | None = Field(
        default=None,
        description="Component-level generated or imported documentation mounts.",
    )
    artifacts: list[ArtifactConfig] | None = Field(
        default=None,
        description="Independently versioned artifacts belonging to this component.",
    )

    @model_validator(mode="after")
    def ensure_artifact_keys_are_unique(self) -> Self:
        if self.artifacts is None:
            return self
        _ensure_unique_strings(
            [artifact.key for artifact in self.artifacts], type_name="artifact key"
        )
        return self


class SiteCatalogDocumentV1(SitePipelineBaseModel):
    """Consumer-authored site catalog from ``site/catalog.yaml``."""

    contract_documentation: ClassVar[ContractDocumentation] = ContractDocumentation(
        category="authored",
        ownership="consumer-owned",
        summary="Catalog of components, defaults, sources, origins, and publication rules for one site.",
        file_path="site/catalog.yaml",
        reference=ReferenceDocumentation(
            summary=ReferenceMarkdown(
                "Canonical site catalog that lists participating components, shared defaults, source bindings, publication origins, and publication policy for one site."
            ),
            sections=(
                ReferenceSection(
                    title="Inheritance",
                    body=ReferenceMarkdown(
                        "Defaults flow from `defaults` to `groups` to individual component entries. See [component entries](type:SiteCatalogDocumentV1#components)."
                    ),
                ),
            ),
        ),
    )
    schema_export: ClassVar[SchemaExportSpecification] = SchemaExportSpecification(
        filename="catalog-v1.schema.json",
        title="Site Pipeline Catalog v1",
        examples=(
            SchemaExample(
                summary="Catalog with a single component, a single artifact, and release selection policy.",
                value_builder=catalog_example_document,
                render_format="yaml",
            ),
        ),
    )

    schema_version: Literal[1] = Field(
        description="Schema version for the catalog format."
    )
    defaults: CatalogDefaults | None = Field(
        default=None,
        description="Shared default settings applied before per-component overrides.",
    )
    site: SiteContentConfig | None = Field(
        default=None,
        description="Consumer-owned top-level site pages, assets, and vendor-asset declarations.",
    )
    origins: dict[OriginKey, OriginConfig] | None = Field(
        default=None,
        description="Named publication origins that components can target.",
    )
    sources: dict[SourceKey, SourceConfig] | None = Field(
        default=None,
        description="Named repository or checkout bindings used by components and artifacts.",
    )
    groups: dict[Identifier, GroupConfig] | None = Field(
        default=None,
        description="Optional grouping defaults shared by multiple components.",
    )
    validation: ValidationConfig | None = Field(
        default=None,
        description="Optional site-wide validation policies that extend the default `check` behavior.",
    )
    components: list[ComponentCatalogEntry] = Field(
        description="Participating components in this consumer-authored catalog."
    )

    @model_validator(mode="after")
    def ensure_document_cross_references(self) -> Self:
        _ensure_unique_strings(
            [component.slug for component in self.components],
            type_name="component slug",
        )

        origin_keys = set(self.origins or {})
        source_keys = set(self.sources or {})
        group_keys = set(self.groups or {})

        def validate_origin_reference(
            origin: OriginKey | None, *, location: str
        ) -> None:
            if origin is None:
                return
            if origin not in origin_keys:
                raise ValueError(
                    f"Unknown origin key {origin!r} referenced by {location}"
                )

        def validate_publication_origins(
            publication: PublicationConfig | None, *, location: str
        ) -> None:
            if publication is None:
                return
            validate_origin_reference(publication.origin, location=f"{location}.origin")
            if publication.aliases is not None:
                for index, alias in enumerate(publication.aliases):
                    validate_origin_reference(
                        alias.origin, location=f"{location}.aliases[{index}].origin"
                    )
            if publication.redirects is not None:
                for index, redirect in enumerate(publication.redirects):
                    validate_origin_reference(
                        redirect.from_origin,
                        location=f"{location}.redirects[{index}].fromOrigin",
                    )

        if self.defaults is not None:
            validate_origin_reference(
                self.defaults.publication.origin
                if self.defaults.publication is not None
                else None,
                location="defaults.publication.origin",
            )

        if self.groups is not None:
            for group_key, group in self.groups.items():
                validate_publication_origins(
                    group.publication, location=f"groups[{group_key!r}].publication"
                )

        for component in self.components:
            if (
                component.provider_snapshot is not None
                and component.provider_snapshot.source not in source_keys
            ):
                raise ValueError(
                    f"Unknown snapshot source {component.provider_snapshot.source!r} for component {component.slug!r}"
                )
            if component.group is not None and component.group not in group_keys:
                raise ValueError(
                    f"Unknown group key {component.group!r} referenced by component {component.slug!r}"
                )

            if (
                component.content is not None
                and component.content.source is not None
                and component.content.source not in source_keys
            ):
                raise ValueError(
                    f"Unknown source key {component.content.source!r} referenced by component {component.slug!r}",
                )

            validate_publication_origins(
                component.publication,
                location=f"component {component.slug!r}.publication",
            )

            if component.artifacts is None:
                continue

            for artifact in component.artifacts:
                if artifact.source is not None and artifact.source not in source_keys:
                    raise ValueError(
                        f"Unknown source key {artifact.source!r} referenced by artifact {artifact.key!r}",
                    )

        return self
