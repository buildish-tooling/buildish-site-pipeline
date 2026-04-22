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
    """Resolve existing component source roots for shell-facing consumers."""

    loaded_catalog = load_catalog_input(
        invocation.layout.workspace_root, invocation.layout.catalog_path
    )
    return _existing_component_source_root_paths(
        resolve_component_source_roots(
            catalog=loaded_catalog.catalog,
            workspace_root=invocation.layout.workspace_root,
        )
    )


def _existing_component_source_root_paths(
    source_roots: tuple[ResolvedComponentSourceRoot, ...],
) -> tuple[Path, ...]:
    unique_paths: list[Path] = []
    seen_paths: set[Path] = set()
    for source_root in source_roots:
        local_dir = source_root.local_dir
        if local_dir in seen_paths or not local_dir.is_dir():
            continue
        seen_paths.add(local_dir)
        unique_paths.append(local_dir)
    return tuple(unique_paths)
