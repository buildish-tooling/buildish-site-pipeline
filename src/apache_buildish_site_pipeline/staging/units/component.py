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

"""Worker for per-component pages, assets, and selected version contexts."""

from __future__ import annotations

import shutil
from pathlib import Path

from apache_buildish_site_pipeline.models.staged_front_matter import (
    PipelineComponentFrontMatter,
    PipelineFrontMatterNamespace,
)

from ..front_matter import (
    authored_link_title,
    authored_title,
    detect_locale,
    extract_page_translation_key,
    is_page_path,
    public_page_path,
    public_page_url,
    stage_authored_page,
)
from ..source_tree import iter_source_tree_files
from ..worker_protocol import (
    ContributionFileRefs,
    StagedPageContributionWire,
    UnitContributionManifestWire,
    WorkerResultWire,
    WorkerSpecWire,
    write_unit_manifest,
)


def run_component_unit(spec: WorkerSpecWire) -> WorkerResultWire:
    """Stage one component subtree and emit page contribution fragments."""

    files_written = 0
    page_files_written = 0
    asset_files_written = 0
    page_contributions: list[StagedPageContributionWire] = []
    component_namespace = (
        PipelineComponentFrontMatter.model_validate(spec.component_front_matter)
        if spec.component_front_matter is not None
        else None
    )

    if (
        spec.component_pages_source is not None
        and spec.component_pages_stage_root is not None
        and spec.component_publication is not None
    ):
        contributions, written = _stage_pages_tree(
            source_root=Path(spec.component_pages_source),
            destination_root=Path(spec.component_pages_stage_root),
            base_publication=spec.component_publication,
            component_slug=spec.component_slug or "",
            artifact_key=None,
            section="component",
            page_kind="component-page",
            version_context=None,
            record_kind=None,
            version_ref=None,
            version=None,
            localization=spec.localization,
            component_namespace=component_namespace,
        )
        page_contributions.extend(contributions)
        files_written += written[0]
        page_files_written += written[1]

    if (
        spec.component_assets_source is not None
        and spec.component_assets_stage_root is not None
    ):
        written_assets = _copy_tree(
            Path(spec.component_assets_source), Path(spec.component_assets_stage_root)
        )
        files_written += written_assets
        asset_files_written += written_assets

    for context in spec.contexts:
        if context.source_docs_root is not None:
            contributions, written = _stage_pages_tree(
                source_root=Path(context.source_docs_root),
                destination_root=Path(context.content_stage_root),
                base_publication=context.publication,
                component_slug=spec.component_slug or "",
                artifact_key=context.artifact_key,
                section=context.section,
                page_kind=context.page_kind,
                version_context=context.version_context,
                record_kind=context.record_kind,
                version_ref=context.version_ref,
                version=context.version,
                localization=spec.localization,
                component_namespace=component_namespace,
            )
            page_contributions.extend(contributions)
            files_written += written[0]
            page_files_written += written[1]
        if context.source_assets_root is not None:
            written_assets = _copy_tree(
                Path(context.source_assets_root), Path(context.static_stage_root)
            )
            files_written += written_assets
            asset_files_written += written_assets

    contribution_files = ContributionFileRefs(unit_manifest=spec.fragment_path)
    write_unit_manifest(
        Path(spec.fragment_path),
        UnitContributionManifestWire(
            unit_id=spec.unit_id, pages=tuple(page_contributions)
        ),
    )
    return WorkerResultWire(
        unit_id=spec.unit_id,
        files_written=files_written,
        page_files_written=page_files_written,
        asset_files_written=asset_files_written,
        contribution_files=contribution_files,
        stage_meta=spec.stage_meta,
    )


def _stage_pages_tree(
    *,
    source_root: Path,
    destination_root: Path,
    base_publication,
    component_slug: str,
    artifact_key: str | None,
    section: str,
    page_kind: str,
    version_context: dict[str, object] | None,
    record_kind: str | None,
    version_ref: str | None,
    version: str | None,
    localization,
    component_namespace: PipelineComponentFrontMatter | None,
) -> tuple[list[StagedPageContributionWire], tuple[int, int]]:
    contributions: list[StagedPageContributionWire] = []
    files_written = 0
    page_files_written = 0
    for source_path, relative_path in iter_source_tree_files(source_root=source_root):
        destination_path = destination_root / relative_path
        if not is_page_path(source_path):
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, destination_path)
            files_written += 1
            continue
        locale, default_locale, routed_relative_path = detect_locale(
            relative_path, localization
        )
        public_path = public_page_path(base_publication.path, routed_relative_path)
        public_url = public_page_url(
            base_publication.url, public_path, route_base_path=base_publication.path
        )
        metadata = stage_authored_page(
            source_path=source_path,
            destination_path=destination_path,
            namespace=PipelineFrontMatterNamespace(
                component=component_namespace,
                page=None,
            )
            if component_namespace is not None
            else None,
        )
        contributions.append(
            StagedPageContributionWire(
                stage_relative_path=destination_path.as_posix(),
                component_slug=component_slug,
                artifact_key=artifact_key,
                section=section,
                page_kind=page_kind,
                public_path=public_path,
                public_url=public_url,
                component_path=base_publication.component_path,
                component_url=base_publication.component_url,
                origin_key=base_publication.origin_key,
                version_context=version_context,
                version_kind=record_kind,
                version_ref=version_ref,
                version=version,
                locale=locale,
                default_locale=default_locale,
                translation_key=extract_page_translation_key(metadata),
                title=authored_title(metadata),
                link_title=authored_link_title(metadata),
                source_path=source_path.as_posix(),
                canonical_url=public_url,
            ),
        )
        files_written += 1
        page_files_written += 1
    return contributions, (files_written, page_files_written)


def _copy_tree(source_root: Path, target_root: Path) -> int:
    count = 0
    for source_path, relative_path in iter_source_tree_files(source_root=source_root):
        destination_path = target_root / relative_path
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)
        count += 1
    return count
