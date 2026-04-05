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

"""Internal immutable planning/runtime types."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from apache_buildish_site_pipeline.models.catalog import (
    ArtifactLifecycleConfig,
    ArtifactVersioningConfig,
    ComponentCatalogEntry,
    PublicationSelectionPolicy,
    RedirectRuleConfig,
    RouteAliasConfig,
    TopLevelAssetConfig,
)
from apache_buildish_site_pipeline.models.component_repository import (
    ComponentRepositoryDocumentV1,
    SupportStatusDefinition,
)
from apache_buildish_site_pipeline.models.scalars import TimestampString
from apache_buildish_site_pipeline.models.enums import (
    MaterializationInputKind,
    MaterializationStatus,
    PlanningTarget,
    PublicationState,
    RecordKind,
    RouteMode,
    WithdrawalBehavior,
)
from apache_buildish_site_pipeline.models.planning_stage_contract import (
    PipelineDiagnosticEntry,
)
from apache_buildish_site_pipeline.models.provider_snapshot import (
    ProviderAsset,
    ProviderDescriptor,
)

if TYPE_CHECKING:
    from apache_buildish_site_pipeline.staging.types import EffectiveBuildPlan


class MaterializationStatusReason(StrEnum):
    """Small bounded reason vocabulary for planning readiness."""

    PATH_MISSING = "pathMissing"
    EXPECTED_DIRECTORY = "expectedDirectory"
    PATH_OUTSIDE_DECLARED_ROOT = "pathOutsideDeclaredRoot"
    STALE_IDENTITY_MISMATCH = "staleIdentityMismatch"
    INVALID_MARKER = "invalidMarker"
    WATCH_ROOT_CONFLICT = "watchRootConflict"
    UNRESOLVED_SOURCE = "unresolvedSource"


@dataclass(frozen=True, slots=True)
class ResolvedOrigin:
    """Resolved named publication origin."""

    key: str
    base_url: str
    hostname: str
    canonical: bool


@dataclass(frozen=True, slots=True)
class ResolvedPublicationPolicy:
    """Resolved per-component publication facts derived from authored config."""

    origin: ResolvedOrigin
    component_path: str
    development_path: str
    docs_path: str
    assets_path: str
    component_url: str
    development_url: str
    docs_url: str
    assets_url: str
    canonical_path: str | None
    aliases: tuple[RouteAliasConfig, ...]
    redirects: tuple[RedirectRuleConfig, ...]


@dataclass(frozen=True, slots=True)
class ResolvedSourceBinding:
    """Absolute and normalized binding for one authored source root."""

    key: str
    local_dir: Path
    metadata_file: Path | None
    repository: str | None
    default_branch: str | None


@dataclass(frozen=True, slots=True)
class ResolvedVendorAsset:
    """Resolved top-level vendor asset binding."""

    key: str
    source_path: Path
    config: TopLevelAssetConfig


@dataclass(frozen=True, slots=True)
class ResolvedArtifactConfig:
    """Resolved component artifact runtime view."""

    key: str
    authored: object
    source_binding: ResolvedSourceBinding
    docs_root: Path
    assets_root: Path | None
    versioning: ArtifactVersioningConfig
    publication_selection: PublicationSelectionPolicy | None
    lifecycle: ArtifactLifecycleConfig | None
    support_status_vocabulary: dict[str, SupportStatusDefinition]


@dataclass(frozen=True, slots=True)
class ResolvedLocalizationPolicy:
    """Resolved per-component localization facts derived from authored config."""

    default_locale: str | None
    supported_locales: tuple[str, ...] | None
    fallback_locale: str | None
    route_mode: RouteMode | None


@dataclass(frozen=True, slots=True)
class ResolvedComponentConfig:
    """Resolved component runtime view for planning."""

    slug: str
    authored: ComponentCatalogEntry
    repository_document: ComponentRepositoryDocumentV1 | None
    group_key: str | None
    content_source: ResolvedSourceBinding | None
    metadata_file: Path | None
    pages_root: Path | None
    docs_root: Path | None
    assets_root: Path | None
    publication: ResolvedPublicationPolicy
    localization: ResolvedLocalizationPolicy
    publication_selection: PublicationSelectionPolicy | None
    artifacts: tuple[ResolvedArtifactConfig, ...]


@dataclass(frozen=True, slots=True)
class ResolvedSiteConfig:
    """Whole-site planning input after authored/default resolution."""

    workspace_root: Path
    site_pages_root: Path | None
    site_assets_root: Path | None
    vendor_assets: tuple[ResolvedVendorAsset, ...]
    origins: dict[str, ResolvedOrigin]
    sources: dict[str, ResolvedSourceBinding]
    components: tuple[ResolvedComponentConfig, ...]


@dataclass(frozen=True, slots=True)
class IndexedProviderRecord:
    """Compact provider record projection used during planning."""

    provider: str
    kind: RecordKind
    component_slug: str
    artifact_key: str
    external_id: str | None
    external_url: str | None
    version: str | None
    display_version: str | None
    tag: str | None
    ref: str | None
    commit_sha: str | None
    named_ref_key: str | None
    release_line: str | None
    release_line_ancestors: tuple[str, ...]
    support_status: str | None
    publication_state: PublicationState | None
    maturity: str | None
    candidate_sequence: int | None
    vote_status: str | None
    created_at: TimestampString | None
    published_at: TimestampString | None
    updated_at: TimestampString | None
    urls: dict[str, str]
    assets: tuple[ProviderAsset, ...]


@dataclass(frozen=True, slots=True)
class ProviderContextIndex:
    """Provider records grouped by artifact and planning identity."""

    released_by_version: dict[str, tuple[IndexedProviderRecord, ...]]
    candidates_by_version: dict[str, tuple[IndexedProviderRecord, ...]]
    named_refs_by_key: dict[str, tuple[IndexedProviderRecord, ...]]
    refs_by_ref: dict[str, tuple[IndexedProviderRecord, ...]]
    line_heads_by_release_line: dict[str, tuple[IndexedProviderRecord, ...]]
    development_records: tuple[IndexedProviderRecord, ...]


@dataclass(frozen=True, slots=True)
class ProviderSnapshotIndex:
    """Indexed provider snapshot runtime view."""

    providers: dict[str, ProviderDescriptor]
    contexts_by_artifact: dict[tuple[str, str], ProviderContextIndex]
    by_external_id: dict[tuple[str, str], IndexedProviderRecord]
    snapshot_bytes: int
    record_count: int


@dataclass(frozen=True, slots=True)
class SelectedVersionContext:
    """One planned version context selected for the current run."""

    component_slug: str
    artifact_key: str
    kind: RecordKind
    source_binding: ResolvedSourceBinding
    docs_root: Path
    assets_root: Path | None
    version: str | None = None
    display_version: str | None = None
    release_line: str | None = None
    ref: str | None = None
    tag: str | None = None
    commit_sha: str | None = None
    named_ref_key: str | None = None
    maturity: str | None = None
    publication_state: PublicationState | None = None
    withdrawal_behavior: WithdrawalBehavior | None = None
    redirect_target: str | None = None
    provider_record: IndexedProviderRecord | None = None
    support_status: str | None = None
    deterministic: bool = True

    @property
    def input_kind(self) -> MaterializationInputKind:
        """Map the selected record kind to the planning/report input kind."""

        return MaterializationInputKind(self.kind.value)

    @property
    def mutable_in_place(self) -> bool:
        """Whether watch mode may treat this context as live local content."""

        return self.kind in {
            RecordKind.DEVELOPMENT,
            RecordKind.NAMED_REF,
            RecordKind.LINE_HEAD,
        }


@dataclass(frozen=True, slots=True)
class SelectedVersionSet:
    """All version contexts selected for one planning run."""

    contexts: tuple[SelectedVersionContext, ...]
    deterministic: bool


@dataclass(frozen=True, slots=True)
class LocalInputIdentity:
    """Stable local-input identity used for reporting and plan mapping."""

    source_key: str | None
    input_kind: MaterializationInputKind
    component_slug: str | None = None
    artifact_key: str | None = None
    release_line: str | None = None
    version: str | None = None
    ref: str | None = None
    tag: str | None = None
    commit_sha: str | None = None


@dataclass(frozen=True, slots=True)
class InputReadiness:
    """Normalized readiness result for one local input."""

    status: MaterializationStatus
    reason: MaterializationStatusReason | None = None
    details: str | None = None


@dataclass(frozen=True, slots=True)
class ResolvedLocalInput:
    """One concrete local tree required by build or watch."""

    identity: LocalInputIdentity
    declared_root: Path
    expected_local_path: Path
    provenance: str | None
    readiness: InputReadiness
    watch_eligible: bool | None = None


@dataclass(frozen=True, slots=True)
class WatchInputPlan:
    """Derived watch roots and related diagnostics for watch-mode planning."""

    roots: tuple[Path, ...]
    diagnostics: tuple[PipelineDiagnosticEntry, ...]


@dataclass(frozen=True, slots=True)
class PlanToBuildBridge:
    """Decision object describing whether a usable build plan exists."""

    ready: bool
    blocking_inputs: tuple[LocalInputIdentity, ...]
    deterministic: bool
    watch_ready: bool


@dataclass(frozen=True, slots=True)
class PlanningEvaluation:
    """Whole planning pass result before later validation and staging."""

    target: PlanningTarget
    site: ResolvedSiteConfig
    provider_index: ProviderSnapshotIndex
    selected_versions: SelectedVersionSet
    local_inputs: tuple[ResolvedLocalInput, ...]
    watch_plan: WatchInputPlan | None
    build_bridge: PlanToBuildBridge
    diagnostics: tuple[PipelineDiagnosticEntry, ...]
    build_plan_candidate: EffectiveBuildPlan | None
