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

"""Reusable validation helpers for shared scalar string kinds."""

from __future__ import annotations

import re

_CONTROL_CHARACTER_PATTERN = re.compile(r"[\x00-\x1f\x7f]")
_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?$")


def _validate_no_structural_whitespace_or_controls(value: str, *, type_name: str) -> str:
    if value != value.strip():
        raise ValueError(f"{type_name} must not have leading or trailing whitespace")
    if any(character.isspace() for character in value):
        raise ValueError(f"{type_name} must not contain whitespace")
    if _CONTROL_CHARACTER_PATTERN.search(value):
        raise ValueError(f"{type_name} must not contain control characters")
    return value


def _validate_identifier_like(value: str, *, type_name: str) -> str:
    value = _validate_no_structural_whitespace_or_controls(value, type_name=type_name)
    if not _IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(
            f"{type_name} must use lowercase letters, digits, dots, underscores, or hyphens",
        )
    return value


def validate_identifier(value: str) -> str:
    """Validate a stable internal identifier key."""
    return _validate_identifier_like(value, type_name="Identifier")


def validate_slug(value: str) -> str:
    """Validate a stable component slug."""
    return _validate_identifier_like(value, type_name="Slug")


def validate_artifact_key(value: str) -> str:
    """Validate a stable artifact key."""
    return _validate_identifier_like(value, type_name="ArtifactKey")


def validate_source_key(value: str) -> str:
    """Validate a stable source key."""
    return _validate_identifier_like(value, type_name="SourceKey")


def validate_provider_key(value: str) -> str:
    """Validate a stable provider key."""
    return _validate_identifier_like(value, type_name="ProviderKey")


def validate_version_string(value: str) -> str:
    """Validate an opaque exact version string."""
    return _validate_no_structural_whitespace_or_controls(value, type_name="VersionString")


def validate_ref_string(value: str) -> str:
    """Validate an opaque source-control reference string."""
    value = _validate_no_structural_whitespace_or_controls(value, type_name="RefString")
    if value.startswith("/") or value.endswith("/") or "//" in value:
        raise ValueError("RefString must not be absolute or contain empty path segments")
    if value in {".", ".."}:
        raise ValueError("RefString must not be a traversal token")
    return value