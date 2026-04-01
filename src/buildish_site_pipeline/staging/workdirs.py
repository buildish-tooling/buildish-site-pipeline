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

"""Private work-root helpers for one staging run."""

from __future__ import annotations

from dataclasses import dataclass
import shutil
import tempfile
from pathlib import Path

from ..cli.errors import StageIntegrityError
from .ownership import OwnedUnit
from .types import WorkRootLayout


@dataclass(frozen=True, slots=True)
class UnitWorkspace:
    """Private filesystem roots reserved for one owned unit run."""

    unit_id: str
    unit_root: Path
    fragment_path: Path
    content_roots: tuple[Path, ...]
    static_roots: tuple[Path, ...]


@dataclass(frozen=True, slots=True)
class RunWorkspace:
    """Resolved private workspace layout for one staging run."""

    workspace_root: Path
    layout: WorkRootLayout

    def workspace_for_unit(self, unit: OwnedUnit) -> UnitWorkspace:
        """Return the dedicated private workspace reserved for one owned unit."""

        normalized_unit_id = unit.unit_id.replace(":", "_")
        unit_root = self.layout.units_root / normalized_unit_id
        unit_root.mkdir(parents=True, exist_ok=True)
        return UnitWorkspace(
            unit_id=unit.unit_id,
            unit_root=unit_root,
            fragment_path=self.layout.fragments_root / f"{normalized_unit_id}.json",
            content_roots=tuple(
                self.layout.next_stage_root / root for root in unit.content_stage_roots
            ),
            static_roots=tuple(
                self.layout.next_stage_root / root for root in unit.static_stage_roots
            ),
        )


def prepare_next_stage_root(stage_root: Path) -> Path:
    """Ensure one candidate stage root exists and is empty before materialization."""

    if stage_root.is_symlink():
        raise StageIntegrityError(
            f"Candidate stage root must not be a symlink: {stage_root.resolve(strict=False)}"
        )
    normalized_stage_root = stage_root.resolve(strict=False)
    if normalized_stage_root.exists():
        if not normalized_stage_root.is_dir():
            raise StageIntegrityError(
                f"Candidate stage root must be a directory: {normalized_stage_root}"
            )
        if any(normalized_stage_root.iterdir()):
            raise StageIntegrityError(
                f"Candidate stage root must be absent or empty: {normalized_stage_root}"
            )
    normalized_stage_root.mkdir(parents=True, exist_ok=True)
    return normalized_stage_root


def create_work_root_layout(*, next_stage_root: Path) -> WorkRootLayout:
    """Create one private work area alongside the candidate stage tree."""

    normalized_stage_root = next_stage_root.resolve(strict=False)
    parent_path = normalized_stage_root.parent
    parent_path.mkdir(parents=True, exist_ok=True)
    work_root = Path(
        tempfile.mkdtemp(prefix=f".{normalized_stage_root.name}.work.", dir=parent_path)
    )

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
