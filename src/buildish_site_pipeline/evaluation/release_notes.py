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

"""Plan-time validation of release-notes files selected by provider records."""

from __future__ import annotations

import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from buildish_site_pipeline.models.enums import DiagnosticSeverity
from buildish_site_pipeline.planning.types import (
    PlanningEvaluation,
    ReleaseNotesTarget,
    SelectedVersionContext,
)

from . import diagnostic_codes
from .collector import DiagnosticCollector
from .types import ReleaseNotesInventory, ValidatedReleaseNotes


def validate_release_notes(
    planning: PlanningEvaluation, collector: DiagnosticCollector
) -> ReleaseNotesInventory:
    """Check every staged notes file once and keep the accepted text for later phases."""

    for conflict in planning.release_notes_conflicts:
        collector.add(
            severity=DiagnosticSeverity.ERROR,
            code=diagnostic_codes.RELEASE_NOTES_SHARED_CONFLICT,
            component_slug=conflict.component_slug,
            target_id=conflict.version,
            message=(
                f"Release {conflict.version} declares release notes on several artifacts "
                f"sharing one route: {', '.join(conflict.artifact_keys)}"
            ),
            details={"artifactKeys": list(conflict.artifact_keys)},
        )
    targets = [
        (context, context.release_notes)
        for context in planning.selected_versions.contexts
        if context.release_notes is not None
    ]
    if not targets:
        return ReleaseNotesInventory()
    _validate_segments(planning, {context.component_slug for context, _ in targets}, collector)
    version_directories = _version_directories(planning)
    accepted: list[ValidatedReleaseNotes] = []
    for context, target in targets:
        problem = _path_problem(
            target, version_directories.get(target.releases_root, frozenset())
        )
        if problem is not None:
            _report(collector, context, target, diagnostic_codes.RELEASE_NOTES_PATH_INVALID, problem)
            continue
        try:
            mode = target.source_path.lstat().st_mode
        except FileNotFoundError:
            collector.add(
                severity=DiagnosticSeverity.ERROR,
                code=diagnostic_codes.INPUT_MISSING,
                component_slug=context.component_slug,
                artifact_key=context.artifact_key,
                target_id=context.version,
                message=f"Release notes for {context.version} are missing",
                details={"expectedLocalPath": str(target.source_path), "reason": "missing"},
            )
            continue
        if not stat.S_ISREG(mode):
            _report(collector, context, target, diagnostic_codes.RELEASE_NOTES_PATH_INVALID, "is not a regular file")
            continue
        text = _read_text(target.source_path)
        if isinstance(text, _Problem):
            _report(collector, context, target, diagnostic_codes.RELEASE_NOTES_CONTENT_INVALID, text.reason)
            continue
        accepted.append(ValidatedReleaseNotes(context=context, target=target, text=text))
    return ReleaseNotesInventory(items=tuple(accepted))


def _content_problem(text: str) -> str | None:
    """Return why decoded text cannot become a notes page body, if it cannot."""

    if "\x00" in text:
        return "contains NUL characters"
    if not text.strip():
        return "is empty"
    if text.splitlines()[0] == "---":
        return "starts with a front-matter block or '---' line; the pipeline owns page metadata"
    return None


@dataclass(frozen=True, slots=True)
class _Problem:
    reason: str


def _read_text(path: Path) -> str | _Problem:
    try:
        text = path.read_bytes().decode("utf-8")
    except UnicodeDecodeError:
        return _Problem("is not valid UTF-8")
    except OSError as exc:
        return _Problem(f"cannot be read: {exc.strerror or exc}")
    problem = _content_problem(text)
    return _Problem(problem) if problem is not None else text


def _path_problem(target: ReleaseNotesTarget, versions: frozenset[str]) -> str | None:
    relative = PurePosixPath(target.relative_path)
    if relative.parts[0] in versions:
        return f"is inside the version directory {relative.parts[0]!r}"
    current = target.releases_root
    # Only segments below releases/ are checked: workspaces may live under symlinked parents.
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return "passes through a symlink"
    resolved = target.source_path.resolve(strict=False)
    if not resolved.is_relative_to(target.releases_root.resolve(strict=False)):
        return "resolves outside the artifact's releases directory"
    return None


def _version_directories(planning: PlanningEvaluation) -> dict[Path, frozenset[str]]:
    """Map each `<docsRoot>/releases/` to every version directory name it may stage."""

    versions: dict[Path, set[str]] = {}
    for component in planning.site.components:
        for artifact in component.artifacts:
            names = versions.setdefault(artifact.docs_root / "releases", set())
            index = planning.provider_index.contexts_by_artifact.get((component.slug, artifact.key))
            if index is not None:
                names.update(index.released_by_version)
            if artifact.lifecycle is not None:
                names.update(item.version for item in artifact.lifecycle.releases or ())
    for context in planning.desired_versions or planning.selected_versions.contexts:
        if context.version is not None:
            versions.setdefault(context.docs_root / "releases", set()).add(context.version)
    return {root: frozenset(names) for root, names in versions.items()}


def _validate_segments(
    planning: PlanningEvaluation,
    slugs: set[str],
    collector: DiagnosticCollector,
) -> None:
    for component in planning.site.components:
        if component.slug not in slugs:
            continue
        segment = component.publication.release_notes_segment
        if segment in (component.localization.supported_locales or ()):
            collector.add(
                severity=DiagnosticSeverity.ERROR,
                code=diagnostic_codes.RELEASE_NOTES_SEGMENT_INVALID,
                component_slug=component.slug,
                message=f"Release-notes segment {segment!r} equals a supported locale",
                details={"segment": segment},
            )


def _report(
    collector: DiagnosticCollector,
    context: SelectedVersionContext,
    target: ReleaseNotesTarget,
    code: str,
    problem: str,
) -> None:
    collector.add(
        severity=DiagnosticSeverity.ERROR,
        code=code,
        component_slug=context.component_slug,
        artifact_key=context.artifact_key,
        target_id=context.version,
        message=f"Release notes {target.relative_path!r} for {context.version} {problem}",
        details={"path": target.relative_path},
    )
