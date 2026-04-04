# Copyright 2026 The Apache Software Foundation

"""Small publication-path helpers reused by staging without evaluation imports."""

from __future__ import annotations

from apache_buildish_site_pipeline.models.enums import RecordKind
from apache_buildish_site_pipeline.planning.types import ResolvedPublicationPolicy, SelectedVersionContext


def target_id_for_context(context: SelectedVersionContext) -> str:
    """Return the stable route target identifier for one selected version context."""

    if context.kind is RecordKind.DEVELOPMENT:
        return f"development:{context.component_slug}:{context.artifact_key}"
    if context.kind is RecordKind.NAMED_REF:
        return f"named-ref:{context.component_slug}:{context.artifact_key}:{context.named_ref_key}"
    if context.kind is RecordKind.LINE_HEAD:
        return f"line-head:{context.component_slug}:{context.artifact_key}:{context.release_line}"
    if context.kind is RecordKind.CANDIDATE:
        return f"candidate:{context.component_slug}:{context.artifact_key}:{context.version}"
    return f"released:{context.component_slug}:{context.artifact_key}:{context.version}"


def public_path_for_context(publication: ResolvedPublicationPolicy, context: SelectedVersionContext) -> str:
    """Return the stable public route path for one selected version context."""

    if context.kind is RecordKind.DEVELOPMENT:
        return publication.development_path
    if context.kind is RecordKind.NAMED_REF:
        return f"{publication.docs_path}refs/{context.named_ref_key}/"
    if context.kind is RecordKind.LINE_HEAD:
        return f"{publication.docs_path}{context.release_line}/"
    if context.kind is RecordKind.CANDIDATE:
        return f"{publication.docs_path}candidates/{context.version}/"
    return f"{publication.docs_path}releases/{context.version}/"