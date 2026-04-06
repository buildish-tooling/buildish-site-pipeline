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

"""JSON-safe worker protocol models for staging units."""

from __future__ import annotations

from pathlib import Path
import tempfile

from apache_buildish_site_pipeline.cli.errors import StageIntegrityError
from apache_buildish_site_pipeline.models.base import SitePipelineBaseModel
from apache_buildish_site_pipeline.models.enums import RouteMode


class WorkerStageMetaWire(SitePipelineBaseModel):
    """Stage roots written by one worker invocation."""

    content_roots: tuple[str, ...] = ()
    static_roots: tuple[str, ...] = ()


class ContributionFileRefs(SitePipelineBaseModel):
    """Paths of worker-emitted contribution fragments."""

    unit_manifest: str | None = None


class WorkerOutputStats(SitePipelineBaseModel):
    """Small bounded counters summarizing one worker's staged outputs."""

    files_written: int = 0
    page_files_written: int = 0
    asset_files_written: int = 0


class WorkerFailureWire(SitePipelineBaseModel):
    """Compact failure payload returned when a worker cannot complete safely."""

    category: str
    message: str


class WorkerResultWire(SitePipelineBaseModel):
    """Coordinator-visible result of one worker run."""

    unit_id: str
    succeeded: bool = True
    files_written: int = 0
    page_files_written: int = 0
    asset_files_written: int = 0
    output_stats: WorkerOutputStats = WorkerOutputStats()
    failure: WorkerFailureWire | None = None
    contribution_files: ContributionFileRefs = ContributionFileRefs()
    stage_meta: WorkerStageMetaWire = WorkerStageMetaWire()

    def normalized(self) -> WorkerResultWire:
        """Return a copy with nested counters populated from the legacy fields."""

        if self.output_stats == WorkerOutputStats():
            return self.model_copy(
                update={
                    "output_stats": WorkerOutputStats(
                        files_written=self.files_written,
                        page_files_written=self.page_files_written,
                        asset_files_written=self.asset_files_written,
                    ),
                },
            )
        return self

    def require_success(self) -> WorkerResultWire:
        """Raise a staging integrity error when the worker reported failure."""

        normalized = self.normalized()
        if normalized.succeeded:
            return normalized
        failure = (
            normalized.failure.message
            if normalized.failure is not None
            else "unknown worker failure"
        )
        raise StageIntegrityError(f"Worker {normalized.unit_id!r} failed: {failure}")


class LocalizationWire(SitePipelineBaseModel):
    """Subset of localization state required during page staging."""

    default_locale: str | None = None
    supported_locales: tuple[str, ...] = ()
    route_mode: RouteMode | None = None


class PagePublicationWire(SitePipelineBaseModel):
    """Page publication base path and URL for one page source family."""

    path: str
    url: str | None = None
    component_path: str
    component_url: str | None = None
    origin_key: str


class ComponentContextWire(SitePipelineBaseModel):
    """One selected version context serialized for the component worker."""

    context_id: str
    artifact_key: str | None = None
    source_docs_root: str | None = None
    source_assets_root: str | None = None
    content_stage_root: str
    static_stage_root: str
    publication: PagePublicationWire
    version_context: dict[str, object] | None = None
    page_kind: str
    section: str
    record_kind: str
    version_ref: str | None = None
    version: str | None = None


class WorkerSpecWire(SitePipelineBaseModel):
    """Coordinator-to-worker specification for one owned unit."""

    unit_id: str
    unit_kind: str
    owner_id: str
    workspace_root: str
    unit_root: str | None = None
    fragment_path: str
    site_pages_source: str | None = None
    site_assets_source: str | None = None
    vendor_assets: tuple[dict[str, str], ...] = ()
    component_slug: str | None = None
    component_pages_source: str | None = None
    component_pages_stage_root: str | None = None
    component_assets_source: str | None = None
    component_assets_stage_root: str | None = None
    component_front_matter: dict[str, object] | None = None
    component_publication: PagePublicationWire | None = None
    localization: LocalizationWire | None = None
    contexts: tuple[ComponentContextWire, ...] = ()
    stage_meta: WorkerStageMetaWire = WorkerStageMetaWire()


class StagedPageContributionWire(SitePipelineBaseModel):
    """Metadata emitted by one page-staging worker for later aggregation."""

    stage_relative_path: str
    component_slug: str
    artifact_key: str | None = None
    section: str
    page_kind: str
    public_path: str
    public_url: str | None = None
    component_path: str
    component_url: str | None = None
    origin_key: str
    version_context: dict[str, object] | None = None
    version_kind: str | None = None
    version_ref: str | None = None
    version: str | None = None
    locale: str | None = None
    default_locale: bool = False
    translation_key: str | None = None
    title: str | None = None
    link_title: str | None = None
    source_path: str
    canonical_url: str | None = None


class UnitContributionManifestWire(SitePipelineBaseModel):
    """Worker-emitted contribution fragment consumed by the coordinator."""

    unit_id: str
    pages: tuple[StagedPageContributionWire, ...] = ()


def write_unit_manifest(path: Path, manifest: UnitContributionManifestWire) -> None:
    """Persist one worker contribution manifest atomically within the private work area."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_file.write(manifest.model_dump_json(indent=2, by_alias=True))
            temp_path = Path(temp_file.name)
        temp_path.replace(path)
    except OSError as exc:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise StageIntegrityError(
            f"Could not write worker contribution manifest: {path}"
        ) from exc


def read_unit_manifest(path: Path) -> UnitContributionManifestWire:
    """Load one worker contribution manifest from JSON."""

    return UnitContributionManifestWire.model_validate_json(
        path.read_text(encoding="utf-8")
    )


def worker_failure_result(
    *, unit_id: str, category: str, message: str, stage_meta: WorkerStageMetaWire
) -> WorkerResultWire:
    """Build one normalized failure result for the explicit worker boundary."""

    return WorkerResultWire(
        unit_id=unit_id,
        succeeded=False,
        output_stats=WorkerOutputStats(),
        failure=WorkerFailureWire(category=category, message=message),
        stage_meta=stage_meta,
    )
