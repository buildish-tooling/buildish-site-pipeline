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

"""Resolved local-input inventory for planning/build/watch."""

from __future__ import annotations

from apache_buildish_site_pipeline.models.enums import MaterializationInputKind, MaterializationStatus

from .types import (
    InputReadiness,
    LocalInputIdentity,
    ResolvedLocalInput,
    ResolvedSiteConfig,
    SelectedVersionSet,
)


def derive_local_inputs(*, site: ResolvedSiteConfig, selected_versions: SelectedVersionSet) -> tuple[ResolvedLocalInput, ...]:
    """Project the site and selected version contexts into concrete local inputs."""

    inputs: list[ResolvedLocalInput] = []
    if site.site_pages_root is not None:
        inputs.append(
            ResolvedLocalInput(
                identity=LocalInputIdentity(source_key="site:pages", input_kind=MaterializationInputKind.SITE_PAGES),
                declared_root=site.site_pages_root,
                expected_local_path=site.site_pages_root,
                provenance="workspace",
                readiness=InputReadiness(status=MaterializationStatus.UNRESOLVED),
            )
        )
    if site.site_assets_root is not None:
        inputs.append(
            ResolvedLocalInput(
                identity=LocalInputIdentity(source_key="site:assets", input_kind=MaterializationInputKind.SITE_ASSETS),
                declared_root=site.site_assets_root,
                expected_local_path=site.site_assets_root,
                provenance="workspace",
                readiness=InputReadiness(status=MaterializationStatus.UNRESOLVED),
            )
        )
    for vendor_asset in site.vendor_assets:
        inputs.append(
            ResolvedLocalInput(
                identity=LocalInputIdentity(source_key=vendor_asset.key, input_kind=MaterializationInputKind.VENDOR_ASSETS),
                declared_root=vendor_asset.source_path,
                expected_local_path=vendor_asset.source_path,
                provenance="workspace",
                readiness=InputReadiness(status=MaterializationStatus.UNRESOLVED),
            )
        )
    for context in selected_versions.contexts:
        expected_local_path = _expected_context_path(context)
        inputs.append(
            ResolvedLocalInput(
                identity=LocalInputIdentity(
                    source_key=context.source_binding.key,
                    input_kind=context.input_kind,
                    component_slug=context.component_slug,
                    artifact_key=context.artifact_key,
                    release_line=context.release_line,
                    version=context.version,
                    ref=context.ref,
                    tag=context.tag,
                    commit_sha=context.commit_sha,
                ),
                declared_root=context.source_binding.local_dir,
                expected_local_path=expected_local_path,
                provenance="workspace" if context.mutable_in_place else "snapshot",
                readiness=InputReadiness(status=MaterializationStatus.UNRESOLVED),
            )
        )
    return tuple(inputs)


def _expected_context_path(context: object):
    if context.input_kind is MaterializationInputKind.DEVELOPMENT:
        return context.docs_root
    if context.input_kind is MaterializationInputKind.LINE_HEAD and context.release_line is not None:
        return context.docs_root / "maintenance" / context.release_line
    if context.input_kind is MaterializationInputKind.RELEASED and context.version is not None:
        return context.docs_root / "releases" / context.version
    if context.input_kind is MaterializationInputKind.CANDIDATE and context.version is not None:
        return context.docs_root / "candidates" / context.version
    return context.docs_root