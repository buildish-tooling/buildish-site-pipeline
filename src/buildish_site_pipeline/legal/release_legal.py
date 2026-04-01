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

"""Orchestrate preliminary release-legal inventory and artifact generation.

The stable facade remains intentionally review-oriented. It selects the locked
runtime set, inventories installed distributions, applies license policy, and
writes draft artifacts. Domain implementation lives in sibling modules so
release-process decisions can evolve independently from these mechanics.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .container_inventory import (
    build_curated_container_image_entry,
    bundled_container_image_refs,
    collect_container_base_image_entries,
    collect_curated_legal_files,
    collect_included_stage_indexes,
    curated_container_image_bundles_by_ref,
    parse_container_build_stages,
)
from .distribution_inventory import (
    LOCK_SELECTION_COMMAND,
    build_distribution_inventory_entry,
    collect_distribution_legal_files,
    export_locked_runtime_packages,
    installed_distributions_by_name,
    inventory_sort_key,
    locked_runtime_packages_from_pylock_text,
)
from .license_policy import raise_for_category_x_licenses
from .release_models import (
    CapturedLegalFile,
    ContainerBuildStage,
    CuratedContainerImageBundle,
    DistributionInventoryEntry,
    LockedPackage,
    ProjectUrl,
    ReleaseLegalReport,
    normalize_distribution_name,
)
from .release_output import write_release_legal_output
from .release_rendering import (
    build_inventory_markdown,
    build_preliminary_license_text,
    build_preliminary_notice_text,
)

_LOCK_SELECTION_COMMAND = LOCK_SELECTION_COMMAND

__all__ = [
    "CapturedLegalFile",
    "ContainerBuildStage",
    "CuratedContainerImageBundle",
    "DistributionInventoryEntry",
    "LockedPackage",
    "ProjectUrl",
    "ReleaseLegalReport",
    "build_curated_container_image_entry",
    "build_distribution_inventory_entry",
    "build_inventory_markdown",
    "build_preliminary_license_text",
    "build_preliminary_notice_text",
    "build_release_legal_report",
    "bundled_container_image_refs",
    "collect_container_base_image_entries",
    "collect_curated_legal_files",
    "collect_distribution_legal_files",
    "collect_included_stage_indexes",
    "curated_container_image_bundles_by_ref",
    "export_locked_runtime_packages",
    "generate_release_legal_artifacts",
    "installed_distributions_by_name",
    "locked_runtime_packages_from_pylock_text",
    "main",
    "normalize_distribution_name",
    "parse_container_build_stages",
    "write_release_legal_output",
]


def generate_release_legal_artifacts(
    *,
    project_dir: Path,
    output_dir: Path,
    details_output_dir: Path | None = None,
    distribution_search_paths: tuple[Path, ...] | None = None,
    locked_packages: tuple[LockedPackage, ...] | None = None,
    project_license_text: str | None = None,
    project_notice_text: str | None = None,
) -> tuple[Path, ...]:
    """Generate preliminary legal review artifacts."""

    resolved_project_dir = project_dir.resolve()
    selected_packages = (
        export_locked_runtime_packages(resolved_project_dir)
        if locked_packages is None
        else locked_packages
    )
    report = build_release_legal_report(
        project_dir=resolved_project_dir,
        locked_packages=selected_packages,
        distribution_search_paths=distribution_search_paths,
    )
    return write_release_legal_output(
        output_dir=output_dir,
        details_output_dir=details_output_dir,
        report=report,
        project_license_text=(
            project_license_text
            if project_license_text is not None
            else (resolved_project_dir / "LICENSE").read_text(encoding="utf-8")
        ),
        project_notice_text=(
            project_notice_text
            if project_notice_text is not None
            else (resolved_project_dir / "NOTICE").read_text(encoding="utf-8")
        ),
    )


def build_release_legal_report(
    *,
    project_dir: Path,
    locked_packages: tuple[LockedPackage, ...],
    distribution_search_paths: tuple[Path, ...] | None = None,
) -> ReleaseLegalReport:
    """Collect structured legal-review data for the locked runtime set."""

    distributions = installed_distributions_by_name(distribution_search_paths)
    entries: list[DistributionInventoryEntry] = []
    missing_packages: list[str] = []
    for locked_package in locked_packages:
        distribution = distributions.get(
            normalize_distribution_name(locked_package.name)
        )
        if distribution is None:
            missing_packages.append(locked_package.name)
        else:
            entries.append(
                build_distribution_inventory_entry(distribution, locked_package)
            )
    if missing_packages:
        missing = ", ".join(sorted(missing_packages))
        raise RuntimeError(
            "The current Python environment does not contain all runtime packages "
            f"selected from uv.lock: {missing}"
        )

    # Intentionally disabled: release review has not decided whether generated
    # LICENSE files should enumerate curated container base-image licenses.
    # Keep the isolated collector ready without coupling it to current output.
    # entries.extend(collect_container_base_image_entries(project_dir))

    ordered_entries = tuple(sorted(entries, key=inventory_sort_key))
    raise_for_category_x_licenses(ordered_entries)
    return ReleaseLegalReport(
        selection_command=_LOCK_SELECTION_COMMAND,
        entries=ordered_entries,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m buildish_site_pipeline.legal.release_legal"
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Repository root that contains pyproject.toml, LICENSE, and NOTICE.",
    )
    parser.add_argument(
        "--output-dir",
        default="dist-release-legal/preliminary",
        help=(
            "Directory that should receive the generated preliminary LICENSE and "
            "NOTICE drafts."
        ),
    )
    parser.add_argument(
        "--details-output-dir",
        default="dist/release-legal-preliminary",
        help=(
            "Directory that should receive the generated inventory files and copied "
            "third-party legal texts."
        ),
    )
    parser.add_argument(
        "--distribution-path",
        action="append",
        default=[],
        help=(
            "Optional additional importlib.metadata search path. When omitted, the "
            "current interpreter environment is inspected."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for the preliminary release-legal generator."""

    args = _build_parser().parse_args(argv)
    distribution_paths = tuple(
        Path(path).resolve() for path in args.distribution_path
    ) or None
    for written_path in generate_release_legal_artifacts(
        project_dir=Path(args.project_dir),
        output_dir=Path(args.output_dir),
        details_output_dir=Path(args.details_output_dir),
        distribution_search_paths=distribution_paths,
    ):
        sys.stdout.write(written_path.as_posix())  # noqa: TID251
        sys.stdout.write("\n")  # noqa: TID251
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
