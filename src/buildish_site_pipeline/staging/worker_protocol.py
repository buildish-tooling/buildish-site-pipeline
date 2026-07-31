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

"""JSON-safe worker protocol models for staging units."""

from __future__ import annotations

from pathlib import Path
import tempfile

from pydantic import Field

from buildish_site_pipeline.cli.errors import StageIntegrityError
from buildish_site_pipeline.models.base import SitePipelineBaseModel
from buildish_site_pipeline.models.enums import RouteMode
from buildish_site_pipeline.models.emitted.staged_front_matter import (
    PageSourceProvenance,
)


class WorkerStageMetaWire(SitePipelineBaseModel):
    """Stage roots written by one worker invocation."""

    content_roots: tuple[str, ...] = Field(
        default=(),
        description="Stage-relative content roots written by the worker.",
        examples=[["content/spark"]],
    )
    static_roots: tuple[str, ...] = Field(
        default=(),
        description="Stage-relative static-asset roots written by the worker.",
        examples=[["static/spark"]],
    )


class ContributionFileRefs(SitePipelineBaseModel):
    """Paths of worker-emitted contribution fragments."""

    unit_manifest: str | None = Field(
        default=None,
        description="Private work-area path of the worker-emitted unit contribution manifest.",
        examples=[".buildish/work/units/spark-runtime/manifest.json"],
    )


class WorkerOutputStats(SitePipelineBaseModel):
    """Small bounded counters summarizing one worker's staged outputs."""

    files_written: int = Field(default=0, description="Total number of files written by the worker during this run.")
    page_files_written: int = Field(default=0, description="Number of staged page files written by the worker during this run.")
    asset_files_written: int = Field(default=0, description="Number of staged asset files written by the worker during this run.")


class WorkerFailureWire(SitePipelineBaseModel):
    """Compact failure payload returned when a worker cannot complete safely."""

    category: str = Field(description="Short machine-readable failure category.", examples=["renderFailure"])
    message: str = Field(description="Primary human-readable failure message returned to the coordinator.")


class WorkerResultWire(SitePipelineBaseModel):
    """Coordinator-visible result of one worker run."""

    unit_id: str = Field(description="Worker unit identifier that produced this result.", examples=["component:spark:runtime"])
    succeeded: bool = Field(default=True, description="Whether the worker completed safely and produced usable output.")
    output_stats: WorkerOutputStats = Field(default_factory=WorkerOutputStats, description="Normalized bounded counters summarizing the worker's staged outputs.")
    failure: WorkerFailureWire | None = Field(default=None, description="Failure payload when the worker could not complete safely.")
    contribution_files: ContributionFileRefs = Field(default_factory=ContributionFileRefs, description="Paths of worker-emitted contribution fragments kept in the private work area.")
    stage_meta: WorkerStageMetaWire = Field(default_factory=WorkerStageMetaWire, description="Stage roots written by the worker during this run.")

    def require_success(self) -> WorkerResultWire:
        """Raise a staging integrity error when the worker reported failure."""

        if self.succeeded:
            return self
        failure = (
            self.failure.message
            if self.failure is not None
            else "unknown worker failure"
        )
        raise StageIntegrityError(f"Worker {self.unit_id!r} failed: {failure}")


class LocalizationWire(SitePipelineBaseModel):
    """Subset of localization state required during page staging."""

    default_locale: str | None = Field(default=None, description="Default locale for the localized page family when localization is enabled.", examples=["en"])
    supported_locales: tuple[str, ...] = Field(default=(), description="Locales that the worker may emit for this page family.", examples=[["en", "de"]])
    route_mode: RouteMode | None = Field(default=None, description="Localization route mode used to derive public paths for translated pages.")


