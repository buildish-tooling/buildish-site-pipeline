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

"""Staged front matter models."""

from __future__ import annotations

from typing import Self

from pydantic import Field, model_validator

from .base import SitePipelineBaseModel
from .catalog import SupportWindow
from .enums import PublicationState, RecordKind
from .scalars import (
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
from .validation.urls import extract_hostname_from_url


def _ensure_unique_strings(values: list[str], *, type_name: str) -> None:
    seen_values: set[str] = set()
    for value in values:
        if value in seen_values:
            raise ValueError(f"Duplicate {type_name} {value!r}")
        seen_values.add(value)


class ResolvedOrigin(SitePipelineBaseModel):
    """Resolved publication origin information."""

    key: OriginKey
    base_url: UrlString
    hostname: HostnameString

    @model_validator(mode="after")
    def ensure_hostname_matches_base_url(self) -> Self:
        if self.hostname.lower() != extract_hostname_from_url(self.base_url).lower():
            raise ValueError(
                "ResolvedOrigin.hostname must match the hostname extracted from baseUrl"
            )
        return self


class ResolvedPathSet(SitePipelineBaseModel):
    """Resolved public paths for one component."""

    component: PublicPath
    development: PublicPath
    docs: PublicPath
    assets: PublicPath


class ResolvedUrlSet(SitePipelineBaseModel):
    """Resolved fully qualified URLs for one component."""

    component: UrlString
    development: UrlString
    docs: UrlString
    assets: UrlString


class ResolvedPublication(SitePipelineBaseModel):
    """Resolved route and URL bundle for one component."""

    origin: ResolvedOrigin
    paths: ResolvedPathSet
    urls: ResolvedUrlSet


class ReleaseLineSummary(SitePipelineBaseModel):
    """Compact release-line summary embedded into front matter."""

    key: NonEmptyString
    parent: NonEmptyString | None = None
    latest: VersionString | None = None
    support_status: NonEmptyString | None = None
    head_ref: RefString | None = None
    aliases: list[NonEmptyString] | None = None
    support_window: SupportWindow | None = None

    @model_validator(mode="after")
    def ensure_aliases_are_unique(self) -> Self:
        if self.aliases is not None:
            _ensure_unique_strings(self.aliases, type_name="release-line alias")
        return self


class ArtifactFrontMatterSummary(SitePipelineBaseModel):
    """Compact artifact summary embedded in component front matter."""

    key: ArtifactKey
    display_name: NonEmptyString | None = None
    latest_stable: VersionString | None = None
    release_lines: list[ReleaseLineSummary] | None = None


class ReleaseLineContext(SitePipelineBaseModel):
    """Page-local release-line context."""

    key: NonEmptyString
    support_status: NonEmptyString | None = None
    ancestors: list[NonEmptyString] | None = None
    support_window: SupportWindow | None = None

    @model_validator(mode="after")
    def ensure_ancestor_keys_are_unique(self) -> Self:
        if self.ancestors is not None:
            _ensure_unique_strings(self.ancestors, type_name="release-line ancestor")
        return self


class VersionContext(SitePipelineBaseModel):
    """Version or ref context attached to one staged page."""

    kind: RecordKind
    label: NonEmptyString
    path: PublicPath | None = None
    url: UrlString | None = None
    docs_path: PublicPath | None = None
    docs_url: UrlString | None = None
    tag: NonEmptyString | None = None
    ref: RefString | None = None
    named_ref_key: NonEmptyString | None = None
    publication_state: PublicationState | None = None
    maturity: NonEmptyString | None = None
    candidate_sequence: int | None = Field(default=None, strict=True, ge=1)
    vote_status: NonEmptyString | None = None
    release_line: ReleaseLineContext | None = None
    support_window: SupportWindow | None = None

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
    """Compact translation sibling reference."""

    locale: NonEmptyString
    path: PublicPath | None = None
    url: UrlString
    title: NonEmptyString | None = None


class ProviderProvenance(SitePipelineBaseModel):
    """Compact provider provenance embedded in page front matter."""

    key: ProviderKey
    external_id: NonEmptyString | None = None
    external_url: UrlString | None = None


class PipelinePageFrontMatter(SitePipelineBaseModel):
    """Pipeline-owned page-local front matter."""

    kind: NonEmptyString
    section: NonEmptyString | None = None
    artifact_key: ArtifactKey | None = None
    path: PublicPath
    url: UrlString
    canonical_url: UrlString | None = None
    alternate_urls: list[UrlString] | None = None
    locale: NonEmptyString | None = None
    default_locale: bool | None = None
    translation_key: NonEmptyString | None = None
    translations: list[TranslationLinkSummary] | None = None
    component_path: PublicPath
    component_url: UrlString
    version: VersionContext | None = None
    provider: ProviderProvenance | None = None

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
    """Pipeline-owned component front matter."""

    slug: Slug
    display_name: NonEmptyString | None = None
    publication: ResolvedPublication
    artifacts: list[ArtifactFrontMatterSummary] | None = None


class PipelineFrontMatterNamespace(SitePipelineBaseModel):
    """Reserved top-level pipeline namespace emitted into staged pages."""

    component: PipelineComponentFrontMatter | None = None
    page: PipelinePageFrontMatter | None = None
