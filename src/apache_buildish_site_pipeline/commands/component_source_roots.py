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

"""Implementation of the `component-source-roots` CLI command."""

from __future__ import annotations

from pathlib import Path

from apache_buildish_site_pipeline.source_roots import (
    ResolvedComponentSourceRoot,
    resolve_component_source_roots,
)

from ..cli.contract import ComponentSourceRootsInvocation
from .shared import load_catalog_input


def run_component_source_roots(
    invocation: ComponentSourceRootsInvocation,
) -> tuple[Path, ...]:
    """Resolve component source-root locators for shell-facing consumers."""

    loaded_catalog = load_catalog_input(
        invocation.layout.workspace_root, invocation.layout.catalog_path
    )
    return _component_source_root_locators(
        resolve_component_source_roots(
            catalog=loaded_catalog.catalog,
            workspace_root=invocation.layout.workspace_root,
        )
    )


def _component_source_root_locators(
    source_roots: tuple[ResolvedComponentSourceRoot, ...],
) -> tuple[Path, ...]:
    unique_paths: list[Path] = []
    seen_paths: set[Path] = set()
    for source_root in source_roots:
        export_locator = (
            source_root.export_locator
            if source_root.export_locator is not None
            else source_root.local_dir
        )
        if export_locator in seen_paths:
            continue
        seen_paths.add(export_locator)
        unique_paths.append(export_locator)
    return tuple(unique_paths)
