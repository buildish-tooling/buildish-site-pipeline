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

"""Effective authored-configuration resolution for planning."""

from __future__ import annotations

from pathlib import Path

from apache_buildish_site_pipeline.models.catalog import CatalogDocumentV1, ComponentCatalogEntry
from apache_buildish_site_pipeline.models.component_repository import ComponentRepositoryDocumentV1
from apache_buildish_site_pipeline.models.validation.urls import extract_hostname_from_url

from .types import (
    ResolvedArtifactConfig,
    ResolvedComponentConfig,
    ResolvedOrigin,
    ResolvedPublicationPolicy,
    ResolvedSiteConfig,
    ResolvedSourceBinding,
    ResolvedVendorAsset,
)

_DEFAULT_DEVELOPMENT_SEGMENT = "development"
_DEFAULT_DOCS_SEGMENT = "docs"
_DEFAULT_ASSETS_SEGMENT = "assets"


def resolve_site_config(
    *,
    catalog: CatalogDocumentV1,
    workspace_root: Path,
    component_documents: dict[str, ComponentRepositoryDocumentV1] | None = None,
) -> ResolvedSiteConfig:
    """Resolve defaults, groups, and component/artifact projections for planning."""

    component_documents = component_documents or {}
    normalized_workspace_root = workspace_root.resolve(strict=False)
    defaults = catalog.defaults

    origins = {
        key: ResolvedOrigin(
            key=key,
            base_url=str(origin.base_url),
            hostname=extract_hostname_from_url(str(origin.base_url)),
            canonical=bool(origin.canonical),
        )
        for key, origin in catalog.origins.items()
    }

    sources = {}
    for key, source in catalog.sources.items():
        local_dir = _resolve_repo_path(normalized_workspace_root, source.local_dir)
        metadata_relpath = source.metadata_file or defaults.metadata_file
        metadata_path = _resolve_repo_path(local_dir, metadata_relpath) if metadata_relpath else None
        sources[key] = ResolvedSourceBinding(
            key=key,
            local_dir=local_dir,
            metadata_file=metadata_path,
            repository=str(source.repository) if source.repository is not None else None,
            default_branch=str(source.default_branch) if source.default_branch is not None else None,
        )

    site_pages_root = _resolve_repo_path(normalized_workspace_root, catalog.site.pages_root) if catalog.site.pages_root else None
    site_assets_root = _resolve_repo_path(normalized_workspace_root, catalog.site.assets_root) if catalog.site.assets_root else None
    vendor_assets = tuple(
        ResolvedVendorAsset(
            key=f"vendorAssets:{index}",
            source_path=_resolve_repo_path(normalized_workspace_root, vendor_asset.source),
            config=vendor_asset,
        )
        for index, vendor_asset in enumerate(catalog.site.vendor_assets or ())
    )

    components = tuple(
        _resolve_component(
            catalog=catalog,
            component=component,
            component_document=component_documents.get(component.slug),
            origins=origins,
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
        components=components,
    )


def _resolve_component(
    *,
    catalog: CatalogDocumentV1,
    component: ComponentCatalogEntry,
    component_document: ComponentRepositoryDocumentV1 | None,
    origins: dict[str, ResolvedOrigin],
    sources: dict[str, ResolvedSourceBinding],
    workspace_root: Path,
) -> ResolvedComponentConfig:
    group = catalog.groups.get(component.group) if component.group is not None else None
    content_source = _resolve_component_content_source(
        component=component,
        sources=sources,
        workspace_root=workspace_root,
        default_metadata_file=catalog.defaults.metadata_file,
    )
    publication = _resolve_publication(
        catalog=catalog,
        component=component,
        group_path_prefix=group.path_prefix if group is not None else None,
        origins=origins,
    )

    metadata_file = content_source.metadata_file if content_source is not None else None
    pages_root = _resolve_component_content_path(content_source, component_document, "pages_root", catalog.defaults.pages_root)
    docs_root = _resolve_component_content_path(content_source, component_document, "docs_root", catalog.defaults.docs_root)
    assets_root = _resolve_component_content_path(content_source, component_document, "assets_root", catalog.defaults.assets_root)

    artifacts = []
    for artifact in component.artifacts or ():
        source_binding = sources[artifact.source]
        artifact_docs_root = _resolve_repo_path(source_binding.local_dir, artifact.docs_root) if artifact.docs_root else docs_root or source_binding.local_dir
        artifact_assets_root = _resolve_repo_path(source_binding.local_dir, artifact.assets_root) if artifact.assets_root else assets_root
        component_vocabulary = component_document.lifecycle.support_status_vocabulary if component_document and component_document.lifecycle else None
        artifact_vocabulary = artifact.lifecycle.support_status_vocabulary if artifact.lifecycle and artifact.lifecycle.support_status_vocabulary else None
        support_status_vocabulary = dict(component_vocabulary or {})
        support_status_vocabulary.update(artifact_vocabulary or {})
        artifacts.append(
            ResolvedArtifactConfig(
                key=artifact.key,
                authored=artifact,
                source_binding=source_binding,
                docs_root=artifact_docs_root,
                assets_root=artifact_assets_root,
                versioning=artifact.versioning,
                publication_selection=artifact.publication_selection,
                lifecycle=artifact.lifecycle,
                support_status_vocabulary=support_status_vocabulary,
            )
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
        publication_selection=component.publication_selection,
        artifacts=tuple(artifacts),
    )


def _resolve_component_content_source(
    *,
    component: ComponentCatalogEntry,
    sources: dict[str, ResolvedSourceBinding],
    workspace_root: Path,
    default_metadata_file: str | None,
) -> ResolvedSourceBinding | None:
    if component.content is not None and component.content.source is not None:
        return sources[component.content.source]
    if component.local_dir is None:
        return None
    local_dir = _resolve_repo_path(workspace_root, component.local_dir)
    metadata_path = _resolve_repo_path(local_dir, default_metadata_file) if default_metadata_file else None
    return ResolvedSourceBinding(
        key=f"component:{component.slug}",
        local_dir=local_dir,
        metadata_file=metadata_path,
        repository=None,
        default_branch=None,
    )


def _resolve_publication(
    *,
    catalog: CatalogDocumentV1,
    component: ComponentCatalogEntry,
    group_path_prefix: str | None,
    origins: dict[str, ResolvedOrigin],
) -> ResolvedPublicationPolicy:
    defaults = catalog.defaults.publication
    publication = component.publication
    origin_key = (
        publication.origin if publication and publication.origin is not None else None
    ) or (
        catalog.groups[component.group].publication.origin
        if component.group is not None
        and catalog.groups[component.group].publication is not None
        and catalog.groups[component.group].publication.origin is not None
        else None
    ) or (defaults.origin if defaults is not None else None)
    if origin_key is None:
        raise ValueError(f"Component {component.slug!r} cannot resolve a publication origin")

    mount_path = None
    if publication is not None and publication.mount_path is not None:
        mount_path = str(publication.mount_path)
    elif group_path_prefix is not None and publication is not None and publication.path_segment is not None:
        mount_path = _join_public_path(group_path_prefix, publication.path_segment)

    component_path = str(publication.component_path) if publication and publication.component_path is not None else mount_path
    if component_path is None:
        raise ValueError(f"Component {component.slug!r} cannot resolve a component publication path")

    development_segment = defaults.development_segment if defaults and defaults.development_segment else _DEFAULT_DEVELOPMENT_SEGMENT
    docs_segment = defaults.docs_segment if defaults and defaults.docs_segment else _DEFAULT_DOCS_SEGMENT
    assets_segment = defaults.assets_segment if defaults and defaults.assets_segment else _DEFAULT_ASSETS_SEGMENT
    development_path = str(publication.development_path) if publication and publication.development_path is not None else _join_public_path(component_path, development_segment)
    docs_path = str(publication.docs_path) if publication and publication.docs_path is not None else _join_public_path(development_path, docs_segment)
    assets_path = str(publication.assets_path) if publication and publication.assets_path is not None else _join_public_path(development_path, assets_segment)
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
        canonical_path=str(publication.canonical_path) if publication and publication.canonical_path is not None else None,
        aliases=tuple(publication.aliases or ()) if publication else (),
        redirects=tuple(publication.redirects or ()) if publication else (),
    )


def _resolve_component_content_path(
    source_binding: ResolvedSourceBinding | None,
    component_document: ComponentRepositoryDocumentV1 | None,
    field_name: str,
    default_relpath: str | None,
) -> Path | None:
    if source_binding is None:
        return None
    document_content = component_document.content if component_document is not None else None
    content_relpath = getattr(document_content, field_name) if document_content is not None else None
    effective_relpath = content_relpath or default_relpath
    if effective_relpath is None:
        return None
    return _resolve_repo_path(source_binding.local_dir, effective_relpath)


def _join_public_path(base_path: str, segment: str) -> str:
    stripped_base = base_path.rstrip("/")
    stripped_segment = segment.strip("/")
    if stripped_base == "":
        return f"/{stripped_segment}/"
    return f"{stripped_base}/{stripped_segment}/"


def _join_public_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def _resolve_repo_path(root: Path, relative_path: str) -> Path:
    candidate_path = (root / relative_path).resolve(strict=False)
    normalized_root = root.resolve(strict=False)
    if not candidate_path.is_relative_to(normalized_root):
        raise ValueError(f"Resolved path {candidate_path} escapes declared root {normalized_root}")
    return candidate_path