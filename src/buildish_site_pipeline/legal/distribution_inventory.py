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

"""Select and inventory locked Python runtime distributions."""

from __future__ import annotations

import hashlib
import importlib.metadata as metadata
from pathlib import Path, PurePosixPath
import subprocess
import tempfile
import tomllib
from typing import Any

from .release_models import (
    CapturedLegalFile,
    DistributionInventoryEntry,
    LockedPackage,
    ProjectUrl,
    normalize_distribution_name,
)

PYLOCK_FILENAME = "pylock.release-legal.toml"
LOCK_SELECTION_COMMAND = (
    "uv",
    "export",
    "--format",
    "pylock.toml",
    "--no-dev",
    "--frozen",
)
_LICENSE_FILE_NAMES = ("license", "licence", "copying")
_NOTICE_FILE_NAMES = ("notice", "notices")
_HOMEPAGE_LABELS = {"homepage", "home", "repository", "source"}


def locked_runtime_packages_from_pylock_text(pylock_text: str) -> tuple[LockedPackage, ...]:
    """Parse one ``uv export --format pylock.toml`` result."""

    parsed = tomllib.loads(pylock_text)
    packages: list[LockedPackage] = []
    for package in parsed.get("packages", []):
        source_kind, source_reference = _locked_package_source(package)
        packages.append(
            LockedPackage(
                name=str(package["name"]),
                version=package.get("version"),
                source_kind=source_kind,
                source_reference=source_reference,
            )
        )
    return tuple(packages)


