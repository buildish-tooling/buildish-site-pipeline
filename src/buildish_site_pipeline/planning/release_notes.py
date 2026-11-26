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

"""Resolve release-notes pages for released contexts that stage original docs."""

from __future__ import annotations

from dataclasses import replace

from buildish_site_pipeline.models.enums import (
    ContextAction,
    RecordKind,
    ReleaseNotesTitleMode,
)
from buildish_site_pipeline.staging.publication_paths import can_share_context_route

from .component_names import component_display_name
from .types import (
    ReleaseNotesConflict,
    ReleaseNotesTarget,
    ResolvedComponentConfig,
    ResolvedSiteConfig,
    SelectedVersionContext,
    SelectedVersionSet,
)

_ContextKey = tuple[str, str | None, str | None]


def attach_release_notes_targets(
    *,
    site: ResolvedSiteConfig,
    selected: SelectedVersionSet,
    desired: tuple[SelectedVersionContext, ...],
) -> tuple[
    SelectedVersionSet,
    tuple[SelectedVersionContext, ...],
    tuple[ReleaseNotesConflict, ...],
]:
    """Attach one target per declaring docs context; conflicting shared routes get none.

    Runs after dispositions so omitted, notice and redirect contexts never get a
    target and their notes files are never read.
    """

    components = {component.slug: component for component in site.components}
    declaring = [
        (context, path)
        for context in selected.contexts
        if (path := _declared_notes_path(context)) is not None
    ]
    conflicts, conflicting = _shared_conflicts(
        components, [context for context, _ in declaring]
    )
    targets: dict[_ContextKey, ReleaseNotesTarget] = {}
    for context, relative_path in declaring:
        key = _key(context)
        if key in conflicting:
            continue
        targets[key] = ReleaseNotesTarget(
            releases_root=context.docs_root / "releases",
            relative_path=relative_path,
            segment=components[context.component_slug].publication.release_notes_segment,
            title=release_notes_title(components[context.component_slug], context),
        )
    if not targets:
        return selected, desired, conflicts

    def attach(context: SelectedVersionContext) -> SelectedVersionContext:
        target = targets.get(_key(context)) if context.kind is RecordKind.RELEASED else None
        return replace(context, release_notes=target) if target is not None else context

    return (
        replace(selected, contexts=tuple(attach(item) for item in selected.contexts)),
        tuple(attach(item) for item in desired),
        conflicts,
    )


def release_notes_title(
    component: ResolvedComponentConfig, context: SelectedVersionContext
) -> str:
    """Render the configured title; the display version falls back to the version."""

    record = context.provider_record
    version = (
        record.display_version if record is not None and record.display_version else None
    ) or str(context.version)
    mode = component.publication.release_notes_title
    if mode is ReleaseNotesTitleMode.VERSION_ONLY:
        return version
    if mode is ReleaseNotesTitleMode.COMPONENT_NAME:
        return f"{component_display_name(component) or component.slug} {version}"
    return f"Release Notes for {version}"


def _declared_notes_path(context: SelectedVersionContext) -> str | None:
    if (
        context.kind is not RecordKind.RELEASED
        or context.action is not ContextAction.DOCS
        or context.provider_record is None
    ):
        return None
    return context.provider_record.release_notes_path


def _shared_conflicts(
    components: dict[str, ResolvedComponentConfig],
    declaring: list[SelectedVersionContext],
) -> tuple[tuple[ReleaseNotesConflict, ...], frozenset[_ContextKey]]:
    conflicts: list[ReleaseNotesConflict] = []
    conflicting: set[_ContextKey] = set()
    for index, context in enumerate(declaring):
        if _key(context) in conflicting:
            continue
        routing = components[context.component_slug].publication.artifact_routing
        group = [context] + [
            other
            for other in declaring[index + 1 :]
            if can_share_context_route(routing, context, other)
        ]
        if len(group) < 2:
            continue
        conflicting.update(_key(item) for item in group)
        conflicts.append(
            ReleaseNotesConflict(
                component_slug=context.component_slug,
                version=str(context.version),
                artifact_keys=tuple(sorted(str(item.artifact_key) for item in group)),
            )
        )
    return tuple(conflicts), frozenset(conflicting)


def _key(context: SelectedVersionContext) -> _ContextKey:
    return (context.component_slug, context.artifact_key, context.version)
