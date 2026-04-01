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

"""Workers for top-level static asset families."""

from __future__ import annotations

import shutil
from pathlib import Path

from ..source_tree import iter_source_tree_files
from ..worker_protocol import WorkerOutputStats, WorkerResultWire, WorkerSpecWire


def run_site_assets_unit(spec: WorkerSpecWire) -> WorkerResultWire:
    """Stage site-owned static assets into the site static subtree."""

    files_written = _copy_tree(
        Path(spec.site_assets_source or ""), Path(spec.stage_meta.static_roots[0])
    )
    return WorkerResultWire(
        unit_id=spec.unit_id,
        output_stats=WorkerOutputStats(
            files_written=files_written,
            asset_files_written=files_written,
        ),
        stage_meta=spec.stage_meta,
    )


def run_vendor_assets_unit(spec: WorkerSpecWire) -> WorkerResultWire:
    """Stage vendor assets into stable vendor-key subtrees."""

    files_written = 0
    vendor_root = Path(spec.stage_meta.static_roots[0])
    for asset in spec.vendor_assets:
        source_root = Path(asset["source_path"])
        target_root = vendor_root / asset["key"]
        files_written += _copy_tree(source_root, target_root)
    return WorkerResultWire(
        unit_id=spec.unit_id,
        output_stats=WorkerOutputStats(
            files_written=files_written,
            asset_files_written=files_written,
        ),
        stage_meta=spec.stage_meta,
    )


def _copy_tree(source_root: Path, target_root: Path) -> int:
    count = 0
    for source_path, relative_path in iter_source_tree_files(source_root=source_root):
        destination_path = target_root / relative_path
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)
        count += 1
    return count
