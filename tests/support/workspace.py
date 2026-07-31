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

"""Shared workspace and fake watch-stream helpers for tests."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def _workspace(*, with_content_file: bool = False, topology: str = "default"):
    with tempfile.TemporaryDirectory() as tempdir:
        workspace_root = Path(tempdir)
        _write_workspace_inputs(
            workspace_root,
            with_content_file=with_content_file,
            topology=topology,
        )
        yield workspace_root


def _write_workspace_inputs(
    workspace_root: Path, *, with_content_file: bool, topology: str
) -> None:
    if topology == "default":
        _write_default_workspace_inputs(workspace_root, with_content_file=with_content_file)
        return
    if topology == "component_only_development":
        _write_component_only_development_workspace_inputs(
            workspace_root,
            with_content_file=with_content_file,
        )
        return
    if topology == "two_artifacts":
        _write_two_artifact_workspace_inputs(workspace_root, with_content_file=with_content_file)
        return
    if topology == "rich_lifecycle":
        _write_rich_lifecycle_workspace_inputs(workspace_root, with_content_file=with_content_file)
        return
    if topology == "grouped_large":
        _write_grouped_large_workspace_inputs(workspace_root, with_content_file=with_content_file)
        return
    raise AssertionError(f"Unknown test workspace topology: {topology}")


def _write_default_workspace_inputs(workspace_root: Path, *, with_content_file: bool) -> None:
    (workspace_root / "site").mkdir(parents=True, exist_ok=True)
    (workspace_root / "site/catalog.yaml").write_text(
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
    repository: https://github.com/example/runtime
    defaultBranch: main
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


def _write_component_only_development_workspace_inputs(
    workspace_root: Path, *, with_content_file: bool
) -> None:
    (workspace_root / "site").mkdir(parents=True, exist_ok=True)
    (workspace_root / "site/catalog.yaml").write_text(
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
  site-pipeline:
    localDir: components/site-pipeline
components:
  - slug: site-pipeline
    content:
      source: site-pipeline
    publication:
      mountPath: /components/site-pipeline/
      developmentPath: /components/site-pipeline/development/
      docsPath: /components/site-pipeline/development/
    artifacts: []
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (workspace_root / "site/provider-snapshot.json").write_text(
        json.dumps({"schemaVersion": 1, "providers": [], "records": []}) + "\n",
        encoding="utf-8",
    )
    (workspace_root / "components/site-pipeline/docs").mkdir(parents=True, exist_ok=True)
    if with_content_file:
        (workspace_root / "components/site-pipeline/docs/index.md").write_text(
            "component development\n",
            encoding="utf-8",
        )


def _write_two_artifact_workspace_inputs(
    workspace_root: Path, *, with_content_file: bool
) -> None:
    (workspace_root / "site").mkdir(parents=True, exist_ok=True)
    (workspace_root / "site/catalog.yaml").write_text(
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
  api:
    localDir: components/api
components:
  - slug: spark
    content:
      source: runtime
    publication:
      mountPath: /spark/
    artifacts:
      - key: runtime
        source: runtime
        docsRoot: docs/runtime
        versioning:
          developmentRef: main
          tagPattern: ^v.*$
        publicationSelection:
          development: true
          releases:
            mode: latestPerLine
        lifecycle:
          releaseLines:
            - key: '4.0'
              maintenanceRef: maintenance/4.0
              latest: '4.0.0'
          releases:
            - version: '4.0.0'
      - key: api
        source: api
        docsRoot: docs
        versioning:
          developmentRef: main
          tagPattern: ^api-v.*$
        publicationSelection:
          development: true
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
                        "kind": "released",
                        "componentSlug": "spark",
                        "artifactKey": "runtime",
                        "version": "4.0.0",
                        "tag": "v4.0.0",
                    },
                    {
                        "provider": "github",
                        "kind": "development",
                        "componentSlug": "spark",
                        "artifactKey": "api",
                        "ref": "main",
                    },
                    {
                        "provider": "github",
                        "kind": "released",
                        "componentSlug": "spark",
                        "artifactKey": "api",
                        "version": "4.0.0",
                        "tag": "api-v4.0.0",
                    },
                ],
            },
        )
        + "\n",
        encoding="utf-8",
    )
    (workspace_root / "components/runtime/docs/runtime/releases/4.0.0/guide").mkdir(
        parents=True,
        exist_ok=True,
    )
    (workspace_root / "components/api/docs/releases/4.0.0/reference").mkdir(
        parents=True,
        exist_ok=True,
    )
    if with_content_file:
        (workspace_root / "components/runtime/docs/runtime/guide").mkdir(
            parents=True,
            exist_ok=True,
        )
        (workspace_root / "components/api/docs/reference").mkdir(
            parents=True,
            exist_ok=True,
        )
        (workspace_root / "components/runtime/docs/runtime/guide/index.md").write_text(
            "runtime development guide\n",
            encoding="utf-8",
        )
        (workspace_root / "components/runtime/docs/runtime/releases/4.0.0/guide/index.md").write_text(
            "runtime release guide\n",
            encoding="utf-8",
        )
        (workspace_root / "components/api/docs/reference/index.md").write_text(
            "api development reference\n",
            encoding="utf-8",
        )
        (workspace_root / "components/api/docs/releases/4.0.0/reference/index.md").write_text(
            "api release reference\n",
            encoding="utf-8",
        )


def _write_rich_lifecycle_workspace_inputs(
    workspace_root: Path, *, with_content_file: bool
) -> None:
    (workspace_root / "site").mkdir(parents=True, exist_ok=True)
    (workspace_root / "site/catalog.yaml").write_text(
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
          candidates:
            mode: latest
        lifecycle:
          releaseLines:
            - key: '4.1'
              maintenanceRef: maintenance/4.1
              latest: '4.1.0'
            - key: '4.0'
              maintenanceRef: maintenance/4.0
              latest: '4.0.2'
          releases:
            - version: '4.1.0'
            - version: '4.0.2'
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
                        "releaseLine": "4.1",
                        "ref": "maintenance/4.1",
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
                        "version": "4.1.0",
                        "tag": "v4.1.0",
                    },
                    {
                        "provider": "github",
                        "kind": "released",
                        "componentSlug": "spark",
                        "artifactKey": "runtime",
                        "version": "4.0.2",
                        "tag": "v4.0.2",
                    },
                    {
                        "provider": "github",
                        "kind": "candidate",
                        "componentSlug": "spark",
                        "artifactKey": "runtime",
                        "version": "4.2.0-rc1",
                        "tag": "v4.2.0-rc1",
                        "candidateSequence": 1,
                    },
                    {
                        "provider": "github",
                        "kind": "candidate",
                        "componentSlug": "spark",
                        "artifactKey": "runtime",
                        "version": "4.2.0-rc2",
                        "tag": "v4.2.0-rc2",
                        "candidateSequence": 2,
                    },
                ],
            },
        )
        + "\n",
        encoding="utf-8",
    )
    (workspace_root / "components/runtime/docs/maintenance/4.1").mkdir(
        parents=True,
        exist_ok=True,
    )
    (workspace_root / "components/runtime/docs/maintenance/4.0").mkdir(
        parents=True,
        exist_ok=True,
    )
    (workspace_root / "components/runtime/docs/releases/4.1.0").mkdir(
        parents=True,
        exist_ok=True,
    )
    (workspace_root / "components/runtime/docs/releases/4.0.2").mkdir(
        parents=True,
        exist_ok=True,
    )
    (workspace_root / "components/runtime/docs/candidates/4.2.0-rc1").mkdir(
        parents=True,
        exist_ok=True,
    )
    (workspace_root / "components/runtime/docs/candidates/4.2.0-rc2").mkdir(
        parents=True,
        exist_ok=True,
    )
    if with_content_file:
        (workspace_root / "components/runtime/docs/index.md").write_text(
            "development docs\n",
            encoding="utf-8",
        )
        (workspace_root / "components/runtime/docs/maintenance/4.1/index.md").write_text(
            "maintenance 4.1\n",
            encoding="utf-8",
        )
        (workspace_root / "components/runtime/docs/maintenance/4.0/index.md").write_text(
            "maintenance 4.0\n",
            encoding="utf-8",
        )
        (workspace_root / "components/runtime/docs/releases/4.1.0/index.md").write_text(
            "release 4.1.0\n",
            encoding="utf-8",
        )
        (workspace_root / "components/runtime/docs/releases/4.0.2/index.md").write_text(
            "release 4.0.2\n",
            encoding="utf-8",
        )
        (workspace_root / "components/runtime/docs/candidates/4.2.0-rc1/index.md").write_text(
            "candidate 4.2.0-rc1\n",
            encoding="utf-8",
        )
        (workspace_root / "components/runtime/docs/candidates/4.2.0-rc2/index.md").write_text(
            "candidate 4.2.0-rc2\n",
            encoding="utf-8",
        )


def _write_grouped_large_workspace_inputs(
    workspace_root: Path, *, with_content_file: bool
) -> None:
    (workspace_root / "site").mkdir(parents=True, exist_ok=True)
    (workspace_root / "site/catalog.yaml").write_text(
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
  spark:
    localDir: components/spark
  operator:
    localDir: components/operator
groups:
  streaming:
    displayName: Streaming
    pathPrefix: /platform/
components:
  - slug: spark
    group: streaming
    content:
      source: spark
    publication:
      pathSegment: spark
    compatibility:
      - subjectRef: component:spark
        targetRef: component:spark-operator
        relation: testedWith
        notes: Spark runtime docs assume the matching operator line.
    artifacts:
      - key: runtime
        source: spark
        versioning:
          developmentRef: main
          tagPattern: ^v.*$
        publicationSelection:
          development: true
          releases:
            mode: latestPerLine
        lifecycle:
          releaseLines:
            - key: '4.0'
              maintenanceRef: maintenance/4.0
              latest: '4.0.0'
          releases:
            - version: '4.0.0'
  - slug: spark-operator
    group: streaming
    content:
      source: operator
    publication:
      pathSegment: spark-operator
    artifacts:
      - key: operator
        source: operator
        versioning:
          developmentRef: main
          tagPattern: ^operator-v.*$
        publicationSelection:
          development: true
          releases:
            mode: latestPerLine
        lifecycle:
          releaseLines:
            - key: '1.2'
              maintenanceRef: maintenance/1.2
              latest: '1.2.0'
          releases:
            - version: '1.2.0'
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
                        "kind": "released",
                        "componentSlug": "spark",
                        "artifactKey": "runtime",
                        "version": "4.0.0",
                        "tag": "v4.0.0",
                    },
                    {
                        "provider": "github",
                        "kind": "development",
                        "componentSlug": "spark-operator",
                        "artifactKey": "operator",
                        "ref": "main",
                    },
                    {
                        "provider": "github",
                        "kind": "released",
                        "componentSlug": "spark-operator",
                        "artifactKey": "operator",
                        "version": "1.2.0",
                        "tag": "operator-v1.2.0",
                    },
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (workspace_root / "components/spark/docs/releases/4.0.0").mkdir(parents=True, exist_ok=True)
    (workspace_root / "components/operator/docs/releases/1.2.0").mkdir(parents=True, exist_ok=True)
    if with_content_file:
        (workspace_root / "components/spark/docs/index.md").write_text(
            "spark development docs\n",
            encoding="utf-8",
        )
        (workspace_root / "components/spark/docs/releases/4.0.0/index.md").write_text(
            "spark 4.0.0 release docs\n",
            encoding="utf-8",
        )
        (workspace_root / "components/operator/docs/index.md").write_text(
            "operator development docs\n",
            encoding="utf-8",
        )
        (workspace_root / "components/operator/docs/releases/1.2.0/index.md").write_text(
            "operator 1.2.0 release docs\n",
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
    def __init__(
        self,
        responses: list[tuple[bool, object]],
        *,
        watch_roots: tuple[Path, ...],
        captured_watch_roots: list[tuple[Path, ...]] | None,
        on_prime: Callable[[], None] | None,
        on_replace: Callable[[tuple[Path, ...]], None] | None,
    ) -> None:
        self._responses = list(responses)
        self.watch_roots = watch_roots
        self._captured_watch_roots = captured_watch_roots
        self._on_prime = on_prime
        self._on_replace = on_replace

    def prime(self) -> bool:
        if self._on_prime is not None:
            self._on_prime()
        return True

    def replace_watch_roots(self, watch_roots: tuple[Path, ...]) -> bool:
        self.watch_roots = watch_roots
        if self._captured_watch_roots is not None:
            self._captured_watch_roots.append(watch_roots)
        if self._on_replace is not None:
            self._on_replace(watch_roots)
        return True

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
    on_prime: Callable[[], None] | None = None,
    on_replace: Callable[[tuple[Path, ...]], None] | None = None,
):
    @contextmanager
    def _factory(
        *,
        watch_roots: tuple[Path, ...],
        stage_root: Path,
        work_root: Path,
        report_output: Path | None,
        event_output: Path | None,
        stop_event,
    ):
        del stage_root, work_root, report_output, event_output, stop_event
        if captured_watch_roots is not None:
            captured_watch_roots.append(watch_roots)
        yield _FakeWatchEventStream(
            list(responses),
            watch_roots=watch_roots,
            captured_watch_roots=captured_watch_roots,
            on_prime=on_prime,
            on_replace=on_replace,
        )

    return _factory
