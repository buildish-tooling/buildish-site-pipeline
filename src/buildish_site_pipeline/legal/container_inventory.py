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

"""Inventory curated legal metadata for bundled container images."""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
import tomllib

from .release_models import (
    CapturedLegalFile,
    ContainerBuildStage,
    CuratedContainerImageBundle,
    DistributionInventoryEntry,
    normalize_distribution_name,
)

_SITE_PIPELINE_CONTAINERFILE_PATH = Path("tools/site-pipeline-image/Containerfile")
_SITE_PIPELINE_BASE_IMAGE_BUNDLE_MANIFEST_PATH = Path(
    "tools/site-pipeline-image/legal/base-image-bundles.toml"
)
_FROM_INSTRUCTION_PATTERN = re.compile(
    r"^\s*FROM\s+(?P<image_ref>\S+)(?:\s+AS\s+(?P<alias>[A-Za-z0-9._-]+))?\s*$",
    re.IGNORECASE,
)
_COPY_FROM_PATTERN = re.compile(
    r"^\s*COPY\s+(?:--[^\s]+\s+)*--from=(?P<source>[^\s]+)",
    re.IGNORECASE,
)


def collect_container_base_image_entries(
    project_dir: Path,
) -> tuple[DistributionInventoryEntry, ...]:
    """Return curated entries for images bundled into the final container."""

    containerfile_path = project_dir / _SITE_PIPELINE_CONTAINERFILE_PATH
    if not containerfile_path.is_file():
        return ()
    manifest_path = project_dir / _SITE_PIPELINE_BASE_IMAGE_BUNDLE_MANIFEST_PATH
    if not manifest_path.is_file():
        raise RuntimeError(
            "The site-pipeline container image exists but no curated base-image "
            f"legal bundle manifest was found at {manifest_path.as_posix()}"
        )
    referenced_image_refs = bundled_container_image_refs(containerfile_path)
    curated_bundles = curated_container_image_bundles_by_ref(
        project_dir=project_dir,
        manifest_path=manifest_path,
    )
    missing_bundles = sorted(
        image_ref for image_ref in referenced_image_refs if image_ref not in curated_bundles
    )
    if missing_bundles:
        missing_list = "\n - ".join(("", *missing_bundles))
        raise RuntimeError(
            "The site-pipeline container image references base images that have no "
            f"curated release-legal bundle metadata:{missing_list}"
        )
    return tuple(
        build_curated_container_image_entry(bundle=curated_bundles[image_ref])
        for image_ref in referenced_image_refs
    )


def bundled_container_image_refs(containerfile_path: Path) -> tuple[str, ...]:
    """Return image refs that flow into the final site-pipeline container image."""

    stages = parse_container_build_stages(containerfile_path.read_text(encoding="utf-8"))
    if not stages:
        return ()
    stage_lookup: dict[str, int] = {}
    for stage in stages:
        stage_lookup[str(stage.index)] = stage.index
        if stage.alias is not None:
            stage_lookup[stage.alias] = stage.index
    included_stage_indexes = collect_included_stage_indexes(stages, stage_lookup)
    image_refs: list[str] = []
    for stage_index in included_stage_indexes:
        image_refs.append(stages[stage_index].image_ref)
        image_refs.extend(
            source
            for source in stages[stage_index].copy_sources
            if source not in stage_lookup
        )
    return tuple(dict.fromkeys(image_refs))


def parse_container_build_stages(
    containerfile_text: str,
) -> tuple[ContainerBuildStage, ...]:
    """Parse ``FROM`` stages and ``COPY --from`` dependencies."""

    stages: list[ContainerBuildStage] = []
    current_image_ref: str | None = None
    current_alias: str | None = None
    current_copy_sources: list[str] = []
    for raw_line in containerfile_text.splitlines():
        from_match = _FROM_INSTRUCTION_PATTERN.match(raw_line)
        if from_match is not None:
            if current_image_ref is not None:
                stages.append(
                    ContainerBuildStage(
                        index=len(stages),
                        image_ref=current_image_ref,
                        alias=current_alias,
                        copy_sources=tuple(current_copy_sources),
                    )
                )
            current_image_ref = from_match.group("image_ref")
            current_alias = from_match.group("alias")
            current_copy_sources = []
            continue
        if current_image_ref is None:
            continue
        copy_match = _COPY_FROM_PATTERN.match(raw_line)
        if copy_match is not None:
            current_copy_sources.append(copy_match.group("source"))
    if current_image_ref is not None:
        stages.append(
            ContainerBuildStage(
                index=len(stages),
                image_ref=current_image_ref,
                alias=current_alias,
                copy_sources=tuple(current_copy_sources),
            )
        )
    return tuple(stages)


