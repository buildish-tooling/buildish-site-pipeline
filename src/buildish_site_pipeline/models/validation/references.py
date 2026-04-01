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

"""Validation helpers for typed internal reference strings."""

from __future__ import annotations

from .common import (
    _validate_no_structural_whitespace_or_controls,
    validate_artifact_key,
    validate_slug,
)
from .paths import validate_public_path

_SUPPORTED_REFERENCE_PREFIXES = frozenset(
    {"route", "component", "artifact", "line", "release"}
)


def _split_component_artifact(payload: str) -> tuple[str, str]:
    try:
        component_slug, artifact_key = payload.split("/", maxsplit=1)
    except ValueError as exc:
        raise ValueError(
            "Artifact-like references must contain exactly one component/artifact separator",
        ) from exc
    return validate_slug(component_slug), validate_artifact_key(artifact_key)


def validate_reference_string(value: str) -> str:
    """Validate the grammar of a typed internal reference string."""
    value = _validate_no_structural_whitespace_or_controls(
        value, type_name="ReferenceString"
    )

    try:
        prefix, payload = value.split(":", maxsplit=1)
    except ValueError as exc:
        raise ValueError(
            "ReferenceString must contain a typed prefix and payload"
        ) from exc
    if prefix not in _SUPPORTED_REFERENCE_PREFIXES:
        raise ValueError("ReferenceString uses an unsupported typed prefix")
    if payload == "":
        raise ValueError("ReferenceString payload must not be empty")

    if prefix == "route":
        validate_public_path(payload)
        return value
    if prefix == "component":
        validate_slug(payload)
        return value
    if prefix == "artifact":
        _split_component_artifact(payload)
        return value

    try:
        artifact_payload, qualifier = payload.split("@", maxsplit=1)
    except ValueError as exc:
        raise ValueError(
            "Line and release references must contain an @ qualifier"
        ) from exc
    if qualifier == "":
        raise ValueError(
            "Line and release references must include a non-empty qualifier"
        )
    _split_component_artifact(artifact_payload)
    _validate_no_structural_whitespace_or_controls(
        qualifier, type_name="Reference qualifier"
    )
    return value
