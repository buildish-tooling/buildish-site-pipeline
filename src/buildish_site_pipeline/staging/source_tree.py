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

"""Helpers for enumerating source-tree files without escaping declared roots."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
import os
from buildish_site_pipeline.content_scope import excluded_relative_path

from buildish_site_pipeline.cli.errors import StageIntegrityError


def iter_source_tree_files(
    *,
    source_root: Path,
    exclusions: tuple[str, ...] = (".git",),
    snapshot_paths: tuple[str, ...] = (),
) -> Iterator[tuple[Path, Path]]:
    """Yield contained files, pruning context-owned and bookkeeping subtrees."""
    snapshot_files = {Path(item) for item in snapshot_paths}
    normalized_root = source_root.resolve(strict=False)
    for directory, dirnames, filenames in os.walk(source_root, followlinks=False):
        current = Path(directory)
        for name in sorted(dirnames + filenames):
            source_path = current / name
            relative = source_path.relative_to(source_root)
            if source_path.resolve(
                strict=False
            ) in snapshot_files or excluded_relative_path(relative, exclusions):
                if name in dirnames:
                    dirnames.remove(name)
                continue
            if not source_path.resolve(strict=False).is_relative_to(normalized_root):
                raise StageIntegrityError(
                    f"Source path escapes declared root after symlink resolution: {source_path}"
                )
            if name in filenames:
                yield source_path, relative
        dirnames.sort()
