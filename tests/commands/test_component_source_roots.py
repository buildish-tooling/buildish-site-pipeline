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

"""Direct coverage for the component source-roots command."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from apache_buildish_site_pipeline.cli.contract import (
    ComponentSourceRootsInvocation,
    RepositoryLayout,
)
from apache_buildish_site_pipeline.commands.component_source_roots import (
    _existing_component_source_root_paths,
    run_component_source_roots,
)
from apache_buildish_site_pipeline.source_roots import (
    ResolvedComponentSourceRoot,
    ResolvedComponentSourceUsage,
    ResolvedSourceBinding,
)

from tests.support.workspace import _workspace


class ComponentSourceRootsCommandTests(unittest.TestCase):
    def test_existing_component_source_root_paths_deduplicates_and_filters_non_directories(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            runtime_root = workspace_root / "components/runtime"
            runtime_root.mkdir(parents=True, exist_ok=True)
            missing_root = workspace_root / "components/missing"
            file_root = workspace_root / "components/file"
            file_root.parent.mkdir(parents=True, exist_ok=True)
            file_root.write_text("not a directory\n", encoding="utf-8")

            roots = (
                _component_source_root("spark", runtime_root, "runtime"),
                _component_source_root("api", runtime_root, "api"),
                _component_source_root("missing", missing_root, "missing"),
                _component_source_root("file", file_root, "file"),
            )

            paths = _existing_component_source_root_paths(roots)

        self.assertEqual(paths, (runtime_root.resolve(strict=False),))

    def test_run_component_source_roots_returns_existing_roots_from_catalog(self) -> None:
        with _workspace(topology="two_artifacts") as workspace_root:
            invocation = _component_source_roots_invocation(workspace_root)

            source_roots = run_component_source_roots(invocation)

        self.assertEqual(
            source_roots,
            (
                (workspace_root / "components/runtime").resolve(strict=False),
                (workspace_root / "components/api").resolve(strict=False),
            ),
        )


def _component_source_root(
    component_slug: str, local_dir: Path, source_key: str
) -> ResolvedComponentSourceRoot:
    return ResolvedComponentSourceRoot(
        component_slug=component_slug,
        local_dir=local_dir.resolve(strict=False),
        usages=(
            ResolvedComponentSourceUsage(
                source_binding=ResolvedSourceBinding(
                    key=source_key,
                    local_dir=local_dir.resolve(strict=False),
                    metadata_file=None,
                    repository=None,
                    default_branch=None,
                ),
                owns_component_content=True,
                artifact_keys=(),
            ),
        ),
    )


def _component_source_roots_invocation(
    workspace_root: Path,
) -> ComponentSourceRootsInvocation:
    site_root = workspace_root / "site"
    return ComponentSourceRootsInvocation(
        layout=RepositoryLayout(
            cwd=workspace_root,
            workspace_root=workspace_root,
            catalog_path=site_root / "catalog.yaml",
            site_root=site_root,
            stage_root=site_root / ".stage",
            work_root=site_root / ".site-pipeline-work",
        )
    )
