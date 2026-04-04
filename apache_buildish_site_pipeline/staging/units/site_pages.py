# Copyright 2026 The Apache Software Foundation

"""Worker for top-level site pages."""

from __future__ import annotations

import shutil
from pathlib import Path

from ..front_matter import is_page_path, stage_authored_page
from ..worker_protocol import ContributionFileRefs, WorkerResultWire, WorkerSpecWire


def run_site_pages_unit(spec: WorkerSpecWire) -> WorkerResultWire:
    """Stage site pages into the owned site content subtree."""

    source_root = Path(spec.site_pages_source or "")
    target_root = Path(spec.stage_meta.content_roots[0])
    files_written = 0
    page_files_written = 0
    for source_path in sorted(source_root.rglob("*")):
        if source_path.is_dir():
            continue
        relative_path = source_path.relative_to(source_root)
        destination_path = target_root / relative_path
        if is_page_path(source_path):
            stage_authored_page(source_path=source_path, destination_path=destination_path, namespace=None)
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