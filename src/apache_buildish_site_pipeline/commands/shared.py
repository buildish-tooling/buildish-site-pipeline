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

"""Shared workspace loading helpers for CLI commands."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from apache_buildish_site_pipeline.models import ProviderSnapshotV1
from apache_buildish_site_pipeline.models.catalog import CatalogDocumentV1
from apache_buildish_site_pipeline.models.component_repository import ComponentRepositoryDocumentV1
from apache_buildish_site_pipeline.models.enums import DocumentFormat
from apache_buildish_site_pipeline.models.loading import (
    LoadingError,
    load_catalog_document,
    load_component_repository_document,
    load_provider_snapshot,
)

from ..cli.errors import InvocationError

_DEFAULT_CATALOG_PATH = Path("site/components.yaml")
_PROVIDER_SNAPSHOT_CANDIDATE_NAMES = (
    "provider-snapshot.yaml",
    "provider-snapshot.yml",
    "provider-snapshot.json",
)


@dataclass(frozen=True, slots=True)
class LoadedWorkspaceInputs:
    """Fully loaded repository inputs for planning/evaluation."""

    catalog: CatalogDocumentV1
    provider_snapshot: ProviderSnapshotV1
    component_documents: dict[str, ComponentRepositoryDocumentV1]
    catalog_path: Path
    provider_snapshot_path: Path | None


def load_workspace_inputs(workspace_root: Path, catalog_path: Path | None = None) -> LoadedWorkspaceInputs:
    """Load default catalog, provider snapshot, and component metadata inputs."""

    resolved_workspace_root = workspace_root.resolve(strict=False)
    resolved_catalog_path = (
        catalog_path.resolve(strict=False)
        if catalog_path is not None
        else (resolved_workspace_root / _DEFAULT_CATALOG_PATH).resolve(strict=False)
    )
    if not resolved_catalog_path.exists():
        raise InvocationError(f"Missing catalog document: {resolved_catalog_path}")
    site_root = resolved_catalog_path.parent

    try:
        catalog = load_catalog_document(
            _read_utf8(resolved_catalog_path),
            document_format=_infer_document_format(resolved_catalog_path),
            source_name=str(resolved_catalog_path),
        )
        provider_snapshot, provider_snapshot_path = _load_provider_snapshot(site_root)
        component_documents = _load_component_documents(resolved_workspace_root, catalog)
    except LoadingError as exc:
        raise InvocationError(str(exc)) from exc
    return LoadedWorkspaceInputs(
        catalog=catalog,
        provider_snapshot=provider_snapshot,
        component_documents=component_documents,
        catalog_path=resolved_catalog_path,
        provider_snapshot_path=provider_snapshot_path,
    )


def _load_provider_snapshot(site_root: Path) -> tuple[ProviderSnapshotV1, Path | None]:
    found_paths = [
        (site_root / candidate_name).resolve(strict=False)
        for candidate_name in _PROVIDER_SNAPSHOT_CANDIDATE_NAMES
        if (site_root / candidate_name).exists()
    ]
    if len(found_paths) > 1:
        raise InvocationError(
            "Found multiple default provider snapshot files; keep only one of "
            f"{', '.join(str(path) for path in found_paths)}",
        )
    if not found_paths:
        return ProviderSnapshotV1(schema_version=1, providers=[], records=[]), None
    provider_snapshot_path = found_paths[0]
    return (
        load_provider_snapshot(
            _read_utf8(provider_snapshot_path),
            document_format=_infer_document_format(provider_snapshot_path),
            source_name=str(provider_snapshot_path),
        ),
        provider_snapshot_path,
    )


def _load_component_documents(
    repo_root: Path,
    catalog: CatalogDocumentV1,
) -> dict[str, ComponentRepositoryDocumentV1]:
    component_documents: dict[str, ComponentRepositoryDocumentV1] = {}
    default_metadata_file = catalog.defaults.metadata_file if catalog.defaults is not None else None
    sources = catalog.sources or {}
    for component in catalog.components:
        source_key = component.content.source if component.content is not None else None
        if source_key is not None:
            source_binding = sources[source_key]
            repository_root = (repo_root / source_binding.local_dir).resolve(strict=False)
            metadata_file = source_binding.metadata_file or default_metadata_file
        elif component.local_dir is not None:
            repository_root = (repo_root / component.local_dir).resolve(strict=False)
            metadata_file = default_metadata_file
        else:
            continue
        if metadata_file is None:
            continue
        metadata_path = (repository_root / metadata_file).resolve(strict=False)
        if not metadata_path.is_relative_to(repository_root):
            raise InvocationError(f"Component metadata path escapes its repository root: {metadata_path}")
        if not metadata_path.exists():
            continue
        component_documents[component.slug] = load_component_repository_document(
            _read_utf8(metadata_path),
            document_format=_infer_document_format(metadata_path),
            source_name=str(metadata_path),
        )
    return component_documents


def _infer_document_format(path: Path) -> DocumentFormat:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return DocumentFormat.JSON
    if suffix in {".yaml", ".yml"}:
        return DocumentFormat.YAML
    raise InvocationError(f"Unsupported document format for {path}")


def _read_utf8(path: Path) -> str:
    return path.read_text(encoding="utf-8")