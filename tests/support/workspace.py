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

"""Shared workspace and fake watch-stream helpers for tests."""

from __future__ import annotations

import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def _workspace(*, with_content_file: bool = False):
    with tempfile.TemporaryDirectory() as tempdir:
        workspace_root = Path(tempdir)
        _write_workspace_inputs(workspace_root, with_content_file=with_content_file)
        yield workspace_root


def _write_workspace_inputs(workspace_root: Path, *, with_content_file: bool) -> None:
    (workspace_root / "site").mkdir(parents=True, exist_ok=True)
    (workspace_root / "site/components.yaml").write_text(
        """
schemaVersion: 1
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
  - slug: spark
    weight: 100
    content:
      source: runtime
    publication:
      mountPath: /spark/
    artifacts:
      - key: runtime
        source: runtime
        versioning:
          developmentRef: main
          tagPattern: ^v.*$
        publicationSelection:
          development: true
          lineHeads:
            mode: allAuthored
          releases:
            mode: latestPerLine
        lifecycle:
          releaseLines:
            - key: '4.0'
              maintenanceRef: maintenance/4.0
              latest: '4.0.0'
          releases:
            - version: '4.0.0'
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (workspace_root / "site/provider-snapshot.json").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "providers": [
                    {
                        "key": "github",
                        "type": "githubReleases",
                        "fetchedAt": "2026-04-03T00:00:00Z",
                    },
                ],
                "records": [
                    {
                        "provider": "github",
                        "kind": "development",
                        "componentSlug": "spark",
                        "artifactKey": "runtime",
                        "ref": "main",
                    },
                    {
                        "provider": "github",
                        "kind": "lineHead",
                        "componentSlug": "spark",
                        "artifactKey": "runtime",
                        "releaseLine": "4.0",
                        "ref": "maintenance/4.0",
                    },
                    {
                        "provider": "github",
                        "kind": "released",
                        "componentSlug": "spark",
                        "artifactKey": "runtime",
                        "version": "4.0.0",
                        "tag": "v4.0.0",
                    },
                ],
            },
        )
        + "\n",
        encoding="utf-8",
    )
    (workspace_root / "components/runtime/docs/maintenance/4.0").mkdir(parents=True, exist_ok=True)
    (workspace_root / "components/runtime/docs/releases/4.0.0").mkdir(parents=True, exist_ok=True)
    if with_content_file:
        (workspace_root / "components/runtime/docs/releases/4.0.0/index.md").write_text(
            "hello\n",
            encoding="utf-8",
        )


@contextmanager
def _cwd(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


class _FakeWatchEventStream:
    def __init__(self, responses: list[tuple[bool, object]]) -> None:
        self._responses = list(responses)

    def collect_dirty_paths(self, *, wait_for_first: bool):
        if not self._responses:
            raise AssertionError("watch test exhausted fake event-stream responses")
        expected_wait_for_first, response = self._responses.pop(0)
        if expected_wait_for_first is not wait_for_first:
            raise AssertionError(f"expected wait_for_first={expected_wait_for_first}, got {wait_for_first}")
        return response() if callable(response) else response

    def close(self) -> None:
        return None


def _fake_watch_event_stream_factory(
    *,
    responses: list[tuple[bool, object]],
    captured_watch_roots: list[tuple[Path, ...]] | None = None,
):
    @contextmanager
    def _factory(
        *,
        watch_roots: tuple[Path, ...],
        stage_root: Path,
        work_root: Path,
        report_output: Path | None,
        stop_event,
    ):
        del stage_root, work_root, report_output, stop_event
        if captured_watch_roots is not None:
            captured_watch_roots.append(watch_roots)
        yield _FakeWatchEventStream(list(responses))

    return _factory