class PagePublicationWire(SitePipelineBaseModel):
    """Page publication base path and URL for one page source family."""

    path: str = Field(description="Public path base for the page source family.", examples=["/spark/4.0.0/docs/"])
    url: str | None = Field(default=None, description="Absolute URL base for the page source family, if known.")
    component_path: str = Field(description="Public root path for the owning component.", examples=["/spark/"])
    component_url: str | None = Field(default=None, description="Absolute URL root for the owning component, if known.")
    origin_key: str = Field(description="Origin key selected for this publication surface.", examples=["archive"])


class ComponentContextWire(SitePipelineBaseModel):
    """One selected version context serialized for the component worker."""

    context_id: str = Field(description="Stable identifier for the selected version context.", examples=["runtime:release:4.0.0"])
    artifact_key: str | None = Field(default=None, description="Owning artifact key when the context belongs to a specific artifact.", examples=["runtime"])
    source_docs_root: str | None = Field(default=None, description="Absolute or workspace-relative docs source root selected for this context.")
    source_assets_root: str | None = Field(default=None, description="Absolute or workspace-relative asset source root selected for this context.")
    content_stage_root: str = Field(description="Stage-relative root where the worker should write staged page output for this context.", examples=["content/spark/4.0.0"])
    static_stage_root: str = Field(description="Stage-relative root where the worker should write staged static assets for this context.", examples=["static/spark/4.0.0"])
    publication: PagePublicationWire = Field(description="Publication base path and URL information for this context.")
    version_context: dict[str, object] | None = Field(default=None, description="Serialized version-context payload forwarded to the worker for page rendering.")
    page_kind: str = Field(description="Primary page-kind label for pages emitted from this context.", examples=["docsPage"])
    section: str = Field(description="Higher-level section label for pages emitted from this context.", examples=["documentation"])
    record_kind: str = Field(description="Version-record kind associated with this context, such as release or named ref.", examples=["release"])
    version_ref: str | None = Field(default=None, description="Source-control ref associated with the context, if present.", examples=["refs/tags/v4.0.0"])
    version: str | None = Field(default=None, description="Exact version string associated with the context, if present.", examples=["4.0.0"])


class WorkerSpecWire(SitePipelineBaseModel):
    """Coordinator-to-worker specification for one owned unit."""

    unit_id: str = Field(description="Stable identifier of the staging unit assigned to the worker.", examples=["component:spark:runtime"])
    unit_kind: str = Field(description="Worker-unit kind, such as site root, component root, or versioned artifact context.", examples=["componentArtifact"])
    owner_id: str = Field(description="Logical owner identifier used for retained-stage ownership accounting.", examples=["artifact:spark/runtime"])
    workspace_root: str = Field(description="Absolute workspace root available to the worker process.")
    unit_root: str | None = Field(default=None, description="Absolute root directory of the owned source unit, if present.")
    fragment_path: str = Field(description="Private work-area path where the worker should persist its contribution manifest fragment.")
    site_pages_source: str | None = Field(default=None, description="Shared site-level pages source root when the worker can stage site-owned pages.")
    site_assets_source: str | None = Field(default=None, description="Shared site-level asset source root when the worker can stage site-owned assets.")
    vendor_assets: tuple[dict[str, str], ...] = Field(default=(), description="Vendor asset mount descriptors forwarded to the worker.")
    component_slug: str | None = Field(default=None, description="Owning component slug when the worker stages component-scoped output.", examples=["spark"])
    component_pages_source: str | None = Field(default=None, description="Component-scoped pages source root, if present.")
    component_pages_stage_root: str | None = Field(default=None, description="Stage-relative root for component-scoped pages, if present.")
    component_assets_source: str | None = Field(default=None, description="Component-scoped assets source root, if present.")
    component_assets_stage_root: str | None = Field(default=None, description="Stage-relative root for component-scoped assets, if present.")
    component_front_matter: dict[str, object] | None = Field(default=None, description="Serialized component-level front matter namespace forwarded to the worker.")
    component_publication: PagePublicationWire | None = Field(default=None, description="Publication base path and URL information for the owning component.")
    localization: LocalizationWire | None = Field(default=None, description="Localization configuration forwarded to the worker when localization is enabled.")
    contexts: tuple[ComponentContextWire, ...] = Field(default=(), description="Selected version contexts that the worker should stage for this unit.")
    stage_meta: WorkerStageMetaWire = Field(default_factory=WorkerStageMetaWire, description="Existing stage roots already associated with the worker's unit.")


