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

"""Small publication-path helpers reused by staging without evaluation imports."""

from __future__ import annotations

from pathlib import Path

from buildish_site_pipeline.models.enums import RecordKind
from buildish_site_pipeline.planning.types import (
    ResolvedPublicationPolicy,
    SelectedVersionContext,
)


def _context_owner_key(context: SelectedVersionContext) -> str:
    """Return the stable owner key segment for one selected version context."""

    return context.artifact_key or "component"


def target_id_for_context(context: SelectedVersionContext) -> str:
    """Return the stable route target identifier for one selected version context."""

    owner_key = _context_owner_key(context)
    if context.kind is RecordKind.DEVELOPMENT:
        return f"development:{context.component_slug}:{owner_key}"
    if context.kind is RecordKind.NAMED_REF:
        return f"named-ref:{context.component_slug}:{owner_key}:{context.named_ref_key}"
    if context.kind is RecordKind.LINE_HEAD:
        return f"line-head:{context.component_slug}:{owner_key}:{context.release_line}"
    if context.kind is RecordKind.CANDIDATE:
        return f"candidate:{context.component_slug}:{owner_key}:{context.version}"
    return f"released:{context.component_slug}:{owner_key}:{context.version}"


def stage_root_for_public_path(stage_kind: str, public_path: str) -> Path:
    """Return the renderer-facing stage root for one resolved public path."""

    relative_path = Path(public_path.strip("/"))
    return Path(stage_kind) / relative_path


def public_path_for_context(
    publication: ResolvedPublicationPolicy, context: SelectedVersionContext
) -> str:
    """Return the stable public route path for one selected version context."""

    if context.kind is RecordKind.DEVELOPMENT:
        return publication.development_path
    if context.kind is RecordKind.NAMED_REF:
        return f"{publication.docs_path}refs/{context.named_ref_key}/"
    if context.kind is RecordKind.LINE_HEAD:
        return f"{publication.docs_path}{context.release_line}/"
    if context.kind is RecordKind.CANDIDATE:
        return f"{publication.docs_path}candidates/{context.version}/"
    release_base_path = (
        publication.component_path
        if publication.docs_path == publication.development_path
        else publication.docs_path
    )
    return f"{release_base_path}releases/{context.version}/"