def collect_included_stage_indexes(
    stages: tuple[ContainerBuildStage, ...],
    stage_lookup: dict[str, int],
) -> tuple[int, ...]:
    """Return stage indexes whose content ends up in the final image."""

    if not stages:
        return ()
    included: set[int] = set()
    stack = [len(stages) - 1]
    while stack:
        stage_index = stack.pop()
        if stage_index in included:
            continue
        included.add(stage_index)
        stack.extend(
            referenced_index
            for source in stages[stage_index].copy_sources
            if (referenced_index := stage_lookup.get(source)) is not None
        )
    return tuple(sorted(included))


def curated_container_image_bundles_by_ref(
    *,
    project_dir: Path,
    manifest_path: Path,
) -> dict[str, CuratedContainerImageBundle]:
    """Load repo-managed legal metadata for bundled container base images."""

    manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    bundles_by_ref: dict[str, CuratedContainerImageBundle] = {}
    for raw_bundle in manifest.get("bundles", []):
        image_ref = str(raw_bundle["image-ref"])
        bundles_by_ref[image_ref] = CuratedContainerImageBundle(
            image_ref=image_ref,
            name=str(raw_bundle["name"]),
            version=str(raw_bundle["version"]),
            output_key=str(raw_bundle["output-key"]),
            home_page=_optional_string(raw_bundle.get("home-page")),
            license_expression=_optional_string(raw_bundle.get("license-expression")),
            license_field=_optional_string(raw_bundle.get("license")),
            license_paths=tuple(
                (project_dir / Path(str(relative_path))).resolve()
                for relative_path in raw_bundle.get("license-files", [])
            ),
            notice_paths=tuple(
                (project_dir / Path(str(relative_path))).resolve()
                for relative_path in raw_bundle.get("notice-files", [])
            ),
        )
    return bundles_by_ref


def build_curated_container_image_entry(
    *,
    bundle: CuratedContainerImageBundle,
) -> DistributionInventoryEntry:
    """Convert a curated image bundle into a normal inventory entry."""

    legal_files = collect_curated_legal_files(
        component_key=bundle.output_key,
        component_kind="container-base-image",
        license_paths=bundle.license_paths,
        notice_paths=bundle.notice_paths,
    )
    review_flags: list[str] = []
    if any(file.decode_warning for file in legal_files):
        review_flags.append("legal-file-utf8-decode-warning")
    if any(file.kind == "notice" for file in legal_files):
        review_flags.append("bundled-notice-files-require-review")
    if not bundle.license_paths:
        review_flags.append("missing-curated-license-files")
    declared_license_summary = (
        f"SPDX: {bundle.license_expression}"
        if bundle.license_expression is not None
        else bundle.license_field
    )
    return DistributionInventoryEntry(
        entry_kind="container-base-image",
        name=bundle.name,
        normalized_name=normalize_distribution_name(bundle.name),
        version=bundle.version,
        source_kind="container-image",
        source_reference=bundle.image_ref,
        is_local_project=False,
        metadata_version=None,
        summary=(
            "Curated legal metadata for a container image whose content is bundled "
            "into the final site-pipeline image."
        ),
        home_page=bundle.home_page,
        project_urls=(),
        author=None,
        author_email=None,
        maintainer=None,
        maintainer_email=None,
        requires_dist=(),
        license_expression=bundle.license_expression,
        license_field=bundle.license_field,
        license_classifiers=(),
        declared_license_summary=declared_license_summary,
        captured_legal_files=legal_files,
        review_flags=tuple(review_flags),
    )


def collect_curated_legal_files(
    *,
    component_key: str,
    component_kind: str,
    license_paths: tuple[Path, ...],
    notice_paths: tuple[Path, ...],
) -> tuple[CapturedLegalFile, ...]:
    """Read repo-managed legal files for curated bundled components."""

    captured: list[CapturedLegalFile] = []
    for kind, paths in (("license", license_paths), ("notice", notice_paths)):
        for source_path in paths:
            if not source_path.is_file():
                raise RuntimeError(
                    f"Missing curated {kind} file for {component_kind}: "
                    f"{source_path.as_posix()}"
                )
            file_bytes = source_path.read_bytes()
            try:
                file_text = file_bytes.decode("utf-8")
                decode_warning = None
            except UnicodeDecodeError:
                file_text = file_bytes.decode("utf-8", errors="replace")
                decode_warning = (
                    "File was not valid UTF-8 and was decoded with replacement "
                    "characters."
                )
            captured.append(
                CapturedLegalFile(
                    kind=kind,
                    original_relative_path=source_path.name,
                    installed_path=source_path.as_posix(),
                    output_relative_path=(
                        f"{kind}s/container-base-images/{component_key}/"
                        f"{source_path.name}"
                    ),
                    sha256=hashlib.sha256(file_bytes).hexdigest(),
                    decode_warning=decode_warning,
                    text=_ensure_trailing_newline(file_text),
                )
            )
    return tuple(sorted(captured, key=lambda file: file.output_relative_path))


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    string_value = str(value).strip()
    return string_value or None


def _ensure_trailing_newline(text: str) -> str:
    return text if text.endswith("\n") else f"{text}\n"