def export_locked_runtime_packages(project_dir: Path) -> tuple[LockedPackage, ...]:
    """Return the runtime dependency set from the repository's uv lockfile."""

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / PYLOCK_FILENAME
        # This fixed trusted command uses no shell or user-controlled executable.
        subprocess.run(  # noqa: S603
            [*LOCK_SELECTION_COMMAND, "--output-file", output_path.as_posix()],
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        return locked_runtime_packages_from_pylock_text(
            output_path.read_text(encoding="utf-8")
        )


def installed_distributions_by_name(
    search_paths: tuple[Path, ...] | None,
) -> dict[str, metadata.Distribution]:
    """Index installed distributions by normalized package name."""

    distribution_iterable = (
        metadata.distributions()
        if search_paths is None
        else metadata.distributions(path=[path.as_posix() for path in search_paths])
    )
    indexed: dict[str, metadata.Distribution] = {}
    duplicates: set[str] = set()
    for distribution in distribution_iterable:
        name = distribution.metadata.get("Name")
        if name is None:
            continue
        normalized_name = normalize_distribution_name(name)
        existing_distribution = indexed.get(normalized_name)
        if existing_distribution is None:
            indexed[normalized_name] = distribution
            continue
        preferred_distribution = _prefer_distribution_candidate(
            existing_distribution,
            distribution,
        )
        if preferred_distribution is None:
            duplicates.add(normalized_name)
        else:
            indexed[normalized_name] = preferred_distribution
    if duplicates:
        duplicate_list = ", ".join(sorted(duplicates))
        raise RuntimeError(
            "Multiple installed distributions matched the same normalized name: "
            f"{duplicate_list}"
        )
    return indexed


def build_distribution_inventory_entry(
    distribution: metadata.Distribution,
    locked_package: LockedPackage,
) -> DistributionInventoryEntry:
    """Build review metadata for one installed distribution."""

    metadata_message = distribution.metadata
    project_urls = _parse_project_urls(metadata_message)
    legal_files = collect_distribution_legal_files(distribution)
    review_flags = list(_review_flags(metadata_message, legal_files))
    if any(file.decode_warning for file in legal_files):
        review_flags.append("legal-file-utf8-decode-warning")
    package_name = metadata_message.get("Name", locked_package.name)
    return DistributionInventoryEntry(
        entry_kind="python-runtime-distribution",
        name=package_name,
        normalized_name=normalize_distribution_name(package_name),
        version=metadata_message.get("Version", locked_package.version or "unknown"),
        source_kind=locked_package.source_kind,
        source_reference=locked_package.source_reference,
        is_local_project=locked_package.source_kind == "directory",
        metadata_version=metadata_message.get("Metadata-Version"),
        summary=metadata_message.get("Summary"),
        home_page=_home_page(metadata_message, project_urls),
        project_urls=project_urls,
        author=metadata_message.get("Author"),
        author_email=metadata_message.get("Author-email"),
        maintainer=metadata_message.get("Maintainer"),
        maintainer_email=metadata_message.get("Maintainer-email"),
        requires_dist=tuple(metadata_message.get_all("Requires-Dist") or ()),
        license_expression=metadata_message.get("License-Expression"),
        license_field=metadata_message.get("License"),
        license_classifiers=_license_classifiers(metadata_message),
        declared_license_summary=_declared_license_summary(metadata_message),
        captured_legal_files=legal_files,
        review_flags=tuple(dict.fromkeys(review_flags)),
    )


def collect_distribution_legal_files(
    distribution: metadata.Distribution,
) -> tuple[CapturedLegalFile, ...]:
    """Collect bundled license and notice files from one installed distribution."""

    name = distribution.metadata.get("Name", "unknown")
    dist_key = normalize_distribution_name(name)
    captured: dict[str, CapturedLegalFile] = {}
    for relative_path in distribution.files or ():
        pure_relative_path = PurePosixPath(str(relative_path))
        capture_kind = _captured_legal_file_kind(pure_relative_path)
        if capture_kind is None:
            continue
        absolute_path = Path(str(distribution.locate_file(relative_path)))
        if not absolute_path.is_file():
            continue
        file_bytes = absolute_path.read_bytes()
        try:
            file_text = file_bytes.decode("utf-8")
            decode_warning = None
        except UnicodeDecodeError:
            file_text = file_bytes.decode("utf-8", errors="replace")
            decode_warning = (
                "File was not valid UTF-8 and was decoded with replacement characters."
            )
        output_relative_path = _managed_output_relative_path(
            package_key=dist_key,
            capture_kind=capture_kind,
            original_relative_path=pure_relative_path,
        )
        captured[output_relative_path] = CapturedLegalFile(
            kind=capture_kind,
            original_relative_path=pure_relative_path.as_posix(),
            installed_path=absolute_path.resolve().as_posix(),
            output_relative_path=output_relative_path,
            sha256=hashlib.sha256(file_bytes).hexdigest(),
            decode_warning=decode_warning,
            text=_ensure_trailing_newline(file_text),
        )
    return tuple(sorted(captured.values(), key=lambda file: file.output_relative_path))


def inventory_sort_key(
    entry: DistributionInventoryEntry,
) -> tuple[str, str, str, str, str]:
    """Return the stable cross-domain ordering key for inventory entries."""

    return (
        entry.normalized_name,
        entry.version,
        entry.entry_kind,
        entry.source_kind,
        entry.source_reference or "",
    )


def _prefer_distribution_candidate(
    existing_distribution: metadata.Distribution,
    candidate_distribution: metadata.Distribution,
) -> metadata.Distribution | None:
    existing_rank = _distribution_preference_rank(existing_distribution)
    candidate_rank = _distribution_preference_rank(candidate_distribution)
    if candidate_rank > existing_rank:
        return candidate_distribution
    if candidate_rank < existing_rank:
        return existing_distribution
    return None


def _distribution_preference_rank(
    distribution: metadata.Distribution,
) -> tuple[int, int, int]:
    files = tuple(distribution.files or ())
    return (
        int(distribution.read_text("RECORD") is not None),
        int(bool(files)),
        len(files),
    )


def _captured_legal_file_kind(relative_path: PurePosixPath) -> str | None:
    lowered_path = relative_path.as_posix().lower()
    lowered_name = relative_path.name.lower()
    if ".dist-info/licenses/" in lowered_path:
        return "notice" if _looks_like_notice_file(lowered_name) else "license"
    if ".dist-info/" not in lowered_path:
        return None
    if _looks_like_notice_file(lowered_name):
        return "notice"
    if _looks_like_license_file(lowered_name):
        return "license"
    return None


def _managed_output_relative_path(
    *,
    package_key: str,
    capture_kind: str,
    original_relative_path: PurePosixPath,
) -> str:
    base_dir = PurePosixPath(
        "notices" if capture_kind == "notice" else "licenses"
    ) / package_key
    lowered_path = original_relative_path.as_posix().lower()
    if ".dist-info/licenses/" in lowered_path:
        _, relative_suffix = original_relative_path.as_posix().split(
            ".dist-info/licenses/",
            maxsplit=1,
        )
        return (
            base_dir / _safe_relative_subpath(PurePosixPath(relative_suffix))
        ).as_posix()
    return (
        base_dir / _safe_relative_subpath(PurePosixPath(original_relative_path.name))
    ).as_posix()


def _safe_relative_subpath(path: PurePosixPath) -> PurePosixPath:
    safe_parts = tuple(part for part in path.parts if part not in {"", ".", ".."})
    return PurePosixPath(*safe_parts) if safe_parts else PurePosixPath("legal.txt")


def _review_flags(
    metadata_message: metadata.PackageMetadata,
    legal_files: tuple[CapturedLegalFile, ...],
) -> tuple[str, ...]:
    flags: list[str] = []
    has_license_expression = metadata_message.get("License-Expression") is not None
    has_license_field = metadata_message.get("License") is not None
    classifiers = _license_classifiers(metadata_message)
    if not has_license_expression and not has_license_field:
        flags.append(
            "classifier-only-license-metadata"
            if classifiers
            else "missing-license-metadata"
        )
    if has_license_expression and has_license_field:
        flags.append("license-and-license-expression-both-present")
    if not any(file.kind == "license" for file in legal_files):
        flags.append("no-license-files-detected")
    if any(file.kind == "notice" for file in legal_files):
        flags.append("bundled-notice-files-require-review")
    return tuple(flags)


def _declared_license_summary(
    metadata_message: metadata.PackageMetadata,
) -> str | None:
    license_expression = metadata_message.get("License-Expression")
    if license_expression is not None:
        return f"SPDX: {license_expression}"
    license_field = metadata_message.get("License")
    if license_field is not None:
        return license_field
    classifiers = _license_classifiers(metadata_message)
    return "; ".join(classifiers) if classifiers else None


def _license_classifiers(
    metadata_message: metadata.PackageMetadata,
) -> tuple[str, ...]:
    return tuple(
        value
        for value in (metadata_message.get_all("Classifier") or ())
        if value.startswith("License ::")
    )


def _parse_project_urls(
    metadata_message: metadata.PackageMetadata,
) -> tuple[ProjectUrl, ...]:
    parsed: list[ProjectUrl] = []
    for raw_value in metadata_message.get_all("Project-URL") or ():
        label, separator, url = raw_value.partition(",")
        if separator:
            parsed.append(ProjectUrl(label=label.strip(), url=url.strip()))
    return tuple(parsed)


def _home_page(
    metadata_message: metadata.PackageMetadata,
    project_urls: tuple[ProjectUrl, ...],
) -> str | None:
    home_page = metadata_message.get("Home-page")
    if home_page is not None:
        return home_page
    for project_url in project_urls:
        if project_url.label.lower() in _HOMEPAGE_LABELS:
            return project_url.url
    return project_urls[0].url if project_urls else None


def _locked_package_source(package: dict[str, Any]) -> tuple[str, str | None]:
    if "directory" in package:
        return "directory", str(package["directory"].get("path"))
    if "vcs" in package:
        return "vcs", str(package["vcs"].get("url"))
    if "archive" in package:
        return "archive", str(package["archive"].get("url"))
    if "index" in package:
        return "index", str(package.get("index"))
    if "sdist" in package:
        return "sdist", str(package["sdist"].get("url"))
    if "wheels" in package and package["wheels"]:
        return "wheel", str(package["wheels"][0].get("url"))
    return "unknown", None


def _looks_like_license_file(file_name: str) -> bool:
    return file_name.startswith(_LICENSE_FILE_NAMES)


def _looks_like_notice_file(file_name: str) -> bool:
    return file_name.startswith(_NOTICE_FILE_NAMES)


def _ensure_trailing_newline(text: str) -> str:
    return text if text.endswith("\n") else f"{text}\n"