class StagedPageContributionWire(SitePipelineBaseModel):
    """Metadata emitted by one page-staging worker for later aggregation."""

    stage_relative_path: str = Field(description="Stage-relative file path of the staged page contribution.", examples=["content/spark/4.0.0/docs/getting-started/index.md"])
    component_slug: str = Field(description="Owning component slug for the staged page.", examples=["spark"])
    artifact_key: str | None = Field(default=None, description="Owning artifact key when the page belongs to a specific artifact.", examples=["runtime"])
    section: str = Field(description="Higher-level section label for the staged page.", examples=["documentation"])
    page_kind: str = Field(description="Short page-kind label for the staged page.", examples=["docsPage"])
    public_path: str = Field(description="Published public path for the staged page.", examples=["/spark/4.0.0/docs/getting-started/"])
    public_url: str | None = Field(default=None, description="Canonical absolute URL for the staged page, if known.")
    component_path: str = Field(description="Public root path for the owning component.", examples=["/spark/"])
    component_url: str | None = Field(default=None, description="Absolute URL root for the owning component, if known.")
    origin_key: str = Field(description="Origin key selected for the staged page.", examples=["archive"])
    version_context: dict[str, object] | None = Field(default=None, description="Serialized version-context payload associated with the staged page.")
    version_kind: str | None = Field(default=None, description="Version-record kind associated with the staged page, if present.", examples=["release"])
    version_ref: str | None = Field(default=None, description="Source-control ref associated with the staged page, if present.", examples=["refs/tags/v4.0.0"])
    version: str | None = Field(default=None, description="Exact version string associated with the staged page, if present.", examples=["4.0.0"])
    locale: str | None = Field(default=None, description="Locale key for the staged page when localization is enabled.", examples=["en"])
    default_locale: bool = Field(default=False, description="Whether the staged page represents the default locale within its translation group.")
    translation_key: str | None = Field(default=None, description="Shared key that ties translated sibling pages together.", examples=["spark-overview"])
    title: str | None = Field(default=None, description="Primary page title extracted during staging.", examples=["Getting Started"])
    link_title: str | None = Field(default=None, description="Shorter link title extracted during staging, if present.", examples=["Start"])
    description: str | None = Field(default=None, description="Primary page description extracted or derived during staging, if present.")
    derived_title: str | None = Field(default=None, description="Body-derived page title inferred from authored content during staging, if present.", examples=["Getting Started"])
    derived_description: str | None = Field(default=None, description="Body-derived page description inferred from authored content during staging, if present.")
    source_path: str | None = Field(default=None, description="Source file path that produced the staged page. Private worker fragments may use an absolute path; the coordinator rewrites workspace sources to workspace-relative form and omits other sources before retaining this internal metadata in the stage.", examples=["components/runtime/docs/getting-started.md"])
    source: PageSourceProvenance | None = Field(
        default=None,
        description="Coordinator-derived repository provenance for the authored source file. Worker-supplied and retained values are overwritten during normalization.",
    )
    canonical_url: str | None = Field(default=None, description="Explicit canonical URL for the page when it should differ from `publicUrl`.")


class UnitContributionManifestWire(SitePipelineBaseModel):
    """Worker-emitted contribution fragment consumed by the coordinator."""

    unit_id: str = Field(description="Worker unit identifier that owns this contribution manifest.", examples=["component:spark:runtime"])
    pages: tuple[StagedPageContributionWire, ...] = Field(default=(), description="Staged page contributions emitted by the worker for later aggregation.")


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
