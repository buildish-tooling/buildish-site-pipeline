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

"""Pipeline-owned page front matter helpers for stage assembly."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import frontmatter

from apache_buildish_site_pipeline.cli.errors import StageIntegrityError
from apache_buildish_site_pipeline.models.authored.site_catalog import (
    ArtifactLifecycleConfig,
    ExactReleaseConfig,
    ReleaseLineConfig,
)
from apache_buildish_site_pipeline.models.authored.page_metadata import (
    PageTranslationMetadata,
)
from apache_buildish_site_pipeline.page_support import (
    is_supported_page_path,
    strips_suffix_in_pretty_route,
)
from apache_buildish_site_pipeline.models.emitted.staged_front_matter import (
    ArtifactFrontMatterSummary,
    PipelineComponentFrontMatter,
    PipelineFrontMatterNamespace,
    PipelinePageFrontMatter,
    ProviderProvenance,
    ReleaseLineContext,
    ReleaseLineSummary,
    ResolvedOrigin,
    ResolvedPathSet,
    ResolvedPublication,
    ResolvedUrlSet,
    TranslationLinkSummary,
    VersionContext,
)
from apache_buildish_site_pipeline.planning.types import (
    ResolvedArtifactConfig,
    ResolvedComponentConfig,
    ResolvedLocalizationPolicy,
    SelectedVersionContext,
)
from apache_buildish_site_pipeline.staging.file_writes import write_utf8_text_file
from apache_buildish_site_pipeline.staging.publication_paths import (
    public_path_for_context,
)
from apache_buildish_site_pipeline.staging.worker_protocol import (
    StagedPageContributionWire,
)


def is_page_path(path: Path) -> bool:
    """Return whether one source file should be treated as a content page."""

    return is_supported_page_path(path)


def build_component_front_matter(
    component: ResolvedComponentConfig,
    selected_versions: tuple[SelectedVersionContext, ...],
) -> PipelineComponentFrontMatter:
    """Build the stable pipeline-owned component summary for staged pages."""

    selected_by_artifact: dict[str, list[SelectedVersionContext]] = {}
    for context in selected_versions:
        if context.component_slug != component.slug:
            continue
        if context.artifact_key is None:
            continue
        selected_by_artifact.setdefault(context.artifact_key, []).append(context)

    artifact_summaries: list[ArtifactFrontMatterSummary] = []
    for artifact in component.artifacts:
        lifecycle = artifact.lifecycle
        release_lines = _release_line_summaries(
            artifact, selected_by_artifact.get(artifact.key, [])
        )
        artifact_summaries.append(
            ArtifactFrontMatterSummary(
                key=artifact.key,
                display_name=_artifact_display_name(artifact),
                latest_stable=lifecycle.latest_stable
                if lifecycle is not None
                else None,
                release_lines=release_lines or None,
            ),
        )

    publication = component.publication
    return PipelineComponentFrontMatter(
        slug=component.slug,
        display_name=_component_display_name(component),
        latest_stable=_component_latest_stable(component),
        publication=ResolvedPublication(
            origin=ResolvedOrigin(
                key=publication.origin.key,
                base_url=publication.origin.base_url,
                hostname=publication.origin.hostname,
            ),
            paths=ResolvedPathSet(
                component=publication.component_path,
                development=publication.development_path,
                docs=publication.docs_path,
                assets=publication.assets_path,
            ),
            urls=ResolvedUrlSet(
                component=publication.component_url,
                development=publication.development_url,
                docs=publication.docs_url,
                assets=publication.assets_url,
            ),
        ),
        artifacts=artifact_summaries or None,
    )


def build_version_context(
    component: ResolvedComponentConfig, context: SelectedVersionContext
) -> VersionContext:
    """Build the page-local version context for one selected version subtree."""

    publication = component.publication
    lifecycle = _artifact_lifecycle(component, artifact_key=context.artifact_key)
    provider_record = context.provider_record
    release_line_key = context.release_line or (
        provider_record.release_line if provider_record is not None else None
    )
    line_config = _release_line_config(lifecycle, release_line_key=release_line_key)
    exact_release = _exact_release_config(lifecycle, version=context.version)
    support_window = exact_release.support_window if exact_release is not None else None
    if support_window is None and line_config is not None:
        support_window = line_config.support_window

    release_line = None
    if release_line_key is not None:
        release_line = ReleaseLineContext(
            key=release_line_key,
            support_status=(
                exact_release.support_status if exact_release is not None else None
            )
            or (line_config.support_status if line_config is not None else None),
            ancestors=list(provider_record.release_line_ancestors)
            if provider_record is not None
            else None,
            support_window=line_config.support_window
            if line_config is not None
            else None,
        )

    label = (
        context.display_version
        or context.version
        or context.named_ref_key
        or context.ref
        or context.release_line
        or context.kind.value
    )

    return VersionContext(
        kind=context.kind,
        label=label,
        path=public_path_for_context(publication=publication, context=context),
        url=_public_url_for_path(
            publication.origin.base_url,
            public_path_for_context(publication=publication, context=context),
        ),
        docs_path=public_path_for_context(publication=publication, context=context),
        docs_url=_public_url_for_path(
            publication.origin.base_url,
            public_path_for_context(publication=publication, context=context),
        ),
        tag=context.tag
        or (provider_record.tag if provider_record is not None else None),
        ref=context.ref,
        named_ref_key=context.named_ref_key
        if context.kind.value == "namedRef"
        else None,
        publication_state=context.publication_state
        or (provider_record.publication_state if provider_record is not None else None),
        maturity=context.maturity
        or (provider_record.maturity if provider_record is not None else None),
        candidate_sequence=provider_record.candidate_sequence
        if provider_record is not None
        else None,
        vote_status=provider_record.vote_status
        if provider_record is not None
        else None,
        release_line=release_line,
        support_window=support_window,
    )


def stage_authored_page(
    *,
    source_path: Path,
    destination_path: Path,
    namespace: PipelineFrontMatterNamespace | None,
) -> Mapping[str, object]:
    """Copy one page source into the private stage and merge pipeline metadata."""

    post = _load_authored_post(source_path=source_path, allow_existing_pipeline=False)
    metadata = dict(post.metadata)
    if namespace is not None:
        metadata["pipeline"] = namespace.model_dump(
            mode="json", by_alias=True, exclude_none=True
        )
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    rendered_post = frontmatter.Post(post.content, **metadata)
    write_utf8_text_file(destination_path, frontmatter.dumps(rendered_post))
    return metadata


def finalize_staged_page(
    *,
    staged_page_path: Path,
    page: PipelinePageFrontMatter,
    component: PipelineComponentFrontMatter | None,
) -> None:
    """Rewrite one already staged page with finalized page-local pipeline metadata."""

    post = _load_authored_post(
        source_path=staged_page_path, allow_existing_pipeline=True
    )
    metadata = dict(post.metadata)
    metadata["pipeline"] = PipelineFrontMatterNamespace(
        component=component,
        page=page,
    ).model_dump(mode="json", by_alias=True, exclude_none=True)
    write_utf8_text_file(
        staged_page_path, frontmatter.dumps(frontmatter.Post(post.content, **metadata))
    )


def extract_page_translation_key(metadata: Mapping[str, object]) -> str | None:
    """Return one validated translation key from authored page metadata."""

    candidate = (
        metadata.get("translationKey")
        if "translationKey" in metadata
        else metadata.get("translation_key")
    )
    if candidate is None:
        return None
    translation = PageTranslationMetadata.model_validate({"translationKey": candidate})
    return translation.translation_key


def authored_title(metadata: Mapping[str, object]) -> str | None:
    """Return one authored title-like string when present."""

    for key in ("title", "linkTitle", "link_title"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def authored_link_title(metadata: Mapping[str, object]) -> str | None:
    """Return one authored link-title string when present."""

    for key in ("linkTitle", "link_title"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def detect_locale(
    relative_source_path: Path, localization: ResolvedLocalizationPolicy | None
) -> tuple[str | None, bool, Path]:
    """Resolve locale and routed relative path for one staged page."""

    if localization is None or localization.default_locale is None:
        return None, False, relative_source_path
    if localization.route_mode is not None and localization.route_mode.value != "path":
        return localization.default_locale, True, relative_source_path
    supported_locales = set(localization.supported_locales or ())
    parts = relative_source_path.parts
    if parts and parts[0] in supported_locales:
        locale = parts[0]
        return (
            locale,
            locale == localization.default_locale,
            Path(*parts[1:]) if len(parts) > 1 else Path(),
        )
    return localization.default_locale, True, relative_source_path


def build_page_front_matter(
    *,
    contribution: StagedPageContributionWire,
    translations: list[TranslationLinkSummary] | None,
) -> PipelinePageFrontMatter:
    """Create finalized page front matter from one staged-page contribution."""

    alternate_urls = None
    if translations:
        alternate_urls = (
            sorted(
                {
                    translation.url
                    for translation in translations
                    if translation.url != contribution.public_url
                }
            )
            or None
        )
    version_context = contribution.version_context or None
    normalized_version_context = None
    if version_context is not None:
        normalized_version_context = dict(version_context)
        normalized_version_context.pop("provider", None)
    page_url = contribution.public_url or contribution.canonical_url
    if page_url is None:
        raise StageIntegrityError(
            f"Staged page contribution is missing a public URL: {contribution.stage_relative_path}"
        )
    component_url = (
        contribution.component_url
        or contribution.public_url
        or contribution.canonical_url
    )
    if component_url is None:
        raise StageIntegrityError(
            f"Staged page contribution is missing a component URL: {contribution.stage_relative_path}",
        )
    return PipelinePageFrontMatter(
        kind=contribution.page_kind,
        section=contribution.section,
        artifact_key=contribution.artifact_key,
        path=contribution.public_path,
        url=page_url,
        canonical_url=contribution.canonical_url,
        alternate_urls=alternate_urls,
        locale=contribution.locale,
        default_locale=contribution.default_locale
        if contribution.locale is not None
        else None,
        translation_key=contribution.translation_key,
        translations=translations or None,
        component_path=contribution.component_path,
        component_url=component_url,
        version=VersionContext.model_validate(normalized_version_context)
        if normalized_version_context is not None
        else None,
        provider=_provider_provenance(contribution),
    )


def build_translation_link(
    contribution: StagedPageContributionWire,
) -> TranslationLinkSummary:
    """Convert one staged-page contribution into one translation sibling link."""

    if contribution.locale is None:
        raise ValueError("Translation links require a locale")
    if contribution.public_url is None:
        raise ValueError("Translation links require a public URL")
    return TranslationLinkSummary(
        locale=contribution.locale,
        path=contribution.public_path,
        url=contribution.public_url,
        title=contribution.title,
    )


def public_page_path(base_path: str, relative_path: Path) -> str:
    """Resolve a route-like public path for one staged page file."""

    normalized_relative = relative_path.as_posix().strip("/")
    stem = relative_path.stem
    if stem == "index":
        parent = relative_path.parent.as_posix().strip(".")
        return _join_public_path(base_path, parent)
    if strips_suffix_in_pretty_route(relative_path):
        without_suffix = relative_path.with_suffix("").as_posix().strip("/")
        return _join_public_path(base_path, without_suffix)
    return _join_public_path(base_path, normalized_relative)


def public_page_url(
    base_url: str | None, public_path: str, *, route_base_path: str | None = None
) -> str | None:
    """Resolve one fully-qualified page URL when one origin URL is available."""

    if base_url is None:
        return None
    if route_base_path is not None:
        normalized_route_base_path = route_base_path.rstrip("/")
        normalized_public_path = public_path.rstrip("/")
        if normalized_public_path == normalized_route_base_path:
            return base_url.rstrip("/") + "/"
        if normalized_public_path.startswith(f"{normalized_route_base_path}/"):
            suffix = normalized_public_path[len(normalized_route_base_path) :].strip(
                "/"
            )
            return base_url.rstrip("/") + (f"/{suffix}" if suffix else "/")
    return _public_url_for_path(base_url, public_path)


def _load_authored_post(
    *, source_path: Path, allow_existing_pipeline: bool
) -> frontmatter.Post:
    raw_text = source_path.read_text(encoding="utf-8")
    post = frontmatter.loads(raw_text)
    if not allow_existing_pipeline and "pipeline" in post.metadata:
        raise StageIntegrityError(
            f"Authored page front matter in {source_path} must not define the reserved 'pipeline' namespace",
        )
    return post


def _artifact_display_name(artifact: ResolvedArtifactConfig) -> str | None:
    display_name = getattr(artifact.authored, "display_name", None)
    return display_name if isinstance(display_name, str) else None


def _component_display_name(component: ResolvedComponentConfig) -> str | None:
    display_name = getattr(component.authored, "display_name", None)
    if isinstance(display_name, str):
        return display_name

    repository_document = getattr(component, "repository_document", None)
    repository_component = getattr(repository_document, "component", None)
    repository_display_name = getattr(repository_component, "display_name", None)
    return repository_display_name if isinstance(repository_display_name, str) else None


def _component_latest_stable(component: ResolvedComponentConfig) -> str | None:
    repository_document = getattr(component, "repository_document", None)
    repository_lifecycle = getattr(repository_document, "lifecycle", None)
    latest_stable = getattr(repository_lifecycle, "latest_stable", None)
    return latest_stable if isinstance(latest_stable, str) else None


def _artifact_lifecycle(
    component: ResolvedComponentConfig, *, artifact_key: str | None
) -> ArtifactLifecycleConfig | None:
    if artifact_key is None:
        return None
    for artifact in component.artifacts:
        if artifact.key == artifact_key:
            return artifact.lifecycle
    return None


def _release_line_summaries(
    artifact: ResolvedArtifactConfig,
    selected_contexts: list[SelectedVersionContext],
) -> list[ReleaseLineSummary]:
    lifecycle = artifact.lifecycle
    if lifecycle is None or lifecycle.release_lines is None:
        return []
    head_ref_by_line: dict[str, str] = {}
    for context in selected_contexts:
        provider_record = context.provider_record
        if (
            context.kind.value == "lineHead"
            and provider_record is not None
            and provider_record.release_line is not None
            and context.ref is not None
        ):
            head_ref_by_line.setdefault(provider_record.release_line, context.ref)
    return [
        ReleaseLineSummary(
            key=release_line.key,
            parent=release_line.parent,
            latest=release_line.latest,
            support_status=release_line.support_status,
            head_ref=head_ref_by_line.get(release_line.key),
            aliases=release_line.aliases,
            support_window=release_line.support_window,
        )
        for release_line in lifecycle.release_lines
    ]


def _release_line_config(
    lifecycle: ArtifactLifecycleConfig | None, *, release_line_key: str | None
) -> ReleaseLineConfig | None:
    if lifecycle is None or lifecycle.release_lines is None or release_line_key is None:
        return None
    for release_line in lifecycle.release_lines:
        if release_line.key == release_line_key:
            return release_line
    return None


def _exact_release_config(
    lifecycle: ArtifactLifecycleConfig | None, *, version: str | None
) -> ExactReleaseConfig | None:
    if lifecycle is None or lifecycle.releases is None or version is None:
        return None
    for release in lifecycle.releases:
        if release.version == version:
            return release
    return None


def _provider_provenance(
    contribution: StagedPageContributionWire,
) -> ProviderProvenance | None:
    version_context = contribution.version_context or {}
    provider = version_context.get("provider")
    if not isinstance(provider, Mapping):
        return None
    key = provider.get("key")
    if not isinstance(key, str):
        return None
    return ProviderProvenance(
        key=key,
        external_id=provider.get("externalId")
        if isinstance(provider.get("externalId"), str)
        else provider.get("external_id")
        if isinstance(provider.get("external_id"), str)
        else None,
        external_url=provider.get("externalUrl")
        if isinstance(provider.get("externalUrl"), str)
        else provider.get("external_url")
        if isinstance(provider.get("external_url"), str)
        else None,
    )


def _public_url_for_path(base_url: str, public_path: str) -> str:
    return base_url.rstrip("/") + public_path


def _join_public_path(base_path: str, suffix: str) -> str:
    normalized_base = "/" + base_path.strip("/") if base_path.strip("/") else "/"
    normalized_suffix = suffix.strip("/")
    if not normalized_suffix:
        return normalized_base if normalized_base != "" else "/"
    if normalized_base == "/":
        return f"/{normalized_suffix}"
    return f"{normalized_base.rstrip('/')}/{normalized_suffix}"
