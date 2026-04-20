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

"""Build uniquely versioned local wheel snapshots and write a consumer manifest.

This module exists because the project keeps a normal, static release version in
``pyproject.toml`` for reproducible source and wheel builds, but local snapshot
publishing needs a different shape:

* every snapshot wheel should have a unique PEP 440 version,
* the working tree should not be edited just to cut that local snapshot,
* the produced wheel should live in a stable output directory, and
* downstream automation needs a machine-readable pointer to the latest build.

The implementation therefore stages a temporary copy of the repository,
rewrites only the version in that temporary copy to
``<base-version>+snapshot.<utc-timestamp>``, builds a wheel from the copy, and
then writes ``latest.json`` with the resulting wheel path and dependency
specifier.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

_IGNORED_COPY_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
}
_IGNORED_COPY_FILES = {".coverage"}


def publish_snapshot(*, out_dir: Path, project_dir: Path) -> tuple[Path, Path]:
    """Build one uniquely versioned wheel snapshot plus ``latest.json``.

    The source tree under ``project_dir`` is treated as read-only. All mutable
    work happens in a temporary copy so local developer state and the checked-in
    ``pyproject.toml`` stay untouched.
    """

    resolved_project_dir = project_dir.resolve()
    resolved_out_dir = out_dir.resolve()
    resolved_out_dir.mkdir(parents=True, exist_ok=True)
    existing_wheels = {path.resolve() for path in resolved_out_dir.glob("*.whl")}

    # The project version is intentionally stored as a simple literal in
    # ``pyproject.toml``. Snapshot publishing derives a one-off build version
    # from that base release line.
    base_version = _read_project_version(resolved_project_dir / "pyproject.toml")
    snapshot_version = f"{base_version}+snapshot.{_timestamp_token()}"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_project_dir = Path(temp_dir) / resolved_project_dir.name
        # Build from a throwaway copy so the working tree does not get rewritten
        # or dirtied just to stamp a local snapshot version.
        shutil.copytree(
            resolved_project_dir,
            temp_project_dir,
            ignore=shutil.ignore_patterns(*_IGNORED_COPY_DIRS, *_IGNORED_COPY_FILES),
        )
        # Only the version changes. Everything else in the staged project stays
        # byte-for-byte aligned with the source checkout.
        _rewrite_project_version(
            pyproject_path=temp_project_dir / "pyproject.toml",
            new_version=snapshot_version,
        )
        # ``uv build`` writes the finished wheel directly into the caller's
        # requested output directory so there is no second artifact-copy step.
        subprocess.run(
            ["uv", "build", "--wheel", "--out-dir", str(resolved_out_dir)],
            check=True,
            cwd=temp_project_dir,
        )

    # The output directory may already contain older snapshots, so detect the
    # exact wheel created by this invocation before writing the manifest.
    wheel_path = _newly_built_wheel(
        out_dir=resolved_out_dir,
        previous_wheels=existing_wheels,
    )
    manifest_path = resolved_out_dir / "latest.json"
    manifest = {
        "name": "apache-buildish-site-pipeline",
        "version": snapshot_version,
        "wheel": wheel_path.name,
        "wheelPath": wheel_path.as_posix(),
        "dependencySpec": (
            f"apache-buildish-site-pipeline @ {wheel_path.resolve().as_uri()}"
        ),
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return wheel_path, manifest_path


def _read_project_version(pyproject_path: Path) -> str:
    """Read the literal ``[project].version`` value from ``pyproject.toml``.

    A focused line-based parser is sufficient here because this project stores a
    static version string and snapshot publishing needs only that single field.
    Avoiding a full TOML round-trip keeps the rewrite logic simple and preserves
    the file's existing formatting in the temporary copy.
    """

    in_project_table = False
    for raw_line in pyproject_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_project_table = stripped == "[project]"
            continue
        if in_project_table and stripped.startswith("version = "):
            quote = '"'
            _, _, remainder = stripped.partition("=")
            version_text = remainder.strip().strip(quote)
            if version_text:
                return version_text
    raise ValueError(f"Could not find [project] version in {pyproject_path}")


def _rewrite_project_version(*, pyproject_path: Path, new_version: str) -> None:
    """Rewrite only the ``[project].version`` line in a temporary project copy."""

    lines = pyproject_path.read_text(encoding="utf-8").splitlines()
    rewritten: list[str] = []
    in_project_table = False
    replaced = False
    for raw_line in lines:
        stripped = raw_line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_project_table = stripped == "[project]"
            rewritten.append(raw_line)
            continue
        if in_project_table and stripped.startswith("version = ") and not replaced:
            indentation = raw_line[: len(raw_line) - len(raw_line.lstrip())]
            rewritten.append(f'{indentation}version = "{new_version}"')
            replaced = True
            continue
        rewritten.append(raw_line)
    if not replaced:
        raise ValueError(f"Could not rewrite [project] version in {pyproject_path}")
    pyproject_path.write_text("\n".join(rewritten) + "\n", encoding="utf-8")


def _timestamp_token() -> str:
    """Return a UTC timestamp token suitable for local snapshot versions."""

    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")


def _newly_built_wheel(*, out_dir: Path, previous_wheels: set[Path]) -> Path:
    """Return the single wheel created by the current snapshot build."""

    candidates = sorted(
        path.resolve()
        for path in out_dir.glob("*.whl")
        if path.resolve() not in previous_wheels
    )
    if not candidates:
        raise FileNotFoundError(
            f"No newly built wheel was produced under {out_dir}"
        )
    if len(candidates) != 1:
        raise ValueError(
            f"Expected exactly one newly built wheel under {out_dir}, found {len(candidates)}"
        )
    return candidates[-1]


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for manual snapshot publishing."""

    parser = argparse.ArgumentParser(
        prog="python -m tools.helpers.snapshot_publish"
    )
    parser.add_argument(
        "--out-dir",
        default="dist/snapshots",
        help="Directory that should receive the snapshot wheel and latest.json manifest.",
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Repository root that contains pyproject.toml and the wheel legal files.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point used by ``make publish-snapshot-local`` and ad hoc runs."""

    args = _build_parser().parse_args(argv)
    wheel_path, manifest_path = publish_snapshot(
        out_dir=Path(args.out_dir),
        project_dir=Path(args.project_dir),
    )
    sys.stdout.write(f"{wheel_path.as_posix()}\n")  # noqa: TID251
    sys.stdout.write(f"{manifest_path.as_posix()}\n")  # noqa: TID251
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
