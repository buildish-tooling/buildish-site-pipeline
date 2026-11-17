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

"""Validate component-owned release decisions before publication selection."""

from __future__ import annotations
from collections import defaultdict
from .types import ResolvedArtifactConfig, ResolvedSiteConfig
from .errors import PlanningInputFailure
from buildish_site_pipeline.models.enums import RecordKind
from buildish_site_pipeline.models.provider.provider_snapshot import (
    ProviderRecord,
    ProviderSnapshotDocumentV1,
)


def release_ancestors(
    artifact: ResolvedArtifactConfig, record: ProviderRecord
) -> tuple[str | None, tuple[str, ...]]:
    lifecycle = artifact.lifecycle
    exact = (
        next(
            (
                item
                for item in lifecycle.releases or ()
                if item.version == record.version
            ),
            None,
        )
        if lifecycle and record.kind is RecordKind.RELEASED
        else None
    )
    if (
        exact
        and exact.release_line
        and record.release_line
        and exact.release_line != record.release_line
    ):
        raise PlanningInputFailure(
            f"Contradictory primary releaseLine for {record.component_slug}:{artifact.key}@{record.version}"
        )
    primary = (
        exact.release_line if exact and exact.release_line else record.release_line
    )
    chain = line_ancestors(artifact, primary)
    if (
        record.release_line_ancestors is not None
        and tuple(record.release_line_ancestors) != chain
    ):
        raise PlanningInputFailure(
            f"Contradictory releaseLineAncestors for {record.component_slug}:{artifact.key}@{record.version}"
        )
    return primary, chain


def line_ancestors(
    artifact: ResolvedArtifactConfig, primary: str | None
) -> tuple[str, ...]:
    lifecycle = artifact.lifecycle
    lines = (
        {line.key: line for line in lifecycle.release_lines or ()} if lifecycle else {}
    )
    chain: list[str] = []
    current = primary
    while current is not None:
        if current not in lines:
            raise PlanningInputFailure(
                f"Unknown release-line {current!r} for artifact {artifact.key}"
            )
        current = lines[current].parent
        if current is not None:
            chain.append(current)
    return tuple(chain)


def validate_release_facts(
    site: ResolvedSiteConfig, snapshot: ProviderSnapshotDocumentV1
) -> dict[tuple[str, str, str], tuple[str | None, tuple[str, ...]]]:
    records_by_artifact: dict[tuple[str, str], list[ProviderRecord]] = defaultdict(list)
    for record in snapshot.records:
        records_by_artifact[(record.component_slug, record.artifact_key)].append(record)
    canonical = {}
    for component in site.components:
        for artifact in component.artifacts:
            lifecycle = artifact.lifecycle
            if lifecycle is None:
                continue
            lines = {line.key: line for line in lifecycle.release_lines or ()}
            releases = {item.version: item for item in lifecycle.releases or ()}
            memberships: dict[str, tuple[str | None, tuple[str, ...]]] = {}
            for release in releases.values():
                memberships[release.version] = (
                    release.release_line,
                    line_ancestors(artifact, release.release_line),
                )
            for record in records_by_artifact[(component.slug, artifact.key)]:
                membership = release_ancestors(artifact, record)
                if record.kind is RecordKind.RELEASED and record.version is not None:
                    previous = memberships.get(record.version)
                    if (
                        previous is not None
                        and previous[0] is not None
                        and membership[0] is not None
                        and previous != membership
                    ):
                        raise PlanningInputFailure(
                            f"Contradictory release-line membership for {component.slug}:{artifact.key}@{record.version}"
                        )
                    if previous is None or membership[0] is not None:
                        memberships[record.version] = membership
            for line in lines.values():
                target_membership = memberships.get(line.latest)
                if (
                    target_membership is None
                    or target_membership[0] is None
                    or line.key not in (target_membership[0], *target_membership[1])
                ):
                    raise PlanningInputFailure(
                        f"Latest target {line.latest!r} for {component.slug}:{artifact.key} line {line.key!r} must be a released member of that line"
                    )
            if (
                lifecycle.latest_stable is not None
                and lifecycle.latest_stable not in memberships
            ):
                raise PlanningInputFailure(
                    f"latestStable {lifecycle.latest_stable!r} for {component.slug}:{artifact.key} must reference a released version"
                )
            for version, membership in memberships.items():
                canonical[(component.slug, artifact.key, version)] = membership
    return canonical
