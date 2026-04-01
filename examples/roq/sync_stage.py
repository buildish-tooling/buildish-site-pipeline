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

"""Synchronize one completed Site Pipeline stage into a Roq project.

Copy this file into the consumer-owned Roq project or adapt the same contract
to the consumer's build tool. The script uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from collections.abc import Sequence
from pathlib import Path, PurePosixPath
from typing import Any


_GENERATED_ROOTS = ("content", "data", "public")
_PAGE_EXTENSIONS = frozenset(
    {".adoc", ".asciidoc", ".htm", ".html", ".markdown", ".md", ".mdx"}
)
_STAGE_ROOT_MAPPINGS = (
    ("data", "data"),
    ("static", "public"),
)


class AdapterError(RuntimeError):
    """Report an unsafe or incompatible stage-to-Roq synchronization."""


def synchronize_stage(*, stage_root: Path, roq_root: Path) -> None:
    """Replace Roq's generated roots from one validated, completed stage.

    Page contents and metadata are copied byte-for-byte. Only renderer-facing
    paths are adapted: the pipeline-owned ``content/site`` prefix is removed,
    and page names of the form ``_index.<extension>`` become
    ``index.<extension>``.
    """

    try:
        _synchronize_stage(stage_root=stage_root, roq_root=roq_root)
    except AdapterError:
        raise
    except OSError as exc:
        raise AdapterError(f"stage synchronization failed: {exc}") from exc


def _synchronize_stage(*, stage_root: Path, roq_root: Path) -> None:
    stage_root = stage_root.absolute()
    roq_root = roq_root.absolute()
    stage_roots = _load_stage_roots(stage_root)
    _validate_roq_root(roq_root)
    for source_root in stage_roots.values():
        _assert_plain_tree(source_root)

    content_plan = _plan_roq_content(stage_roots["content"])
    _validate_generated_roots(roq_root)

    with tempfile.TemporaryDirectory(
        dir=roq_root, prefix=".site-pipeline-sync-"
    ) as tempdir:
        prepared_root = Path(tempdir)
        _prepare_content(
            content_plan=content_plan,
            destination_root=prepared_root / "content",
        )
        for stage_name, roq_name in _STAGE_ROOT_MAPPINGS:
            shutil.copytree(stage_roots[stage_name], prepared_root / roq_name)
        _publish_prepared_roots(prepared_root=prepared_root, roq_root=roq_root)


def _load_stage_roots(stage_root: Path) -> dict[str, Path]:
    if stage_root.is_symlink() or not stage_root.is_dir():
        raise AdapterError(f"stage root must be an ordinary directory: {stage_root}")

    manifest_path = stage_root / "manifest.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise AdapterError("synchronization requires a completed stage manifest")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AdapterError(f"cannot read stage manifest: {exc}") from exc
    if not isinstance(manifest, dict):
        raise AdapterError("stage manifest must be a JSON object")
    if manifest.get("stageLayoutVersion") != 1:
        raise AdapterError("reference adapter supports only stage layout version 1")

    roots = manifest.get("roots")
    if not isinstance(roots, dict):
        raise AdapterError("stage manifest does not declare its generated roots")
    result = {
        name: stage_root / _safe_manifest_path(roots.get(name), root_name=name)
        for name in ("content", "data", "static")
    }
    if len({path.relative_to(stage_root) for path in result.values()}) != len(result):
        raise AdapterError("stage manifest roots must be distinct")
    for path in result.values():
        _assert_no_symlink_components(stage_root=stage_root, path=path)
    return result


def _safe_manifest_path(value: Any, *, root_name: str) -> Path:
    if not isinstance(value, str) or not value:
        raise AdapterError(f"stage manifest root {root_name!r} must be a path string")
    if "\\" in value:
        raise AdapterError(
            f"stage manifest root {root_name!r} must use forward-slash paths"
        )
    relative_path = PurePosixPath(value)
    if (
        relative_path.is_absolute()
        or relative_path == PurePosixPath(".")
        or ".." in relative_path.parts
    ):
        raise AdapterError(f"stage manifest root {root_name!r} is not stage-relative")
    return Path(*relative_path.parts)


def _validate_roq_root(roq_root: Path) -> None:
    if roq_root.is_symlink() or not roq_root.is_dir():
        raise AdapterError(
            f"Roq project root must be an ordinary directory: {roq_root}"
        )


def _assert_plain_tree(root: Path) -> None:
    if root.is_symlink() or not root.is_dir():
        raise AdapterError(f"stage manifest root is not an ordinary directory: {root}")
    symlink = next((path for path in root.rglob("*") if path.is_symlink()), None)
    if symlink is not None:
        raise AdapterError(
            f"stage generated roots must not contain symlinks: {symlink}"
        )


def _assert_no_symlink_components(*, stage_root: Path, path: Path) -> None:
    current = stage_root
    for part in path.relative_to(stage_root).parts:
        current /= part
        if current.is_symlink():
            raise AdapterError(
                f"stage generated-root paths must not contain symlinks: {current}"
            )


def _validate_generated_roots(roq_root: Path) -> None:
    for root_name in _GENERATED_ROOTS:
        destination_root = roq_root / root_name
        if destination_root.is_symlink():
            raise AdapterError(
                f"Roq generated root must not be a symlink: {destination_root}"
            )
        if destination_root.exists() and not destination_root.is_dir():
            raise AdapterError(
                f"Roq generated root must be a directory: {destination_root}"
            )


def _plan_roq_content(content_root: Path) -> dict[Path, Path]:
    plan: dict[Path, Path] = {}
    collision_sources: dict[str, Path] = {}
    for source_path in sorted(
        (path for path in content_root.rglob("*") if path.is_file()),
        key=lambda path: path.as_posix(),
    ):
        relative_path = source_path.relative_to(content_root)
        if relative_path.parts[0] == "site":
            if len(relative_path.parts) == 1:
                raise AdapterError("staged content/site must be a directory")
            relative_path = Path(*relative_path.parts[1:])
        if (
            relative_path.stem == "_index"
            and relative_path.suffix.casefold() in _PAGE_EXTENSIONS
        ):
            relative_path = relative_path.with_name(f"index{relative_path.suffix}")

        collision_key = relative_path.as_posix().casefold()
        prior_source = collision_sources.get(collision_key)
        if prior_source is not None:
            raise AdapterError(
                "Roq content collision after adapting staged paths: "
                f"{prior_source} and {source_path} -> {relative_path}"
            )
        collision_sources[collision_key] = source_path
        plan[relative_path] = source_path
    return plan


def _prepare_content(*, content_plan: dict[Path, Path], destination_root: Path) -> None:
    destination_root.mkdir()
    for relative_path, source_path in content_plan.items():
        destination_path = destination_root / relative_path
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)


def _publish_prepared_roots(*, prepared_root: Path, roq_root: Path) -> None:
    backups: dict[str, Path | None] = {}
    published: list[str] = []
    try:
        for root_name in _GENERATED_ROOTS:
            destination_root = roq_root / root_name
            backup_root = roq_root / f"{prepared_root.name}-previous-{root_name}"
            if destination_root.exists():
                destination_root.replace(backup_root)
                backups[root_name] = backup_root
            else:
                backups[root_name] = None
            try:
                (prepared_root / root_name).replace(destination_root)
            except OSError:
                backup = backups[root_name]
                if backup is not None and backup.exists():
                    backup.replace(destination_root)
                raise
            published.append(root_name)
    except OSError as exc:
        rollback_failures = _rollback_published_roots(
            published=published, backups=backups, roq_root=roq_root
        )
        suffix = ""
        if rollback_failures:
            suffix = f"; rollback also failed for: {', '.join(rollback_failures)}"
        raise AdapterError(
            f"could not replace Roq generated roots: {exc}{suffix}"
        ) from exc
    for previous_root in backups.values():
        if previous_root is not None and previous_root.exists():
            shutil.rmtree(previous_root)


def _rollback_published_roots(
    *, published: list[str], backups: dict[str, Path | None], roq_root: Path
) -> list[str]:
    failures: list[str] = []
    for root_name in reversed(published):
        destination_root = roq_root / root_name
        backup_root = backups[root_name]
        try:
            if destination_root.exists():
                shutil.rmtree(destination_root)
            if backup_root is not None and backup_root.exists():
                backup_root.replace(destination_root)
        except OSError:
            failures.append(root_name)
    return failures


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Adapt one completed Site Pipeline stage for a Roq project."
    )
    parser.add_argument("stage_root", type=Path, help="completed stage root")
    parser.add_argument("roq_root", type=Path, help="consumer-owned Roq project root")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the copyable adapter command."""

    parser = _parser()
    arguments = parser.parse_args(argv)
    try:
        synchronize_stage(stage_root=arguments.stage_root, roq_root=arguments.roq_root)
    except AdapterError as exc:
        parser.exit(status=1, message=f"{parser.prog}: error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
