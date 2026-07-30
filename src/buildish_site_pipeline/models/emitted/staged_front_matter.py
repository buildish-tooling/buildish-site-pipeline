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

"""Staged front matter models."""

from __future__ import annotations

from typing import ClassVar, Self

from pydantic import Field, model_validator

from ...docs.documentation import (
    ContractDocumentation,
    PipelineDerivedModel as SitePipelineBaseModel,
    SchemaExample,
    SchemaExportSpecification,
)
from ...docs.schema_examples import front_matter_namespace_example_document
from ..enums import PublicationState, RecordKind
from ..scalars import (
    ArtifactKey,
    HostnameString,
    NonEmptyString,
    OriginKey,
    ProviderKey,
    PublicPath,
    RefString,
    Slug,
    UrlString,
    VersionString,
)
from ..validation.urls import extract_hostname_from_url
from ..authored.site_catalog import SupportWindow


def _ensure_unique_strings(values: list[str], *, type_name: str) -> None:
    seen_values: set[str] = set()
    for value in values:
        if value in seen_values:
            raise ValueError(f"Duplicate {type_name} {value!r}")
        seen_values.add(value)


class ResolvedOrigin(SitePipelineBaseModel):
    """Resolved origin details for the current publication target."""

    key: OriginKey = Field(
        description="Origin key selected for this published route or page.",
        examples=["archive"],
    )
    base_url: UrlString = Field(
        description="Fully qualified base URL for the selected origin.",
        examples=["https://archive.apache.org/dist/spark"],
    )
    hostname: HostnameString = Field(
        description="Hostname extracted from `baseUrl` for callers that need it without reparsing the URL.",
        examples=["archive.apache.org"],
    )

    @model_validator(mode="after")
    def ensure_hostname_matches_base_url(self) -> Self:
        if self.hostname.lower() != extract_hostname_from_url(self.base_url).lower():
            raise ValueError(
                "ResolvedOrigin.hostname must match the hostname extracted from baseUrl"
            )
        return self


class ResolvedPathSet(SitePipelineBaseModel):
    """Resolved public path roots for a component."""

    component: PublicPath = Field(
        description="Public root path for the component as a whole.",
        examples=["/spark/"],
    )
    development: PublicPath = Field(
        description="Public root path for development-version content.",
        examples=["/spark/main/"],
    )
    docs: PublicPath = Field(
        description="Public root path for versioned documentation content.",
        examples=["/spark/docs/"],
    )
    assets: PublicPath = Field(
        description="Public root path for shared component assets.",
        examples=["/spark/assets/"],
    )


class ResolvedUrlSet(SitePipelineBaseModel):
    """Resolved absolute URLs for a component."""

    component: UrlString = Field(
        description="Absolute URL for the component root.",
        examples=["https://archive.apache.org/dist/spark/"],
    )
    development: UrlString = Field(
        description="Absolute URL for the development-version root.",
        examples=["https://archive.apache.org/dist/spark/main/"],
    )
    docs: UrlString = Field(
        description="Absolute URL for the versioned docs root.",
        examples=["https://archive.apache.org/dist/spark/docs/"],
    )
    assets: UrlString = Field(
        description="Absolute URL for the shared component asset root.",
        examples=["https://archive.apache.org/dist/spark/assets/"],
    )


class ResolvedPublication(SitePipelineBaseModel):
    """Resolved origin, path roots, and absolute URLs for a component."""

    origin: ResolvedOrigin = Field(
        description="Origin details used to resolve paths into absolute URLs."
    )
    paths: ResolvedPathSet = Field(
        description="Resolved public path roots for the component."
    )
    urls: ResolvedUrlSet = Field(
        description="Resolved absolute URLs for the same publication roots."
    )


