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

"""Verify curated licenses and smoke-test the CLI inside the built image."""

from __future__ import annotations

from collections.abc import Callable
import difflib
import logging
from pathlib import Path
import re
import shutil
import subprocess
import sysconfig
import tempfile
from urllib.request import urlopen

from buildish_site_pipeline.legal.container_inventory import (
    collect_container_base_image_entries,
)

_LOG = logging.getLogger(__name__)


def fetch_uv_license(version: str, filename: str) -> str:
    """Fetch a legal text from the uv release selected by the Containerfile."""

    if re.fullmatch(r"0\.\d+\.\d+", version) is None or filename not in {
        "LICENSE-APACHE",
        "LICENSE-MIT",
    }:
        raise ValueError("Unsupported uv release or license filename")
    url = f"https://raw.githubusercontent.com/astral-sh/uv/{version}/{filename}"
    with urlopen(url, timeout=30) as response:  # noqa: S310 -- fixed HTTPS source
        return response.read().decode("utf-8")


def verify_licenses(
    project_dir: Path,
    python_license_path: Path,
    fetch_uv: Callable[[str, str], str] = fetch_uv_license,
) -> None:
    """Fail with a reviewable diff when the curated legal texts have changed.

    Python's text comes from the running image. uv's scratch image contains no
    legal texts, so compare against the source release matching its pinned tag.
    """

    differences: list[str] = []
    for entry in collect_container_base_image_entries(project_dir):
        for license_file in entry.license_files:
            if entry.name == "python":
                upstream = python_license_path.read_text(encoding="utf-8")
            elif entry.name == "uv":
                filename = (
                    "LICENSE-APACHE"
                    if license_file.original_relative_path == "LICENSE"
                    else license_file.original_relative_path
                )
                upstream = fetch_uv(entry.version, filename)
            else:
                raise RuntimeError(
                    f"No upstream license check for {entry.source_reference}"
                )
            differences.extend(
                difflib.unified_diff(
                    license_file.text.splitlines(keepends=True),
                    (upstream.rstrip("\n") + "\n").splitlines(keepends=True),
                    fromfile=license_file.installed_path,
                    tofile=f"{entry.source_reference}/{license_file.original_relative_path}",
                )
            )
    if differences:
        raise RuntimeError(
            "Curated base-image legal texts changed; review and update the copies:\n"
            + "".join(differences)
        )


def smoke_test() -> None:
    """Exercise the installed entrypoint and stage a small local workspace."""

    executable = shutil.which("site-pipeline")
    if executable is None:
        raise RuntimeError("The installed site-pipeline entrypoint is missing")
    subprocess.run(  # noqa: S603 -- installed CLI
        [executable, "--help"], check=True, timeout=60
    )
    with tempfile.TemporaryDirectory(prefix="site-pipeline-smoke-") as temp_dir:
        workspace = Path(temp_dir)
        (workspace / "site").mkdir()
        docs = workspace / "components/runtime/docs/releases/4.0.0"
        docs.mkdir(parents=True)
        (docs / "index.md").write_text(
            "---\ntitle: Container smoke test\n---\n\nHello from the container.\n",
            encoding="utf-8",
        )
        (workspace / "site/catalog.yaml").write_text(
            """schemaVersion: 1
defaults:
  docsRoot: docs
  publication:
    origin: docs
site: {}
origins:
  docs:
    baseUrl: https://docs.example.org
sources:
  runtime:
    localDir: components/runtime
components:
  - slug: smoke
    content:
      source: runtime
    publication:
      mountPath: /smoke/
    artifacts:
      - key: runtime
        source: runtime
        versioning:
          developmentRef: main
          tagPattern: ^v.*$
""",
            encoding="utf-8",
        )
        (workspace / "site/provider-snapshot.json").write_text(
            """{
  "schemaVersion": 1,
  "providers": [{"key": "github", "type": "githubReleases", "fetchedAt": "2026-04-03T00:00:00Z"}],
  "records": [
    {"provider": "github", "kind": "development", "componentSlug": "smoke", "artifactKey": "runtime", "ref": "main"},
    {"provider": "github", "kind": "released", "componentSlug": "smoke", "artifactKey": "runtime", "version": "4.0.0", "tag": "v4.0.0"}
  ]
}
""",
            encoding="utf-8",
        )
        for command in ("check", "build"):
            subprocess.run(  # noqa: S603 -- installed CLI and local smoke fixture
                [executable, command, "--workspace-root", str(workspace)],
                check=True,
                timeout=60,
            )
        pages = (workspace / "site/.stage").rglob("*.md")
        if not any(
            "Hello from the container." in page.read_text(encoding="utf-8")
            for page in pages
        ):
            raise RuntimeError("Container smoke test did not stage the authored page")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    project_dir = Path(__file__).resolve().parents[2]
    try:
        verify_licenses(
            project_dir,
            Path(sysconfig.get_path("stdlib")) / "LICENSE.txt",
        )
        smoke_test()
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        _LOG.error("%s", exc)
        raise SystemExit(1) from exc
    _LOG.info("Verified base-image legal texts and installed CLI")


if __name__ == "__main__":
    main()
