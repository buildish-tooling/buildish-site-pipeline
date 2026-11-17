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

"""Component-owned artifact stream and lifecycle contracts."""

from __future__ import annotations
from typing import Self
from pydantic import Field, model_validator
from ...docs.documentation import ComponentOwnedAuthoredModel as SitePipelineBaseModel
from ..enums import PublicationState, WithdrawalBehavior
from ..scalars import (
    Identifier,
    NonEmptyString,
    RefString,
    RegexString,
    TimestampString,
    UrlString,
    VersionString,
    ReferenceString,
)

_WITHDRAWN_PUBLICATION_STATES = frozenset(
    {PublicationState.WITHDRAWN, PublicationState.TOMBSTONED}
)


def _ensure_unique_strings(values: list[str], *, type_name: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"Duplicate {type_name}")


class SupportStatusDefinition(SitePipelineBaseModel):
    """One reusable support-status label, description, and default lifecycle behavior."""

    display_name: NonEmptyString = Field(
        description="Human-readable status label shown to readers, such as `Supported` or `Security fixes only`.",
        examples=["Supported"],
    )
    order: int | None = Field(
        default=None,
        description="Optional sort order used when several support statuses should appear in a stable display order.",
        examples=[10],
    )
    description: NonEmptyString | None = Field(
        default=None,
        description="Human-readable explanation of what this support status means in practice.",
        examples=["Receives regular fixes and new patch releases."],
    )
    default_maintenance_phase: NonEmptyString | None = Field(
        default=None,
        description="Default maintenance-phase label to apply when a release uses this support status and does not provide a more specific phase.",
        examples=["active"],
    )


class NamedRefConfig(SitePipelineBaseModel):
    """Named source-control ref intentionally exposed as a stable version context."""

    key: Identifier = Field(
        description="Stable identifier used elsewhere in the catalog to select this named ref.",
        examples=["preview"],
    )
    ref: RefString = Field(
        description="Exact source-control ref to resolve when this named context is selected.",
        examples=["refs/heads/preview"],
    )
    display_name: NonEmptyString | None = Field(
        default=None,
        description="Human-readable label shown in version pickers, breadcrumbs, or other rendered UI.",
        examples=["Preview"],
    )
    maturity: NonEmptyString | None = Field(
        default=None,
        description="Short maturity label that explains how stable or experimental this named ref should be treated.",
        examples=["preview"],
    )
    description: NonEmptyString | None = Field(
        default=None,
        description="Human-readable explanation of what this named ref contains or who should use it.",
        examples=["Early access docs for the next planned minor release."],
    )


class ArtifactVersioningConfig(SitePipelineBaseModel):
    """How the pipeline discovers development, maintenance, tag, and named-ref versions."""

    development_ref: RefString = Field(
        default="main",
        description="Source-control ref that represents the moving development docs for this artifact.",
        examples=["main"],
    )
    maintenance_ref_pattern: NonEmptyString | None = Field(
        default=None,
        description="Pattern used to derive maintenance branch refs from a release-line key, usually with `{line}` as the substitution placeholder.",
        examples=["release/{line}"],
    )
    tag_pattern: RegexString | None = Field(
        default=None,
        description="Regular expression used to recognize provider tags that belong to this artifact's version stream.",
        examples=[r"^v[0-9]+\.[0-9]+\.[0-9]+$"],
    )
    named_refs: list[NamedRefConfig] | None = Field(
        default=None,
        description="Additional intentionally named version contexts, such as preview or stable branches, that should be selectable by key.",
    )

    @model_validator(mode="after")
    def ensure_named_ref_keys_are_unique(self) -> Self:
        if self.named_refs is None:
            return self

        _ensure_unique_strings(
            [named_ref.key for named_ref in self.named_refs], type_name="named ref key"
        )
        return self


