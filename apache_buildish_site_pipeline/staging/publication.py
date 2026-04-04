# Copyright 2026 The Apache Software Foundation

"""Visible-stage publication and integrity checks."""

from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from apache_buildish_site_pipeline.cli_errors import RetainedStageError, StageIntegrityError


@dataclass(frozen=True, slots=True)
class StagePublicationResult:
    """Paths of one successfully published visible stage tree."""

    stage_root: Path
    manifest_path: Path


def finalize_stage_publication(
    *,
    candidate_stage_root: Path,
    stage_root: Path,
    allow_replace_existing: bool = False,
) -> StagePublicationResult:
    """Publish a previously materialized candidate stage tree atomically."""

    validate_visible_stage_target_path(stage_root)
    normalized_candidate_root = candidate_stage_root.resolve(strict=False)
    normalized_stage_root = stage_root.resolve(strict=False)
    _validate_candidate_stage_root(normalized_candidate_root)
    _validate_publication_filesystems(
        candidate_stage_root=normalized_candidate_root,
        stage_root=normalized_stage_root,
    )
    if allow_replace_existing:
        _validate_replaceable_stage_root(
            stage_root=normalized_stage_root,
            candidate_stage_root=normalized_candidate_root,
        )
        return _replace_stage_root(
            candidate_stage_root=normalized_candidate_root,
            stage_root=normalized_stage_root,
        )

    _validate_initial_stage_root(normalized_stage_root)
    if normalized_stage_root.exists():
        normalized_stage_root.rmdir()
    os.replace(normalized_candidate_root, normalized_stage_root)
    return StagePublicationResult(
        stage_root=normalized_stage_root,
        manifest_path=normalized_stage_root / "manifest.json",
    )


def validate_visible_stage_target_path(stage_root: Path) -> None:
    """Reject visible stage targets that resolve through symlinked parents."""

    absolute_stage_root = stage_root if stage_root.is_absolute() else stage_root.absolute()
    parent_path = absolute_stage_root.parent
    if _contains_symlink(parent_path):
        raise StageIntegrityError(f"Stage root parent directory resolves through a symlink: {parent_path}")
    if absolute_stage_root.exists() and absolute_stage_root.is_symlink():
        raise StageIntegrityError(f"Stage root must not be a symlink: {absolute_stage_root}")


def validate_materialized_stage_tree(stage_root: Path) -> None:
    """Reject staged trees that contain symlinked files or directories."""

    try:
        for root, dir_names, file_names in os.walk(stage_root, topdown=True, followlinks=False):
            root_path = Path(root)
            for name in (*dir_names, *file_names):
                entry_path = root_path / name
                if entry_path.is_symlink():
                    raise StageIntegrityError(f"Stage tree must not contain symlinks: {entry_path}")
    except OSError as exc:
        raise StageIntegrityError(f"Could not validate stage tree integrity for {stage_root}: {exc}") from exc


def _validate_initial_stage_root(stage_root: Path) -> None:
    if stage_root.exists() and stage_root.is_symlink():
        raise StageIntegrityError(f"Stage root must not be a symlink: {stage_root}")
    if stage_root.exists() and not stage_root.is_dir():
        raise StageIntegrityError(f"Stage root must be a directory: {stage_root}")
    if not stage_root.exists():
        return
    if any(stage_root.iterdir()):
        raise StageIntegrityError(
            f"Stage root must be absent or empty for the initial build implementation: {stage_root}",
        )


def _validate_replaceable_stage_root(*, stage_root: Path, candidate_stage_root: Path) -> None:
    if stage_root.exists() and stage_root.is_symlink():
        raise StageIntegrityError(f"Stage root must not be a symlink: {stage_root}")
    if stage_root.exists() and not stage_root.is_dir():
        raise StageIntegrityError(f"Stage root must be a directory: {stage_root}")
    if not stage_root.exists():
        return
    manifest_path = stage_root / "manifest.json"
    if not manifest_path.exists() or not manifest_path.is_file() or manifest_path.is_symlink():
        raise StageIntegrityError(f"Existing visible stage is not a trustworthy stage tree: {stage_root}")
    validate_materialized_stage_tree(stage_root)
    _validate_replacement_cleanup_scope(stage_root=stage_root, candidate_stage_root=candidate_stage_root)


