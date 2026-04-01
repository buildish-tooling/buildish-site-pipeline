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

"""Domain models shared by release-legal inventory and rendering."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

_NORMALIZE_NAME_PATTERN = re.compile(r"[-_.]+")


@dataclass(frozen=True, slots=True)
class LockedPackage:
    """One runtime dependency selected from the project's lock export."""

    name: str
    version: str | None
    source_kind: str
    source_reference: str | None


@dataclass(frozen=True, slots=True)
class ProjectUrl:
    """One parsed ``Project-URL`` metadata entry."""

    label: str
    url: str

    def as_dict(self) -> dict[str, str]:
        return {"label": self.label, "url": self.url}


@dataclass(frozen=True, slots=True)
class CapturedLegalFile:
    """One copied legal file from an installed Python distribution."""

    kind: str
    original_relative_path: str
    installed_path: str
    output_relative_path: str
    sha256: str
    decode_warning: str | None
    text: str

    def as_inventory_dict(self) -> dict[str, str | None]:
        return {
            "kind": self.kind,
            "outputRelativePath": self.output_relative_path,
            "sha256": self.sha256,
            "decodeWarning": self.decode_warning,
        }


@dataclass(frozen=True, slots=True)
class CuratedContainerImageBundle:
    """Repo-managed legal metadata for one bundled container image."""

    image_ref: str
    name: str
    version: str
    output_key: str
    home_page: str | None
    license_expression: str | None
    license_field: str | None
    license_paths: tuple[Path, ...]
    notice_paths: tuple[Path, ...]


@dataclass(frozen=True, slots=True)
class ContainerBuildStage:
    """One parsed ``FROM`` stage from the site-pipeline container definition."""

    index: int
    image_ref: str
    alias: str | None
    copy_sources: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DistributionInventoryEntry:
    """Structured review inventory for one locked runtime distribution."""

    entry_kind: str
    name: str
    normalized_name: str
    version: str
    source_kind: str
    source_reference: str | None
    is_local_project: bool
    metadata_version: str | None
    summary: str | None
    home_page: str | None
    project_urls: tuple[ProjectUrl, ...]
    author: str | None
    author_email: str | None
    maintainer: str | None
    maintainer_email: str | None
    requires_dist: tuple[str, ...]
    license_expression: str | None
    license_field: str | None
    license_classifiers: tuple[str, ...]
    declared_license_summary: str | None
    captured_legal_files: tuple[CapturedLegalFile, ...]
    review_flags: tuple[str, ...]

    @property
    def license_files(self) -> tuple[CapturedLegalFile, ...]:
        return tuple(file for file in self.captured_legal_files if file.kind == "license")

    @property
    def notice_files(self) -> tuple[CapturedLegalFile, ...]:
        return tuple(file for file in self.captured_legal_files if file.kind == "notice")

    def as_inventory_dict(self) -> dict[str, Any]:
        return {
            "entryKind": self.entry_kind,
            "name": self.name,
            "normalizedName": self.normalized_name,
            "sourceKind": self.source_kind,
            "sourceReference": self.source_reference,
            "isLocalProject": self.is_local_project,
            "metadataVersion": self.metadata_version,
            "summary": self.summary,
            "homePage": self.home_page,
            "projectUrls": [item.as_dict() for item in self.project_urls],
            "author": self.author,
            "authorEmail": self.author_email,
            "maintainer": self.maintainer,
            "maintainerEmail": self.maintainer_email,
            "requiresDist": list(self.requires_dist),
            "licenseExpression": self.license_expression,
            "license": self.license_field,
            "licenseClassifiers": list(self.license_classifiers),
            "declaredLicenseSummary": self.declared_license_summary,
            "licenseFiles": [item.as_inventory_dict() for item in self.license_files],
            "noticeFiles": [item.as_inventory_dict() for item in self.notice_files],
            "reviewFlags": list(self.review_flags),
        }


@dataclass(frozen=True, slots=True)
class ReleaseLegalReport:
    """All generated review data for one run of the preliminary helper."""

    selection_command: tuple[str, ...]
    entries: tuple[DistributionInventoryEntry, ...]

    @property
    def python_runtime_entries(self) -> tuple[DistributionInventoryEntry, ...]:
        return tuple(
            entry
            for entry in self.entries
            if entry.entry_kind == "python-runtime-distribution"
        )

    @property
    def third_party_entries(self) -> tuple[DistributionInventoryEntry, ...]:
        return tuple(
            entry for entry in self.python_runtime_entries if not entry.is_local_project
        )

    @property
    def supplemental_entries(self) -> tuple[DistributionInventoryEntry, ...]:
        return tuple(
            entry
            for entry in self.entries
            if entry.entry_kind != "python-runtime-distribution"
        )

    @property
    def bundled_entries(self) -> tuple[DistributionInventoryEntry, ...]:
        return tuple(
            entry
            for entry in self.entries
            if entry.entry_kind != "python-runtime-distribution"
            or not entry.is_local_project
        )

    def as_inventory_dict(self) -> dict[str, Any]:
        packages_with_notices = sum(1 for entry in self.entries if entry.notice_files)
        packages_with_flags = sum(1 for entry in self.entries if entry.review_flags)
        runtime_package_count = len(self.python_runtime_entries)
        supplemental_component_count = len(self.supplemental_entries)
        return {
            "selection": {
                "kind": "uv-export-pylock",
                "command": list(self.selection_command),
                "runtimePackageCount": runtime_package_count,
            },
            "summary": {
                "runtimePackageCount": runtime_package_count,
                "supplementalComponentCount": supplemental_component_count,
                "packagesWithBundledNoticeFiles": packages_with_notices,
                "packagesWithReviewFlags": packages_with_flags,
            },
            "entries": [entry.as_inventory_dict() for entry in self.entries],
        }


def normalize_distribution_name(name: str) -> str:
    """Return the PEP 503-style canonical form used for package matching."""

    return _NORMALIZE_NAME_PATTERN.sub("-", name).lower()
