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

"""Worker for top-level site pages."""

from __future__ import annotations

import shutil
from pathlib import Path

from ..front_matter import is_page_path, stage_authored_page
from ..source_tree import iter_source_tree_files
from ..worker_protocol import ContributionFileRefs, WorkerResultWire, WorkerSpecWire


def run_site_pages_unit(spec: WorkerSpecWire) -> WorkerResultWire:
    """Stage site pages into the owned site content subtree."""

    source_root = Path(spec.site_pages_source or "")
    target_root = Path(spec.stage_meta.content_roots[0])
    files_written = 0
    page_files_written = 0
    for source_path, relative_path in iter_source_tree_files(source_root=source_root):
        destination_path = target_root / relative_path
        if is_page_path(source_path):
            stage_authored_page(
                source_path=source_path,
                destination_path=destination_path,
                namespace=None,
            )
            page_files_written += 1
        else:
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, destination_path)
        files_written += 1
    return WorkerResultWire(
        unit_id=spec.unit_id,
        files_written=files_written,
        page_files_written=page_files_written,
        contribution_files=ContributionFileRefs(),
        stage_meta=spec.stage_meta,
    )
