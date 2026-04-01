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

"""Canonical trust-boundary helpers for filesystem path safety rules."""

from __future__ import annotations

from pathlib import Path


def path_resolves_through_symlink(path: Path) -> bool:
    """Return whether any existing segment of ``path`` is a symlink.

    This helper is the source of truth for trust-boundary checks that must reject
    output targets or retained metadata paths whose resolved ancestry passes
    through a symlinked filesystem entry.
    """

    current = Path(path.anchor) if path.is_absolute() else Path()
    for part in path.parts:
        if current == Path(path.anchor) and part == path.anchor:
            continue
        current = current / part if current != Path() else Path(part)
        if current.exists() and current.is_symlink():
            return True
    return False