class ReleaseLineSummary(SitePipelineBaseModel):
    """Small release-line summary embedded into page or component front matter."""

    key: NonEmptyString = Field(
        description="Release-line key, such as `4.0`, for the summarized line.",
        examples=["4.0"],
    )
    parent: NonEmptyString | None = Field(
        default=None,
        description="Optional parent release-line key when lineage should be preserved in front matter.",
        examples=["4.x"],
    )
    latest: VersionString | None = Field(
        default=None,
        description="Latest released version currently associated with this line.",
        examples=["4.0.1"],
    )
    support_status: NonEmptyString | None = Field(
        default=None,
        description="Support-status key or label for the release line.",
        examples=["supported"],
    )
    head_ref: RefString | None = Field(
        default=None,
        description="Maintenance or line-head ref associated with this release line, if known.",
        examples=["refs/heads/release-4.0"],
    )
    aliases: list[NonEmptyString] | None = Field(
        default=None,
        description="Alternate labels that should also refer to this release line.",
        examples=[["stable"]],
    )
    support_window: SupportWindow | None = Field(
        default=None,
        description="Lifecycle dates and support notes for the release line."
    )

    @model_validator(mode="after")
    def ensure_aliases_are_unique(self) -> Self:
        if self.aliases is not None:
            _ensure_unique_strings(self.aliases, type_name="release-line alias")
        return self


class ArtifactFrontMatterSummary(SitePipelineBaseModel):
    """Small artifact summary embedded in component front matter."""

    key: ArtifactKey = Field(
        description="Artifact key used to identify the artifact in page links and typed references.",
        examples=["runtime"],
    )
    display_name: NonEmptyString | None = Field(
        default=None,
        description="Human-readable artifact label shown in page chrome or listings.",
        examples=["Runtime"],
    )
    latest_stable: VersionString | None = Field(
        default=None,
        description="Most recent stable version that readers should treat as the default recommendation.",
        examples=["4.0.1"],
    )
    release_lines: list[ReleaseLineSummary] | None = Field(
        default=None,
        description="Compact release-line summaries that the page can use for navigation or version selection."
    )


class ReleaseLineContext(SitePipelineBaseModel):
    """Release-line context attached to one staged page's current version."""

    key: NonEmptyString = Field(
        description="Release-line key for this page's version context.",
        examples=["4.0"],
    )
    support_status: NonEmptyString | None = Field(
        default=None,
        description="Support-status key or label associated with the current release line.",
        examples=["supported"],
    )
    ancestors: list[NonEmptyString] | None = Field(
        default=None,
        description="Ancestor release-line keys ordered from nearest to farthest.",
        examples=[["4.x", "stable"]],
    )
    support_window: SupportWindow | None = Field(
        default=None,
        description="Lifecycle dates and support notes attached to the current release line."
    )

    @model_validator(mode="after")
    def ensure_ancestor_keys_are_unique(self) -> Self:
        if self.ancestors is not None:
            _ensure_unique_strings(self.ancestors, type_name="release-line ancestor")
        return self