class SupportWindow(SitePipelineBaseModel):
    """Lifecycle dates and support notes for one release line or exact release."""

    release_date: TimestampString | None = Field(
        default=None,
        description="Release date for the line or version that this support window describes.",
        examples=["2026-04-01T00:00:00Z"],
    )
    maintenance_phase: NonEmptyString | None = Field(
        default=None,
        description="Short label for the current maintenance phase, such as general availability, maintenance, or security-only support.",
        examples=["security-fixes"],
    )
    end_of_active_support_date: TimestampString | None = Field(
        default=None,
        description="Date after which the release no longer receives full active support.",
    )
    end_of_support_date: TimestampString | None = Field(
        default=None,
        description="Date after which the release is no longer supported in normal maintenance channels.",
    )
    end_of_life_date: TimestampString | None = Field(
        default=None,
        description="Final retirement date after which the release should be treated as fully end-of-life.",
    )
    support_policy_url: UrlString | None = Field(
        default=None,
        description="Canonical URL that explains the support policy referenced by this support window.",
    )
    notes: NonEmptyString | None = Field(
        default=None,
        description="Additional notes that clarify exceptions, migration advice, or support caveats.",
    )

    @model_validator(mode="after")
    def ensure_dates_are_in_order(self) -> Self:
        ordered_dates = [
            ("releaseDate", self.release_date),
            ("endOfActiveSupportDate", self.end_of_active_support_date),
            ("endOfSupportDate", self.end_of_support_date),
            ("endOfLifeDate", self.end_of_life_date),
        ]
        previous_name: str | None = None
        previous_value = None
        for current_name, current_value in ordered_dates:
            if current_value is None:
                continue
            if previous_value is not None and current_value < previous_value:
                raise ValueError(
                    f"Support-window dates must be ordered: {previous_name} <= {current_name}"
                )
            previous_name = current_name
            previous_value = current_value
        return self


class ReleaseLineConfig(SitePipelineBaseModel):
    """One logical release line, such as `4.0`, together with its lifecycle metadata."""

    key: NonEmptyString = Field(
        description="Stable key for the release line, typically matching the family label used in URLs and navigation.",
        examples=["4.0"],
    )
    display_name: NonEmptyString | None = Field(
        default=None,
        description="Human-readable label shown to readers when the raw line key is not ideal UI text.",
        examples=["4.0 line"],
    )
    parent: NonEmptyString | None = Field(
        default=None,
        description="Optional parent release-line key used to model lineage such as `4.x` inheriting from `3.x` policy or navigation structure.",
        examples=["3.5"],
    )
    latest: VersionString = Field(
        description="Explicit released version recommended as the head of this release line.",
        examples=["4.0.1"],
    )
    support_status: NonEmptyString | None = Field(
        default=None,
        description="Support-status key or label that should be shown for the line as a whole.",
        examples=["supported"],
    )
    aliases: list[NonEmptyString] | None = Field(
        default=None,
        description="Alternate labels that should also resolve to this release line in generated metadata or UI.",
        examples=[["stable"]],
    )
    maintenance_ref: RefString | None = Field(
        default=None,
        description="Explicit maintenance branch ref for the line when it should not be derived from `maintenanceRefPattern`.",
        examples=["refs/heads/release-4.0"],
    )
    support_window: SupportWindow | None = Field(
        default=None,
        description="Lifecycle dates and support notes that apply to the release line.",
    )


