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

from collections.abc import Iterable
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

    if context.artifact_key is not None:
        artifact_paths = next(
            (
                item
                for item in publication.artifact_publications
                if item.key == context.artifact_key
            ),
            None,
        )
        if artifact_paths is not None:
            return _context_path(
                artifact_paths.development_path,
                artifact_paths.docs_path,
                artifact_paths.release_base_path,
                context,
            )
        if (
            publication.artifact_publications
            or publication.artifact_routing == "namespaced"
        ):
            raise ValueError(
                f"Unknown artifact route: {context.component_slug}/{context.artifact_key}"
            )
    return _context_path(
        publication.development_path,
        publication.docs_path,
        publication.component_path
        if publication.docs_path == publication.development_path
        else publication.docs_path,
        context,
    )


def _context_path(
    development: str, docs: str, releases: str, context: SelectedVersionContext
) -> str:
    if context.kind is RecordKind.DEVELOPMENT:
        return development
    if context.kind is RecordKind.NAMED_REF:
        return f"{docs}refs/{context.named_ref_key}/"
    if context.kind is RecordKind.LINE_HEAD:
        return f"{docs}{context.release_line}/"
    if context.kind is RecordKind.CANDIDATE:
        return f"{docs}candidates/{context.version}/"
    return f"{releases}releases/{context.version}/"


def publishes_family_path(
    publication: ResolvedPublicationPolicy,
    contexts: Iterable[SelectedVersionContext],
    path: str,
) -> bool:
    """Do not turn a layout base into a phantom namespaced publication target."""
    if (
        publication.artifact_routing == "shared"
        or not publication.artifact_publications
    ):
        return True
    return publication.default_artifact is not None and any(
        context.artifact_key == publication.default_artifact
        and public_path_for_context(publication, context) == path
        for context in contexts
    )


def can_share_context_route(
    artifact_routing: str,
    first: SelectedVersionContext,
    second: SelectedVersionContext,
) -> bool:
    """Shared composition joins corresponding contexts of distinct artifacts only."""
    if (
        artifact_routing != "shared"
        or first.component_slug != second.component_slug
        or first.artifact_key == second.artifact_key
        or first.artifact_key is None
        or second.artifact_key is None
        or first.kind is not second.kind
        or first.action.value == "redirect"
        or second.action.value == "redirect"
    ):
        return False
    if first.kind is RecordKind.NAMED_REF:
        return first.named_ref_key == second.named_ref_key
    if first.kind is RecordKind.LINE_HEAD:
        return first.release_line == second.release_line
    if first.kind in {RecordKind.RELEASED, RecordKind.CANDIDATE}:
        return first.version == second.version
    return True