def _validate_candidate_stage_root(stage_root: Path) -> None:
    if not stage_root.exists() or not stage_root.is_dir() or stage_root.is_symlink():
        raise StageIntegrityError(f"Candidate stage root is not a normal directory: {stage_root}")
    manifest_path = stage_root / "manifest.json"
    if not manifest_path.exists() or not manifest_path.is_file() or manifest_path.is_symlink():
        raise StageIntegrityError(f"Candidate stage root is missing manifest.json: {stage_root}")
    validate_materialized_stage_tree(stage_root)


def _validate_replacement_cleanup_scope(*, stage_root: Path, candidate_stage_root: Path) -> None:
    existing_entries = _collect_stage_tree_entries(stage_root)
    candidate_entries = _collect_stage_tree_entries(candidate_stage_root)
    extra_existing_paths = sorted(existing_entries.keys() - candidate_entries.keys())
    if extra_existing_paths:
        raise StageIntegrityError(
            "Visible stage replacement would delete paths with ambiguous ownership: " + ", ".join(extra_existing_paths[:5]),
        )
    changed_entry_types = sorted(
        path
        for path in existing_entries.keys() & candidate_entries.keys()
        if existing_entries[path] != candidate_entries[path]
    )
    if changed_entry_types:
        raise StageIntegrityError(
            "Visible stage replacement would change existing path types ambiguously: " + ", ".join(changed_entry_types[:5]),
        )


def _collect_stage_tree_entries(stage_root: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    try:
        for root, dir_names, file_names in os.walk(stage_root, topdown=True, followlinks=False):
            root_path = Path(root)
            relative_root = root_path.relative_to(stage_root)
            if relative_root != Path("."):
                entries[str(relative_root)] = "directory"
            for directory_name in dir_names:
                relative_path = (root_path / directory_name).relative_to(stage_root)
                entries[str(relative_path)] = "directory"
            for file_name in file_names:
                relative_path = (root_path / file_name).relative_to(stage_root)
                entries[str(relative_path)] = "file"
    except OSError as exc:
        raise StageIntegrityError(f"Could not inspect stage tree entries for {stage_root}: {exc}") from exc
    return entries


def _validate_publication_filesystems(*, candidate_stage_root: Path, stage_root: Path) -> None:
    stage_parent = stage_root.parent
    if not stage_parent.exists() or not stage_parent.is_dir():
        raise StageIntegrityError(f"Stage root parent directory does not exist: {stage_parent}")
    target_device = _stat_device_id(stage_parent)
    candidate_device = _stat_device_id(candidate_stage_root)
    if candidate_device != target_device:
        raise StageIntegrityError(
            "Candidate stage root and visible stage root must live on the same filesystem "
            f"for atomic publication: {candidate_stage_root} -> {stage_root}",
        )
    if stage_root.exists() and _stat_device_id(stage_root) != target_device:
        raise StageIntegrityError(
            "Existing stage root and its parent must live on the same filesystem "
            f"for safe replacement publication: {stage_root}",
        )


def _stat_device_id(path: Path) -> int:
    return path.stat().st_dev


def _contains_symlink(path: Path) -> bool:
    current = Path(path.anchor) if path.is_absolute() else Path()
    for part in path.parts:
        if current == Path(path.anchor) and part == path.anchor:
            continue
        current = current / part if current != Path() else Path(part)
        if current.exists() and current.is_symlink():
            return True
    return False


def _replace_stage_root(*, candidate_stage_root: Path, stage_root: Path) -> StagePublicationResult:
    parent_path = stage_root.parent
    parent_path.mkdir(parents=True, exist_ok=True)
    backup_root = Path(tempfile.mkdtemp(prefix=f".{stage_root.name}.backup.", dir=parent_path))
    shutil.rmtree(backup_root, ignore_errors=True)
    previous_stage_moved = False
    try:
        if stage_root.exists():
            os.replace(stage_root, backup_root)
            previous_stage_moved = True
        os.replace(candidate_stage_root, stage_root)
    except OSError as exc:
        if previous_stage_moved and backup_root.exists() and not stage_root.exists():
            try:
                os.replace(backup_root, stage_root)
            except OSError as rollback_exc:
                raise StageIntegrityError(
                    f"Could not finalize stage publication or roll back safely for {stage_root}: {rollback_exc}",
                ) from rollback_exc
            raise RetainedStageError(
                f"Could not finalize the newly materialized stage; retained the prior stage at {stage_root}",
            ) from exc
        raise StageIntegrityError(f"Could not finalize stage publication for {stage_root}: {exc}") from exc
    finally:
        if backup_root.exists():
            shutil.rmtree(backup_root, ignore_errors=True)
    return StagePublicationResult(
        stage_root=stage_root,
        manifest_path=stage_root / "manifest.json",
    )