class VersionContext(SitePipelineBaseModel):
    """Version, release-candidate, or ref context attached to one staged page."""

    kind: RecordKind = Field(
        description="Kind of version context attached to the page, such as release, candidate, development ref, or named ref."
    )
    label: NonEmptyString = Field(
        description="Primary label shown to readers for this version context.",
        examples=["4.0.0"],
    )
    path: PublicPath | None = Field(
        default=None,
        description="Public route root for this version context when it has a routable landing path.",
        examples=["/spark/4.0.0/"],
    )
    url: UrlString | None = Field(
        default=None,
        description="Absolute URL for the version-context route root when it has one.",
    )
    docs_path: PublicPath | None = Field(
        default=None,
        description="Public docs root for this version context when versioned docs are available.",
        examples=["/spark/4.0.0/docs/"],
    )
    docs_url: UrlString | None = Field(
        default=None,
        description="Absolute URL for the version-context docs root when it has one."
    )
    tag: NonEmptyString | None = Field(
        default=None,
        description="Exact tag name associated with this version context, if present.",
        examples=["v4.0.0"],
    )
    ref: RefString | None = Field(
        default=None,
        description="Exact source-control ref associated with this version context, if present.",
        examples=["refs/heads/main"],
    )
    named_ref_key: NonEmptyString | None = Field(
        default=None,
        description="Catalog-authored named-ref key when this context represents a named ref.",
        examples=["preview"],
    )
    publication_state: PublicationState | None = Field(
        default=None,
        description="Publication-state label for this version context, such as published or withdrawn."
    )
    maturity: NonEmptyString | None = Field(
        default=None,
        description="Maturity label such as preview, beta, or stable.",
        examples=["stable"],
    )
    candidate_sequence: int | None = Field(
        default=None,
        strict=True,
        ge=1,
        description="Release-candidate sequence number when this version context represents a candidate release.",
        examples=[1],
    )
    vote_status: NonEmptyString | None = Field(
        default=None,
        description="Vote status label for release-candidate contexts when it is known.",
        examples=["passed"],
    )
    release_line: ReleaseLineContext | None = Field(
        default=None,
        description="Release-line context attached to the current version when the version belongs to a known release line."
    )
    support_window: SupportWindow | None = Field(
        default=None,
        description="Lifecycle dates and support notes attached directly to this version context."
    )

    @model_validator(mode="after")
    def ensure_path_and_url_pairs_stay_in_sync(self) -> Self:
        if (self.path is None) != (self.url is None):
            raise ValueError(
                "VersionContext path and url must either both be present or both be absent"
            )
        if (self.docs_path is None) != (self.docs_url is None):
            raise ValueError(
                "VersionContext docsPath and docsUrl must either both be present or both be absent",
            )
        return self


class TranslationLinkSummary(SitePipelineBaseModel):
    """Compact link to one translated sibling page."""

    locale: NonEmptyString = Field(
        description="Locale key for the translated sibling page.",
        examples=["de"],
    )
    path: PublicPath | None = Field(
        default=None,
        description="Public path for the translated sibling page, if available.",
        examples=["/de/spark/overview/"],
    )
    url: UrlString = Field(
        description="Absolute URL for the translated sibling page.",
    )
    title: NonEmptyString | None = Field(
        default=None,
        description="Localized page title for the translated sibling page.",
        examples=["Übersicht"],
    )


class ProviderProvenance(SitePipelineBaseModel):
    """Small pointer back to the provider record that informed this page's version."""

    key: ProviderKey = Field(
        description="Provider key for the upstream system that supplied the current version metadata.",
        examples=["github-releases"],
    )
    external_id: NonEmptyString | None = Field(
        default=None,
        description="Provider-specific stable identifier for the upstream record that informed this page.",
        examples=["github:release:runtime-4.0.0"],
    )
    external_url: UrlString | None = Field(
        default=None,
        description="Human-browsable URL for the upstream record that informed this page."
    )


