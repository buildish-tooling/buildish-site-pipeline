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

import unittest
from pathlib import Path

from apache_buildish_site_pipeline.cli.contract import (
    ComponentSourceRootsInvocation,
    RepositoryLayout,
)
from apache_buildish_site_pipeline.commands.component_source_roots import (
    _component_source_root_locators,
    run_component_source_roots,
)
from apache_buildish_site_pipeline.source_roots import (
    ResolvedComponentSourceRoot,
    ResolvedComponentSourceUsage,
    ResolvedSourceBinding,
)

from tests.support.workspace import _workspace


class ComponentSourceRootsCommandTests(unittest.TestCase):
    def test_component_source_root_locators_deduplicates_by_export_locator(self) -> None:
        runtime_root = Path("/host/components/runtime")
        roots = (
            _component_source_root(
                "spark",
                runtime_root,
                Path("components/runtime"),
                "runtime",
            ),
            _component_source_root(
                "api",
                runtime_root,
                Path("components/runtime"),
                "api",
            ),
            _component_source_root(
                "missing",
                Path("/host/components/missing"),
                Path("components/missing"),
                "missing",
            ),
            _component_source_root(
                "override",
                runtime_root,
                Path("/srv/overrides/runtime"),
                "override",
            ),
        )

        paths = _component_source_root_locators(roots)

        self.assertEqual(
            paths,
            (
                Path("components/runtime"),
                Path("components/missing"),
                Path("/srv/overrides/runtime"),
            ),
        )

    def test_run_component_source_roots_returns_workspace_relative_roots_from_catalog(
        self,
    ) -> None:
        with _workspace(topology="two_artifacts") as workspace_root:
            invocation = _component_source_roots_invocation(workspace_root)

            source_roots = run_component_source_roots(invocation)

        self.assertEqual(
            source_roots,
            (
                Path("components/runtime"),
                Path("components/api"),
            ),
        )


def _component_source_root(
    component_slug: str, local_dir: Path, export_locator: Path, source_key: str
) -> ResolvedComponentSourceRoot:
    return ResolvedComponentSourceRoot(
        component_slug=component_slug,
        local_dir=local_dir.resolve(strict=False),
        export_locator=export_locator,
        usages=(
            ResolvedComponentSourceUsage(
                source_binding=ResolvedSourceBinding(
                    key=source_key,
                    local_dir=local_dir.resolve(strict=False),
                    export_locator=export_locator,
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
