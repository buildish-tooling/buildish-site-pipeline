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

"""Canonical component source-root resolution helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from apache_buildish_site_pipeline.models.authored.site_catalog import (
    ComponentCatalogEntry,
    SiteCatalogDocumentV1,
)


@dataclass(frozen=True, slots=True)
class ResolvedSourceBinding:
    """Absolute and normalized binding for one authored source root."""

    key: str
    local_dir: Path
    metadata_file: Path | None
    repository: str | None
    default_branch: str | None


@dataclass(frozen=True, slots=True)
class ResolvedComponentSourceUsage:
    """One way a component consumes a resolved source binding."""

    source_binding: ResolvedSourceBinding
    owns_component_content: bool
    artifact_keys: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ResolvedComponentSourceRoot:
    """One effective source root consumed by a component."""

    component_slug: str
    local_dir: Path
    usages: tuple[ResolvedComponentSourceUsage, ...]


def resolve_repo_path(root: Path, relative_path: str) -> Path:
    """Resolve one repo-relative path and reject escapes."""

    candidate_path = (root / relative_path).resolve(strict=False)
    normalized_root = root.resolve(strict=False)
    if not candidate_path.is_relative_to(normalized_root):
        raise ValueError(
            f"Resolved path {candidate_path} escapes declared root {normalized_root}"
        )
    return candidate_path


def resolve_catalog_source_bindings(
    *, catalog: SiteCatalogDocumentV1, workspace_root: Path
) -> dict[str, ResolvedSourceBinding]:
    """Resolve named source bindings declared in the authored catalog."""

    normalized_workspace_root = workspace_root.resolve(strict=False)
    defaults = catalog.defaults
    source_configs = catalog.sources or {}
    resolved_bindings: dict[str, ResolvedSourceBinding] = {}
    for key, source in source_configs.items():
        local_dir = resolve_repo_path(normalized_workspace_root, source.local_dir)
        metadata_relpath = source.metadata_file or (
            defaults.metadata_file if defaults is not None else None
        )
        metadata_path = (
            resolve_repo_path(local_dir, metadata_relpath)
            if metadata_relpath is not None
            else None
        )
        resolved_bindings[key] = ResolvedSourceBinding(
            key=key,
            local_dir=local_dir,
            metadata_file=metadata_path,
            repository=str(source.repository)
            if source.repository is not None
            else None,
            default_branch=str(source.default_branch)
            if source.default_branch is not None
            else None,
        )
    return resolved_bindings


def resolve_component_content_source_binding(
    *,
    component: ComponentCatalogEntry,
    source_bindings: dict[str, ResolvedSourceBinding],
    workspace_root: Path,
    default_metadata_file: str | None,
) -> ResolvedSourceBinding | None:
    """Resolve the source binding that owns one component's shared content."""

    source_key = component.content.source if component.content is not None else None
    if source_key is not None:
        return _lookup_source_binding(
            source_bindings=source_bindings,
            source_key=source_key,
            component_slug=component.slug,
        )
    if component.local_dir is None:
        return None
    local_dir = resolve_repo_path(workspace_root.resolve(strict=False), component.local_dir)
    metadata_path = (
        resolve_repo_path(local_dir, default_metadata_file)
        if default_metadata_file is not None
        else None
    )
    return ResolvedSourceBinding(
        key=f"component:{component.slug}",
        local_dir=local_dir,
        metadata_file=metadata_path,
        repository=None,
        default_branch=None,
    )


def resolve_component_source_roots(
    *, catalog: SiteCatalogDocumentV1, workspace_root: Path
) -> tuple[ResolvedComponentSourceRoot, ...]:
    """Resolve effective per-component source roots across content and artifacts."""

    normalized_workspace_root = workspace_root.resolve(strict=False)
    default_metadata_file = (
        catalog.defaults.metadata_file if catalog.defaults is not None else None
    )
    source_bindings = resolve_catalog_source_bindings(
        catalog=catalog, workspace_root=normalized_workspace_root
    )
    resolved_roots: list[ResolvedComponentSourceRoot] = []
    for component in catalog.components:
        roots_by_local_dir: dict[Path, dict[str, _MutableSourceUsage]] = {}
        content_source = resolve_component_content_source_binding(
            component=component,
            source_bindings=source_bindings,
            workspace_root=normalized_workspace_root,
            default_metadata_file=default_metadata_file,
        )
        if content_source is not None:
            _register_source_usage(
                roots_by_local_dir,
                source_binding=content_source,
                owns_component_content=True,
            )
        for artifact in component.artifacts or ():
            _register_source_usage(
                roots_by_local_dir,
                source_binding=_lookup_source_binding(
                    source_bindings=source_bindings,
                    source_key=artifact.source,
                    component_slug=component.slug,
                    artifact_key=artifact.key,
                ),
                artifact_key=artifact.key,
            )
        resolved_roots.extend(
            ResolvedComponentSourceRoot(
                component_slug=component.slug,
                local_dir=local_dir,
                usages=tuple(
                    ResolvedComponentSourceUsage(
                        source_binding=usage.source_binding,
                        owns_component_content=usage.owns_component_content,
                        artifact_keys=tuple(usage.artifact_keys),
                    )
                    for usage in usages_by_key.values()
                ),
            )
            for local_dir, usages_by_key in roots_by_local_dir.items()
        )
    return tuple(resolved_roots)


@dataclass(slots=True)
class _MutableSourceUsage:
    source_binding: ResolvedSourceBinding
    owns_component_content: bool = False
    artifact_keys: list[str] = field(default_factory=list)


def _lookup_source_binding(
    *,
    source_bindings: dict[str, ResolvedSourceBinding],
    source_key: str,
    component_slug: str,
    artifact_key: str | None = None,
) -> ResolvedSourceBinding:
    try:
        return source_bindings[source_key]
    except KeyError as exc:
        context = (
            f"component {component_slug!r} artifact {artifact_key!r}"
            if artifact_key is not None
            else f"component {component_slug!r}"
        )
        raise ValueError(
            f"Catalog {context} references unknown source {source_key!r}"
        ) from exc


def _register_source_usage(
    roots_by_local_dir: dict[Path, dict[str, _MutableSourceUsage]],
    *,
    source_binding: ResolvedSourceBinding,
    owns_component_content: bool = False,
    artifact_key: str | None = None,
) -> None:
    usages_by_key = roots_by_local_dir.setdefault(source_binding.local_dir, {})
    usage = usages_by_key.get(source_binding.key)
    if usage is None:
        usage = _MutableSourceUsage(
            source_binding=source_binding,
            artifact_keys=[],
        )
        usages_by_key[source_binding.key] = usage
    if owns_component_content:
        usage.owns_component_content = True
    if artifact_key is not None and artifact_key not in usage.artifact_keys:
        usage.artifact_keys.append(artifact_key)