class PipelinePageFrontMatter(SitePipelineBaseModel):
    """Page-local pipeline metadata injected into staged page front matter."""

    kind: NonEmptyString = Field(
        description="Short page kind label used by renderers to distinguish landing pages, docs pages, release notes, and similar page families.",
        examples=["docsPage"],
    )
    section: NonEmptyString | None = Field(
        default=None,
        description="Optional higher-level section label that groups the page with related navigation or templates.",
        examples=["documentation"],
    )
    artifact_key: ArtifactKey | None = Field(
        default=None,
        description="Artifact key when the page belongs to one independently versioned artifact.",
        examples=["runtime"],
    )
    path: PublicPath = Field(
        description="Published public path for this page.",
        examples=["/spark/4.0.0/docs/getting-started/"],
    )
    url: UrlString = Field(
        description="Canonical absolute URL for this page."
    )
    canonical_url: UrlString | None = Field(
        default=None,
        description="Explicit canonical URL when it should differ from `url`, for example to consolidate duplicate routes."
    )
    alternate_urls: list[UrlString] | None = Field(
        default=None,
        description="Additional absolute URLs that should be considered alternate entry points for the same page.",
    )
    locale: NonEmptyString | None = Field(
        default=None,
        description="Locale key for this page when it participates in localization.",
        examples=["en"],
    )
    default_locale: bool | None = Field(
        default=None,
        description="Whether this page represents the default locale within its translation group."
    )
    translation_key: NonEmptyString | None = Field(
        default=None,
        description="Shared key that ties translated sibling pages together across locales.",
        examples=["spark-overview"],
    )
    derived_title: NonEmptyString | None = Field(
        default=None,
        description="Body-derived page title inferred from authored content when the pipeline can detect one.",
        examples=["Getting Started"],
    )
    derived_description: NonEmptyString | None = Field(
        default=None,
        description="Body-derived page description inferred from authored content when the pipeline can detect one.",
        examples=["Install the package and run the quickstart."],
    )
    translations: list[TranslationLinkSummary] | None = Field(
        default=None,
        description="Compact links to translated sibling pages in other locales."
    )
    component_path: PublicPath = Field(
        description="Public root path for the owning component.",
        examples=["/spark/"],
    )
    component_url: UrlString = Field(
        description="Absolute URL for the owning component root."
    )
    version: VersionContext | None = Field(
        default=None,
        description="Version or ref context attached when this page belongs to a versioned route set."
    )
    provider: ProviderProvenance | None = Field(
        default=None,
        description="Pointer back to the upstream provider record that informed the page's version metadata."
    )

    @model_validator(mode="after")
    def ensure_alternates_and_translations_are_unique(self) -> Self:
        if self.alternate_urls is not None:
            _ensure_unique_strings(self.alternate_urls, type_name="alternate URL")
        if self.translations is not None:
            _ensure_unique_strings(
                [translation.locale for translation in self.translations],
                type_name="translation locale",
            )
        return self


class PipelineComponentFrontMatter(SitePipelineBaseModel):
    """Component-level pipeline metadata injected into staged page front matter."""

    slug: Slug = Field(
        description="Stable component slug for the owning component.",
        examples=["spark"],
    )
    display_name: NonEmptyString | None = Field(
        default=None,
        description="Human-readable component name shown in page chrome or navigation.",
        examples=["Apache Spark"],
    )
    latest_stable: VersionString | None = Field(
        default=None,
        description="Most recent stable version recommended for the component as a whole when one shared release line is enough.",
        examples=["4.0.1"],
    )
    publication: ResolvedPublication = Field(
        description="Resolved publication roots and URLs for the owning component."
    )
    artifacts: list[ArtifactFrontMatterSummary] | None = Field(
        default=None,
        description="Compact artifact summaries that pages can use for version navigation or page chrome."
    )


class PipelineFrontMatterNamespace(SitePipelineBaseModel):
    """Reserved top-level front matter namespace that the pipeline injects into staged pages."""

    contract_documentation: ClassVar[ContractDocumentation] = ContractDocumentation(
        category="emitted",
        ownership="pipeline-derived",
        summary="Reserved front matter namespace containing pipeline-derived component and page metadata.",
    )
    schema_export: ClassVar[SchemaExportSpecification] = SchemaExportSpecification(
        filename="front-matter-namespace-v1.schema.json",
        title="Site Pipeline Front Matter Namespace v1",
        examples=(
            SchemaExample(
                summary="Injected front matter for a component page and a released version.",
                value_builder=front_matter_namespace_example_document,
                render_format="yaml",
            ),
        ),
    )

    component: PipelineComponentFrontMatter | None = Field(
        default=None,
        description="Component-level pipeline metadata injected into the staged page."
    )
    page: PipelinePageFrontMatter | None = Field(
        default=None,
        description="Page-local pipeline metadata injected into the staged page."
    )
