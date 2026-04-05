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

"""Filesystem readiness classification for resolved planning inputs."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from apache_buildish_site_pipeline.models.enums import MaterializationStatus

from .types import InputReadiness, MaterializationStatusReason, ResolvedLocalInput

_MARKER_FILENAME = ".site-pipeline-materialization.json"


def classify_input_readiness(
    inputs: tuple[ResolvedLocalInput, ...],
) -> tuple[ResolvedLocalInput, ...]:
    """Classify each required input as present, missing, stale, or unresolved."""

    return tuple(
        replace(local_input, readiness=_classify_one(local_input))
        for local_input in inputs
    )


def _classify_one(local_input: ResolvedLocalInput) -> InputReadiness:
    normalized_root = local_input.declared_root.resolve(strict=False)
    normalized_path = local_input.expected_local_path.resolve(strict=False)
    if not normalized_path.is_relative_to(normalized_root):
        return InputReadiness(
            status=MaterializationStatus.UNRESOLVED,
            reason=MaterializationStatusReason.PATH_OUTSIDE_DECLARED_ROOT,
        )

    if not normalized_path.exists():
        return InputReadiness(
            status=MaterializationStatus.MISSING,
            reason=MaterializationStatusReason.PATH_MISSING,
        )
    if not normalized_path.is_dir():
        return InputReadiness(
            status=MaterializationStatus.UNRESOLVED,
            reason=MaterializationStatusReason.EXPECTED_DIRECTORY,
        )

    marker_readiness = _classify_marker_readiness(normalized_path, local_input)
    if marker_readiness is not None:
        return marker_readiness
    return InputReadiness(status=MaterializationStatus.PRESENT)


def _classify_marker_readiness(
    expected_path: Path, local_input: ResolvedLocalInput
) -> InputReadiness | None:
    marker_path = expected_path / _MARKER_FILENAME
    if not marker_path.exists():
        return None
    try:
        payload = json.loads(marker_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return InputReadiness(
            status=MaterializationStatus.UNRESOLVED,
            reason=MaterializationStatusReason.INVALID_MARKER,
        )

    expected_pairs = {
        "version": local_input.identity.version,
        "ref": local_input.identity.ref,
        "tag": local_input.identity.tag,
        "commitSha": local_input.identity.commit_sha,
    }
    for key, expected_value in expected_pairs.items():
        if expected_value is None:
            continue
        if payload.get(key) != expected_value:
            return InputReadiness(
                status=MaterializationStatus.STALE,
                reason=MaterializationStatusReason.STALE_IDENTITY_MISMATCH,
            )
    return None