class ExactReleaseConfig(SitePipelineBaseModel):
    """Per-version lifecycle metadata and publication overrides for one exact release."""

    version: VersionString = Field(
        description="Exact released version that this metadata entry applies to.",
        examples=["4.0.0"],
    )
    release_line: NonEmptyString | None = Field(
        default=None,
        description="Release-line key that this version belongs to when the provider data alone does not already make that relationship obvious.",
        examples=["4.0"],
    )
    support_status: NonEmptyString | None = Field(
        default=None,
        description="Support-status key or label that should override the line-level status for this exact version.",
        examples=["withdrawn"],
    )
    support_window: SupportWindow | None = Field(
        default=None,
        description="Lifecycle dates and support notes that apply only to this exact release.",
    )
    publication_state: PublicationState | None = Field(
        default=None,
        description="Publication-state override for this version, such as published, withdrawn, or tombstoned.",
    )
    withdrawal_behavior: WithdrawalBehavior | None = Field(
        default=None,
        description="What readers should experience when this release has been withdrawn, for example a redirect or a hard removal.",
    )
    redirect_target: ReferenceString | UrlString | None = Field(
        default=None,
        description="Replacement logical reference or external URL to send readers to when `withdrawalBehavior` is `redirect`.",
        examples=["release:spark/runtime@4.0.1"],
    )
    reason: NonEmptyString | None = Field(
        default=None,
        description="Human-readable explanation of the withdrawal, redirect, or support-state override for this release.",
        examples=["Superseded by 4.0.1."],
    )

    @model_validator(mode="after")
    def ensure_withdrawal_fields_are_consistent(self) -> Self:
        if self.redirect_target is not None and str(self.redirect_target).startswith(
            "route:"
        ):
            raise ValueError(
                "Component withdrawal redirectTarget must use a logical reference or external URL; website routes belong in catalog redirects"
            )
        if self.withdrawal_behavior is None:
            if self.redirect_target is not None:
                raise ValueError("redirectTarget requires withdrawalBehavior: redirect")
            return self

        if self.publication_state not in _WITHDRAWN_PUBLICATION_STATES:
            raise ValueError(
                "withdrawalBehavior is only allowed when publicationState is withdrawn or tombstoned",
            )
        if (
            self.withdrawal_behavior is WithdrawalBehavior.REDIRECT
            and self.redirect_target is None
        ):
            raise ValueError("withdrawalBehavior redirect requires redirectTarget")
        if (
            self.withdrawal_behavior is not WithdrawalBehavior.REDIRECT
            and self.redirect_target is not None
        ):
            raise ValueError(
                "redirectTarget is only allowed when withdrawalBehavior is redirect"
            )
        return self


class ArtifactLifecycleConfig(SitePipelineBaseModel):
    """Lifecycle metadata for an artifact's stable versions, release lines, and support policy."""

    latest_stable: VersionString | None = Field(
        default=None,
        description="Explicit stable version that readers should treat as the default recommendation for this artifact.",
        examples=["4.0.1"],
    )
    release_lines: list[ReleaseLineConfig] | None = Field(
        default=None,
        description="Release-line definitions for this artifact, including latest versions and optional support metadata.",
    )
    releases: list[ExactReleaseConfig] | None = Field(
        default=None,
        description="Per-version lifecycle metadata and publication overrides for exact released versions.",
    )
    support_status_vocabulary: dict[Identifier, SupportStatusDefinition] | None = Field(
        default=None,
        description="Reusable support-status definitions that release lines and exact releases can refer to by key.",
    )
    support_policy_url: UrlString | None = Field(
        default=None,
        description="Canonical URL for the support policy document that readers should consult for this artifact.",
    )
    default_support_window: SupportWindow | None = Field(
        default=None,
        description="Fallback lifecycle window applied when a line or exact release does not provide a more specific support window.",
    )

    @model_validator(mode="after")
    def ensure_release_lines_and_versions_are_unique_and_acyclic(self) -> Self:
        if self.releases is not None:
            _ensure_unique_strings(
                [release.version for release in self.releases],
                type_name="exact release version",
            )

        if self.release_lines is None:
            return self

        release_line_keys = [release_line.key for release_line in self.release_lines]
        _ensure_unique_strings(release_line_keys, type_name="release-line key")
        known_release_line_keys = set(release_line_keys)

        for release_line in self.release_lines:
            if (
                release_line.parent is not None
                and release_line.parent not in known_release_line_keys
            ):
                raise ValueError(f"Unknown release-line parent {release_line.parent!r}")

        visiting: set[str] = set()
        visited: set[str] = set()
        parents_by_key = {
            release_line.key: release_line.parent for release_line in self.release_lines
        }

        def visit(release_line_key: str) -> None:
            if release_line_key in visited:
                return
            if release_line_key in visiting:
                raise ValueError("Release-line parent chains must not contain cycles")

            visiting.add(release_line_key)
            parent_key = parents_by_key[release_line_key]
            if parent_key is not None:
                visit(parent_key)
            visiting.remove(release_line_key)
            visited.add(release_line_key)

        for release_line_key in release_line_keys:
            visit(release_line_key)

        return self
