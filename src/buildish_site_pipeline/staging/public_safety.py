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

"""Public-output sanitizers for stage data and stage-run reports."""

from __future__ import annotations

from pathlib import Path

from buildish_site_pipeline.models.emitted.planning_stage_contract import (
    PipelineDiagnosticEntry,
    ReducedDiagnosticDetailsSummary,
)

REDACTED_LOCAL_PATH = "[redacted-local-path]"
_LOCAL_DETAIL_FIELDS = frozenset(
    {
        "expectedlocalpath",
        "fragmentpath",
        "localpath",
        "manifestpath",
        "sourcepath",
        "stageroot",
        "stagerootpath",
        "workpath",
        "workroot",
        "workspacepath",
        "workspaceroot",
    },
)
_PUBLIC_ABSOLUTE_DETAIL_FIELDS = frozenset(
    {
        # These detail keys represent public route/path contracts rather than
        # machine-local filesystem locations. Keep this list intentionally small
        # and add a focused regression test whenever a new field is allowlisted.
        "canonicalpath",
        "frompath",
        "href",
        "mirrorpath",
        "path",
        "resolvedpath",
        "sourceroute",
    },
)


def sanitize_public_diagnostics(
    diagnostics: tuple[PipelineDiagnosticEntry, ...],
    *,
    workspace_root: Path,
    private_roots: tuple[Path, ...] = (),
) -> tuple[PipelineDiagnosticEntry, ...]:
    """Return diagnostics with machine-local path details sanitized for public output."""

    normalized_workspace_root = workspace_root.resolve(strict=False)
    normalized_private_roots = tuple(
        root.resolve(strict=False) for root in private_roots
    )
    return tuple(
        _sanitize_diagnostic(
            entry,
            workspace_root=normalized_workspace_root,
            private_roots=normalized_private_roots,
        )
        for entry in diagnostics
    )


def public_source_path(
    *, source_path: str | None, workspace_root: Path
) -> str | None:
    """Return a workspace-relative internal source path, or ``None`` if unsafe."""

    if source_path is None:
        return None
    raw_source_path = Path(source_path)
    if not raw_source_path.is_absolute():
        if raw_source_path == Path() or ".." in raw_source_path.parts:
            return None
        return raw_source_path.as_posix()
    normalized_workspace_root = workspace_root.resolve(strict=False)
    normalized_source_path = raw_source_path.resolve(strict=False)
    if not normalized_source_path.is_relative_to(normalized_workspace_root):
        return None
    return normalized_source_path.relative_to(normalized_workspace_root).as_posix()


def _sanitize_diagnostic(
    entry: PipelineDiagnosticEntry,
    *,
    workspace_root: Path,
    private_roots: tuple[Path, ...],
) -> PipelineDiagnosticEntry:
    if entry.details is None or isinstance(
        entry.details, ReducedDiagnosticDetailsSummary
    ):
        return entry
    return entry.model_copy(
        update={
            "details": _sanitize_detail_value(
                entry.details,
                field_name=None,
                workspace_root=workspace_root,
                private_roots=private_roots,
            ),
        },
    )


def _sanitize_detail_value(
    value: object,
    *,
    field_name: str | None,
    workspace_root: Path,
    private_roots: tuple[Path, ...],
) -> object:
    if isinstance(value, dict):
        return {
            key: _sanitize_detail_value(
                item,
                field_name=key,
                workspace_root=workspace_root,
                private_roots=private_roots,
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [
            _sanitize_detail_value(
                item,
                field_name=field_name,
                workspace_root=workspace_root,
                private_roots=private_roots,
            )
            for item in value
        ]
    if not isinstance(value, str):
        return value
    return _sanitize_detail_string(
        value,
        field_name=field_name,
        workspace_root=workspace_root,
        private_roots=private_roots,
    )


def _sanitize_detail_string(
    value: str,
    *,
    field_name: str | None,
    workspace_root: Path,
    private_roots: tuple[Path, ...],
) -> str:
    candidate_path = Path(value)
    if not candidate_path.is_absolute():
        return value
    normalized_candidate = candidate_path.resolve(strict=False)
    if _is_within_private_roots(normalized_candidate, private_roots):
        return REDACTED_LOCAL_PATH
    if normalized_candidate.is_relative_to(workspace_root):
        return normalized_candidate.relative_to(workspace_root).as_posix()
    if field_name is not None and field_name.lower() in _LOCAL_DETAIL_FIELDS:
        return REDACTED_LOCAL_PATH
    if field_name is not None and field_name.lower() in _PUBLIC_ABSOLUTE_DETAIL_FIELDS:
        return value
    return REDACTED_LOCAL_PATH


def _is_within_private_roots(path: Path, private_roots: tuple[Path, ...]) -> bool:
    return any(path == root or path.is_relative_to(root) for root in private_roots)
