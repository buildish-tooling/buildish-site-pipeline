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

"""Private work-root helpers for one staging run."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from ..cli_errors import StageIntegrityError
from .types import WorkRootLayout


def prepare_next_stage_root(stage_root: Path) -> Path:
    """Ensure one candidate stage root exists and is empty before materialization."""

    normalized_stage_root = stage_root.resolve(strict=False)
    if normalized_stage_root.exists():
        if normalized_stage_root.is_symlink():
            raise StageIntegrityError(f"Candidate stage root must not be a symlink: {normalized_stage_root}")
        if not normalized_stage_root.is_dir():
            raise StageIntegrityError(f"Candidate stage root must be a directory: {normalized_stage_root}")
        if any(normalized_stage_root.iterdir()):
            raise StageIntegrityError(f"Candidate stage root must be absent or empty: {normalized_stage_root}")
    normalized_stage_root.mkdir(parents=True, exist_ok=True)
    return normalized_stage_root


def create_work_root_layout(*, next_stage_root: Path) -> WorkRootLayout:
    """Create one private work area alongside the candidate stage tree."""

    normalized_stage_root = next_stage_root.resolve(strict=False)
    parent_path = normalized_stage_root.parent
    parent_path.mkdir(parents=True, exist_ok=True)
    work_root = Path(tempfile.mkdtemp(prefix=f".{normalized_stage_root.name}.work.", dir=parent_path))

    layout = WorkRootLayout(
        work_root=work_root,
        next_stage_root=normalized_stage_root,
        content_root=normalized_stage_root / "content",
        static_root=normalized_stage_root / "static",
        data_root=normalized_stage_root / "data",
        fragments_root=work_root / "fragments",
        units_root=work_root / "units",
    )
    for path in (
        layout.content_root,
        layout.static_root,
        layout.data_root,
        layout.fragments_root,
        layout.units_root,
    ):
        path.mkdir(parents=True, exist_ok=True)
    return layout


def remove_work_root(layout: WorkRootLayout) -> None:
    """Best-effort cleanup for one private work area."""

    shutil.rmtree(layout.work_root, ignore_errors=True)