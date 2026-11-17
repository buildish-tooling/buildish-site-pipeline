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

"""Effective authored-configuration resolution for planning.

Maintainer note: this module is the ownership boundary between authored site
inputs and the normalized planning view that later phases consume.

- The site catalog owns publication policy, grouping, source bindings, and
  vendor assets.
- Component metadata defines artifact identities, streams, roots, and support defaults.
- Snapshot artifact sections supply release lines and lifecycle decisions; provider
  records join those identities during indexing. Public routes remain catalog-owned.

Keep that split obvious. If a later change wants provider data or staged-output
details to influence these resolved values, it almost certainly belongs in a
different layer.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from buildish_site_pipeline.models.authored.site_catalog import (
    CandidateSelectionPolicy,
    LineHeadSelectionPolicy,
    PublicationSelectionPolicy,
    ReleaseSelectionPolicy,
    ComponentCatalogEntry,
    SiteCatalogDocumentV1,
)
from buildish_site_pipeline.models.authored.component_metadata import (
    ComponentMetadataDocumentV1,
)
from buildish_site_pipeline.models.validation.urls import (
    extract_hostname_from_url,
)
from buildish_site_pipeline.public_paths import join_public_path
from buildish_site_pipeline.source_roots import (
    resolve_catalog_source_bindings,
    resolve_component_content_source_binding,
    resolve_repo_path as _resolve_repo_path,
)

from buildish_site_pipeline.models.provider.provider_snapshot import (
    ProviderSnapshotDocumentV1,
)
from buildish_site_pipeline.models.authored.artifacts import ArtifactLifecycleConfig

from buildish_site_pipeline.models.enums import (
    CandidateSelectionMode,
    LineHeadSelectionMode,
    ReleaseSelectionMode,
)

from .errors import PlanningInputFailure
from .types import (
    ResolvedArtifactConfig,
    ResolvedArtifactPublication,
    ResolvedComponentConfig,
    ResolvedLinkCheckPolicy,
    ResolvedLocalizationPolicy,
    ResolvedOrigin,
    ResolvedPublicationPolicy,
    ResolvedSiteConfig,
    ResolvedSourceBinding,
    ResolvedVendorAsset,
)

_DEFAULT_DEVELOPMENT_SEGMENT = "development"
_DEFAULT_DOCS_SEGMENT: str | None = None
_DEFAULT_ASSETS_SEGMENT = "assets"


def resolve_site_config(
    *,
    catalog: SiteCatalogDocumentV1,
    workspace_root: Path,
    component_documents: dict[str, ComponentMetadataDocumentV1] | None = None,
    provider_snapshot: ProviderSnapshotDocumentV1 | None = None,
) -> ResolvedSiteConfig:
    """Resolve authored inputs into one planning-only read model.

    This function normalizes repo-relative paths and merges catalog defaults,
    group policy, and optional component metadata. It does not inspect provider
    records or staged output.
    """

    component_documents = component_documents or {}
    normalized_workspace_root = workspace_root.resolve(strict=False)
    site_config = catalog.site
    origin_configs = catalog.origins or {}

    origins = {
        key: ResolvedOrigin(
            key=key,
            base_url=str(origin.base_url),
            hostname=extract_hostname_from_url(str(origin.base_url)),
            canonical=bool(origin.canonical),
        )
        for key, origin in origin_configs.items()
    }

    # Source bindings are the only place where authored repo-relative paths turn
    # into trusted workspace paths. Keep that normalization centralized here so
    # later phases can treat the resolved model as authoritative.
    sources = resolve_catalog_source_bindings(
        catalog=catalog, workspace_root=normalized_workspace_root
    )

    site_pages_root = (
        _resolve_repo_path(normalized_workspace_root, site_config.pages_root)
        if site_config and site_config.pages_root
        else None
    )
    site_assets_root = (
        _resolve_repo_path(normalized_workspace_root, site_config.assets_root)
        if site_config and site_config.assets_root
        else None
    )
    site_vendor_assets = site_config.vendor_assets if site_config is not None else None
    vendor_assets = tuple(
        ResolvedVendorAsset(
            key=f"vendorAssets:{index}",
            source_path=_resolve_repo_path(
                normalized_workspace_root, vendor_asset.source
            ),
            config=vendor_asset,
        )
        for index, vendor_asset in enumerate(site_vendor_assets or ())
    )
    link_checks = _resolve_link_checks(catalog)

    components = tuple(
        _resolve_component(
            catalog=catalog,
            component=component,
            component_document=component_documents.get(component.slug),
            origins=origins,
            provider_snapshot=provider_snapshot,
            sources=sources,
            workspace_root=normalized_workspace_root,
        )
        for component in catalog.components
    )

    return ResolvedSiteConfig(
        workspace_root=normalized_workspace_root,
        site_pages_root=site_pages_root,
        site_assets_root=site_assets_root,
        vendor_assets=vendor_assets,
        origins=origins,
        sources=sources,
        link_checks=link_checks,
        components=components,
    )


def _resolve_component(
    *,
    catalog: SiteCatalogDocumentV1,
    component: ComponentCatalogEntry,
    component_document: ComponentMetadataDocumentV1 | None,
    provider_snapshot: ProviderSnapshotDocumentV1 | None,
    origins: dict[str, ResolvedOrigin],
    sources: dict[str, ResolvedSourceBinding],
    workspace_root: Path,
) -> ResolvedComponentConfig:
    """Resolve one component while preserving authored ownership boundaries."""

    groups = catalog.groups or {}
    group = groups.get(component.group) if component.group is not None else None
    content_source = _resolve_component_content_source(
        component=component,
        sources=sources,
        workspace_root=workspace_root,
        default_metadata_file=catalog.defaults.metadata_file
        if catalog.defaults is not None
        else None,
    )
    # Publication stays catalog-owned even when component metadata exists. The
    # repository document may refine content roots, but it must never silently
    # move public URLs away from what the site owner authored in the catalog.
    publication = _resolve_publication(
        catalog=catalog,
        component=component,
        group_path_prefix=group.path_prefix if group is not None else None,
        origins=origins,
    )
    localization = _resolve_localization(catalog=catalog, component=component)

    metadata_file = content_source.metadata_file if content_source is not None else None
    pages_root = _resolve_component_content_path(
        content_source,
        component_document,
        "pages_root",
        catalog.defaults.pages_root if catalog.defaults is not None else None,
    )
    docs_root = _resolve_component_content_path(
        content_source,
        component_document,
        "docs_root",
        catalog.defaults.docs_root if catalog.defaults is not None else None,
    )
    assets_root = _resolve_component_content_path(
        content_source,
        component_document,
        "assets_root",
        catalog.defaults.assets_root if catalog.defaults is not None else None,
    )

    publication_selection = _resolve_publication_selection(
        _default_publication_selection_policy(), component.publication_selection
    )
    artifacts = []
    definitions = component_document.artifacts or () if component_document else ()
    bindings = {item.key: item for item in component.artifacts or ()}
    unknown = set(bindings) - {item.key for item in definitions}
    if unknown:
        raise PlanningInputFailure(
            f"Catalog bindings for {component.slug!r} reference unknown component artifacts: {sorted(unknown)}"
        )
    snapshots = (
        {
            (item.component_slug, item.artifact_key): item
            for item in provider_snapshot.artifacts
        }
        if provider_snapshot
        else {}
    )
    known = {item.key for item in definitions}
    if publication.default_artifact is not None and publication.default_artifact not in known:
        raise PlanningInputFailure(
            f"Component {component.slug!r} publication.defaultArtifact references unknown static artifact {publication.default_artifact!r}"
        )
    for owner, key in snapshots:
        if owner == component.slug and key not in known:
            raise PlanningInputFailure(
                f"Snapshot references unknown artifact {owner}:{key}"
            )
    for artifact in definitions:
        binding = bindings.get(artifact.key)
        source_binding = (
            sources[binding.source] if binding and binding.source else content_source
        )
        if source_binding is None:
            raise PlanningInputFailure(
                f"Artifact {component.slug}:{artifact.key} has no content source"
            )
        snapshot = snapshots.get((component.slug, artifact.key))
        lifecycle = ArtifactLifecycleConfig(
            **(artifact.lifecycle.model_dump() if artifact.lifecycle else {}),
            **(
                snapshot.model_dump(
                    exclude={
                        "component_slug",
                        "artifact_key",
                        "support_status_vocabulary",
                        "support_policy_url",
                        "default_support_window",
                    }
                )
                if snapshot
                else {}
            ),
        )
        docs_relative = (
            binding.docs_root if binding and binding.docs_root else artifact.docs_root
        )
        assets_relative = (
            binding.assets_root
            if binding and binding.assets_root
            else artifact.assets_root
        )
        artifact_docs_root = (
            _resolve_repo_path(source_binding.local_dir, docs_relative)
            if docs_relative
            else docs_root or source_binding.local_dir
        )
        artifact_assets_root = (
            _resolve_repo_path(source_binding.local_dir, assets_relative)
            if assets_relative
            else assets_root
        )
        component_vocabulary = (
            component_document.lifecycle.support_status_vocabulary
            if component_document and component_document.lifecycle
            else None
        )
        artifact_vocabulary = (
            artifact.lifecycle.support_status_vocabulary
            if artifact.lifecycle and artifact.lifecycle.support_status_vocabulary
            else None
        )
        # Component metadata provides the shared vocabulary baseline while the
        # artifact lifecycle can layer on additional statuses for that specific
        # publication surface.
        support_status_vocabulary = dict(component_vocabulary or {})
        support_status_vocabulary.update(artifact_vocabulary or {})
        artifacts.append(
            ResolvedArtifactConfig(
                key=artifact.key,
                publication=_resolve_artifact_publication(publication, artifact.key),
                authored=artifact,
                binding=binding,
                source_binding=source_binding,
                docs_root=artifact_docs_root,
                assets_root=artifact_assets_root,
                versioning=artifact.versioning,
                publication_selection=_resolve_publication_selection(
                    publication_selection,
                    binding.publication_selection if binding is not None else None,
                ),
                lifecycle=lifecycle,
                support_status_vocabulary=support_status_vocabulary,
            ),
        )

    publication = replace(
        publication,
        artifact_publications=tuple(
            artifact.publication for artifact in artifacts
        ),
    )
    return ResolvedComponentConfig(
        slug=component.slug,
        authored=component,
        repository_document=component_document,
        group_key=component.group,
        content_source=content_source,
        metadata_file=metadata_file,
        pages_root=pages_root,
        docs_root=docs_root,
        assets_root=assets_root,
        publication=publication,
        localization=localization,
        publication_selection=publication_selection,
        artifacts=tuple(artifacts),
        snapshot_path=_resolve_repo_path(
            sources[component.provider_snapshot.source].local_dir,
            component.provider_snapshot.path,
        )
        if component.provider_snapshot
        else None,
    )


def _resolve_artifact_publication(
    publication: ResolvedPublicationPolicy, key: str
) -> ResolvedArtifactPublication:
    def namespace(path: str) -> str:
        if publication.artifact_routing != "namespaced" or publication.default_artifact == key:
            return path
        root = publication.component_path
        if path.startswith(root):
            return f"{root}artifacts/{key}/{path[len(root):]}"
        return f"{path}artifacts/{key}/"

    return ResolvedArtifactPublication(
        key=key,
        origin=publication.origin,
        component_path=namespace(publication.component_path),
        development_path=namespace(publication.development_path),
        docs_path=namespace(publication.docs_path),
        release_base_path=namespace(
            publication.component_path
            if publication.docs_path == publication.development_path
            else publication.docs_path
        ),
    )


def _default_publication_selection_policy() -> PublicationSelectionPolicy:
    return PublicationSelectionPolicy(
        development=True,
        line_heads=LineHeadSelectionPolicy(mode=LineHeadSelectionMode.ALL_AUTHORED),
        releases=ReleaseSelectionPolicy(mode=ReleaseSelectionMode.LATEST_PER_LINE),
        named_refs=[],
        candidates=CandidateSelectionPolicy(mode=CandidateSelectionMode.NONE),
    )


def _resolve_publication_selection(
    inherited: PublicationSelectionPolicy,
    override: PublicationSelectionPolicy | None,
) -> PublicationSelectionPolicy:
    """Resolve independent fields, replacing nested modes and lists atomically."""

    if override is None:
        override = PublicationSelectionPolicy()
    named_refs = (
        override.named_refs if override.named_refs is not None else inherited.named_refs
    )
    return PublicationSelectionPolicy(
        development=override.development
        if override.development is not None
        else inherited.development,
        line_heads=override.line_heads
        if override.line_heads is not None
        else inherited.line_heads,
        releases=override.releases
        if override.releases is not None
        else inherited.releases,
        named_refs=list(named_refs) if named_refs is not None else None,
        candidates=override.candidates
        if override.candidates is not None
        else inherited.candidates,
    )


def _resolve_component_content_source(
    *,
    component: ComponentCatalogEntry,
    sources: dict[str, ResolvedSourceBinding],
    workspace_root: Path,
    default_metadata_file: str | None,
) -> ResolvedSourceBinding | None:
    return resolve_component_content_source_binding(
        component=component,
        source_bindings=sources,
        workspace_root=workspace_root,
        default_metadata_file=default_metadata_file,
    )


def _resolve_publication(
    *,
    catalog: SiteCatalogDocumentV1,
    component: ComponentCatalogEntry,
    group_path_prefix: str | None,
    origins: dict[str, ResolvedOrigin],
) -> ResolvedPublicationPolicy:
    """Resolve the catalog-owned publication contract for one component.

    Precedence is intentionally local and explicit: component override, then
    group policy, then site defaults. Component metadata and provider records
    never participate in public-origin or route-path resolution.
    """

    defaults = catalog.defaults.publication if catalog.defaults is not None else None
    publication = component.publication
    groups = catalog.groups or {}
    group = groups.get(component.group) if component.group is not None else None
    group_publication = group.publication if group is not None else None
    origin_key = (
        (publication.origin if publication and publication.origin is not None else None)
        or (
            group_publication.origin
            if group_publication is not None and group_publication.origin is not None
            else None
        )
        or (defaults.origin if defaults is not None else None)
    )
    if origin_key is None:
        raise PlanningInputFailure(
            f"Component {component.slug!r} cannot resolve a publication origin"
        )

    mount_path = None
    if publication is not None and publication.mount_path is not None:
        mount_path = str(publication.mount_path)
    elif (
        group_path_prefix is not None
        and publication is not None
        and publication.path_segment is not None
    ):
        mount_path = _join_public_path(group_path_prefix, publication.path_segment)

    component_path = (
        str(publication.component_path)
        if publication and publication.component_path is not None
        else mount_path
    )
    if component_path is None:
        raise PlanningInputFailure(
            f"Component {component.slug!r} cannot resolve a component publication path"
        )

    development_segment = (
        defaults.development_segment
        if defaults and defaults.development_segment
        else _DEFAULT_DEVELOPMENT_SEGMENT
    )
    docs_segment = (
        defaults.docs_segment
        if defaults and defaults.docs_segment
        else _DEFAULT_DOCS_SEGMENT
    )
    assets_segment = (
        defaults.assets_segment
        if defaults and defaults.assets_segment
        else _DEFAULT_ASSETS_SEGMENT
    )
    development_path = (
        str(publication.development_path)
        if publication and publication.development_path is not None
        else _join_public_path(component_path, development_segment)
    )
    docs_path = (
        str(publication.docs_path)
        if publication and publication.docs_path is not None
        else _join_public_path(development_path, docs_segment)
        if docs_segment is not None
        else development_path
    )
    assets_path = (
        str(publication.assets_path)
        if publication and publication.assets_path is not None
        else _join_public_path(component_path, assets_segment)
    )
    origin = origins[origin_key]
    return ResolvedPublicationPolicy(
        origin=origin,
        component_path=component_path,
        development_path=development_path,
        docs_path=docs_path,
        assets_path=assets_path,
        component_url=_join_public_url(origin.base_url, component_path),
        development_url=_join_public_url(origin.base_url, development_path),
        docs_url=_join_public_url(origin.base_url, docs_path),
        assets_url=_join_public_url(origin.base_url, assets_path),
        artifact_routing=publication.artifact_routing or "shared" if publication else "shared",
        default_artifact=publication.default_artifact if publication else None,
        canonical_path=str(publication.canonical_path)
        if publication and publication.canonical_path is not None
        else None,
        aliases=tuple(publication.aliases or ()) if publication else (),
        redirects=tuple(publication.redirects or ()) if publication else (),
    )


def _resolve_component_content_path(
    source_binding: ResolvedSourceBinding | None,
    component_document: ComponentMetadataDocumentV1 | None,
    field_name: str,
    default_relpath: str | None,
) -> Path | None:
    if source_binding is None:
        return None
    document_content = (
        component_document.content if component_document is not None else None
    )
    content_relpath = (
        getattr(document_content, field_name) if document_content is not None else None
    )
    effective_relpath = content_relpath or default_relpath
    if effective_relpath is None:
        return None
    return _resolve_repo_path(source_binding.local_dir, effective_relpath)


def _resolve_localization(
    *,
    catalog: SiteCatalogDocumentV1,
    component: ComponentCatalogEntry,
) -> ResolvedLocalizationPolicy:
    defaults = catalog.defaults.localization if catalog.defaults is not None else None
    authored = component.localization
    if defaults is None and authored is None:
        return ResolvedLocalizationPolicy(
            default_locale=None,
            supported_locales=None,
            fallback_locale=None,
            route_mode=None,
        )
    return ResolvedLocalizationPolicy(
        default_locale=(
            authored.default_locale
            if authored and authored.default_locale is not None
            else (defaults.default_locale if defaults is not None else None)
        ),
        supported_locales=(
            tuple(authored.supported_locales)
            if authored and authored.supported_locales is not None
            else (
                tuple(defaults.supported_locales)
                if defaults is not None and defaults.supported_locales is not None
                else None
            )
        ),
        fallback_locale=(
            authored.fallback_locale
            if authored and authored.fallback_locale is not None
            else (defaults.fallback_locale if defaults is not None else None)
        ),
        route_mode=(
            authored.route_mode
            if authored and authored.route_mode is not None
            else (defaults.route_mode if defaults is not None else None)
        ),
    )


def _resolve_link_checks(
    catalog: SiteCatalogDocumentV1,
) -> ResolvedLinkCheckPolicy | None:
    validation = catalog.validation
    if validation is None or validation.link_checks is None:
        return None

    link_checks = validation.link_checks
    return ResolvedLinkCheckPolicy(
        enabled=link_checks.enabled,
        mode=link_checks.mode,
        check_root_absolute=link_checks.check_root_absolute,
        internal_prefixes=tuple(
            str(prefix) for prefix in (link_checks.internal_prefixes or ())
        ),
    )


def _join_public_path(base_path: str, segment: str) -> str:
    return join_public_path(base_path, segment, trailing_slash=True)


def _join_public_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"
