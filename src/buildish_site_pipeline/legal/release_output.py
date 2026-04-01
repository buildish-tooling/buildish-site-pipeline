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

"""Write preliminary release-legal artifacts to their managed roots."""

from __future__ import annotations

import json
from pathlib import Path
import shutil

from .release_models import ReleaseLegalReport
from .release_rendering import (
    build_inventory_markdown,
    build_preliminary_license_text,
    build_preliminary_notice_text,
)


def write_release_legal_output(
    *,
    output_dir: Path,
    details_output_dir: Path | None,
    report: ReleaseLegalReport,
    project_license_text: str,
    project_notice_text: str,
) -> tuple[Path, ...]:
    """Write the preliminary review files and copied legal texts."""

    output_dir.mkdir(parents=True, exist_ok=True)
    details_dir = output_dir if details_output_dir is None else details_output_dir
    details_dir.mkdir(parents=True, exist_ok=True)
    licenses_dir = details_dir / "licenses"
    notices_dir = details_dir / "notices"

    if details_dir != output_dir:
        for stale_path in (
            details_dir / "LICENSE",
            details_dir / "NOTICE",
            output_dir / "inventory.json",
            output_dir / "inventory.md",
            output_dir / "licenses",
            output_dir / "notices",
        ):
            _remove_output_path(stale_path)

    for managed_dir in (licenses_dir, notices_dir):
        if managed_dir.exists():
            shutil.rmtree(managed_dir)
        managed_dir.mkdir(parents=True, exist_ok=True)

    for entry in report.entries:
        for legal_file in entry.captured_legal_files:
            destination = details_dir / legal_file.output_relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(legal_file.text, encoding="utf-8")

    license_path = output_dir / "LICENSE"
    notice_path = output_dir / "NOTICE"
    inventory_json_path = details_dir / "inventory.json"
    inventory_markdown_path = details_dir / "inventory.md"
    license_path.write_text(
        build_preliminary_license_text(report, project_license_text),
        encoding="utf-8",
    )
    notice_path.write_text(
        build_preliminary_notice_text(report, project_notice_text),
        encoding="utf-8",
    )
    inventory_json_path.write_text(
        json.dumps(report.as_inventory_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    inventory_markdown_path.write_text(
        build_inventory_markdown(report),
        encoding="utf-8",
    )
    return (
        license_path,
        notice_path,
        inventory_json_path,
        inventory_markdown_path,
        licenses_dir,
        notices_dir,
    )


def _remove_output_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()
