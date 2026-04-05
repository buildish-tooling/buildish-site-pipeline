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

"""Helpers for enumerating source-tree files without escaping declared roots."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from apache_buildish_site_pipeline.cli.errors import StageIntegrityError


def iter_source_tree_files(*, source_root: Path) -> Iterator[tuple[Path, Path]]:
    """Yield files under one source root while rejecting symlink escapes.

    The trust model treats the declared source root as the maximum authority for
    staged inputs. We therefore resolve every discovered path before using it so
    symlinked files or directories cannot silently pull bytes from outside that
    root.
    """

    normalized_root = source_root.resolve(strict=False)
    for source_path in sorted(source_root.rglob("*")):
        normalized_source_path = source_path.resolve(strict=False)
        if not normalized_source_path.is_relative_to(normalized_root):
            raise StageIntegrityError(
                "Source path escapes declared root after symlink resolution: "
                f"{source_path} -> {normalized_source_path}"
            )
        if source_path.is_dir():
            continue
        yield source_path, source_path.relative_to(source_root)