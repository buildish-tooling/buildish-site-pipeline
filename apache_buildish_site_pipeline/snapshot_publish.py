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

"""Build uniquely versioned local wheel snapshots for the site-pipeline package."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import tempfile
import tomllib
from pathlib import Path

_VERSION_PATTERN = re.compile(r'^version = "[^"]+"$', re.MULTILINE)


def format_snapshot_version(
    base_version: str, *, built_at: dt.datetime, git_revision: str | None
) -> str:
    """Return a unique PEP 440 snapshot version for one local wheel build."""

    if built_at.tzinfo is None:
        raise ValueError("built_at must be timezone-aware")
    timestamp = built_at.astimezone(dt.UTC).strftime("%Y%m%d%H%M%S")
    normalized_revision = _normalize_git_revision(git_revision)
    local_label = f"g{normalized_revision}" if normalized_revision else "nogit"
    return f"{base_version}.dev{timestamp}+{local_label}"


def replace_project_version(pyproject_text: str, version: str) -> str:
    """Replace the first project version assignment in a ``pyproject.toml``."""

    updated_text, replacements = _VERSION_PATTERN.subn(
        f'version = "{version}"', pyproject_text, count=1
    )
    if replacements != 1:
        raise ValueError("expected exactly one project version assignment")
    return updated_text


def build_snapshot_wheel(repo_root: Path, out_dir: Path) -> Path:
    """Build one local snapshot wheel into ``out_dir`` and return its path."""

    pyproject_path = repo_root / "pyproject.toml"
    pyproject_text = pyproject_path.read_text(encoding="utf-8")
    base_version = tomllib.loads(pyproject_text)["project"]["version"]
    snapshot_version = format_snapshot_version(
        base_version,
        built_at=dt.datetime.now(dt.UTC),
        git_revision=_current_git_revision(repo_root),
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    existing_wheels = set(out_dir.glob("*.whl"))

    with tempfile.TemporaryDirectory() as temp_dir:
        source_root = Path(temp_dir) / "source"
        source_root.mkdir()
        (source_root / "pyproject.toml").write_text(
            replace_project_version(pyproject_text, snapshot_version),
            encoding="utf-8",
        )
        shutil.copy2(repo_root / "README.md", source_root / "README.md")
        shutil.copytree(
            repo_root / "apache_buildish_site_pipeline",
            source_root / "apache_buildish_site_pipeline",
        )
        subprocess.run(  # noqa: S603 - controlled local build command
            [_required_executable("uv"), "build", "--wheel", "--out-dir", str(out_dir)],
            cwd=source_root,
            check=True,
        )

    created_wheels = sorted(set(out_dir.glob("*.whl")) - existing_wheels)
    if len(created_wheels) != 1:
        raise RuntimeError(
            f"expected exactly one new wheel in {out_dir}, found {len(created_wheels)}"
        )

    wheel_path = created_wheels[0].resolve()
    manifest_path = out_dir / "latest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "package": "apache-buildish-site-pipeline",
                "version": snapshot_version,
                "wheel": wheel_path.name,
                "wheelPath": str(wheel_path),
                "fileUrl": wheel_path.as_uri(),
                "dependencySpec": f"apache-buildish-site-pipeline @ {wheel_path.as_uri()}",
                "publishedAt": dt.datetime.now(dt.UTC).isoformat(),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return wheel_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for local snapshot publication."""

    parser = argparse.ArgumentParser(
        description="Build a uniquely versioned local wheel snapshot for file-based consumption."
    )
    parser.add_argument(
        "--out-dir",
        default="dist/snapshots",
        help="Output directory for wheel snapshots and latest.json metadata",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Build one local snapshot wheel and print the resulting dependency hint."""

    args = parse_args(argv)
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = repo_root / out_dir
    wheel_path = build_snapshot_wheel(repo_root, out_dir.resolve())
    print(f"Built local snapshot wheel: {wheel_path}")
    print(f"Dependency spec: apache-buildish-site-pipeline @ {wheel_path.as_uri()}")
    print(f"Snapshot metadata: {out_dir / 'latest.json'}")
    return 0


def _current_git_revision(repo_root: Path) -> str | None:
    """Return the current short Git revision when available."""

    completed = subprocess.run(  # noqa: S603 - controlled local git query
        [_required_executable("git"), "rev-parse", "--short=12", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def _normalize_git_revision(value: str | None) -> str | None:
    """Normalize a Git revision for use in a local-version label."""

    if value is None:
        return None
    normalized = re.sub(r"[^0-9a-z]+", "", value.strip().lower())
    return normalized[:12] or None


def _required_executable(name: str) -> str:
    """Resolve one required executable from PATH."""

    executable = shutil.which(name)
    if executable is None:
        raise FileNotFoundError(f"Required executable not found on PATH: {name}")
    return executable


if __name__ == "__main__":
    raise SystemExit(main())