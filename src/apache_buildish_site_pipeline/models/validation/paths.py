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

"""Validation helpers for path-bearing wire fields."""

from __future__ import annotations

from .common import _validate_no_structural_whitespace_or_controls


def _validate_normalized_posix_path(
    value: str,
    *,
    type_name: str,
    require_absolute: bool,
    allow_root: bool = False,
    allow_trailing_slash: bool = False,
) -> str:
    value = _validate_no_structural_whitespace_or_controls(value, type_name=type_name)
    if "\\" in value:
        raise ValueError(f"{type_name} must use forward slashes")

    normalized_value = value
    if allow_trailing_slash and value not in {"", "/"} and value.endswith("/"):
        normalized_value = value[:-1]

    if require_absolute:
        if not normalized_value.startswith("/"):
            raise ValueError(f"{type_name} must start with /")
        if normalized_value == "/":
            if allow_root:
                return value
            raise ValueError(f"{type_name} must not be the root path")
        segments = normalized_value[1:].split("/")
    else:
        if normalized_value.startswith("/"):
            raise ValueError(f"{type_name} must be relative rather than absolute")
        segments = normalized_value.split("/")

    if any(segment in {"", ".", ".."} for segment in segments):
        raise ValueError(f"{type_name} must be normalized and traversal-free")
    return value


def validate_local_path_string(value: str) -> str:
    """Reject obviously malformed machine-local path strings."""
    if "\x00" in value:
        raise ValueError("Local paths must not contain NUL bytes")
    return value


def validate_repo_relative_path(value: str) -> str:
    """Validate a repository-relative POSIX path."""
    return _validate_normalized_posix_path(
        value,
        type_name="RepoRelativePath",
        require_absolute=False,
    )


def validate_stage_relative_path(value: str) -> str:
    """Require a normalized stage-relative POSIX path with no traversal syntax."""
    return _validate_normalized_posix_path(
        value,
        type_name="StageRelativePath",
        require_absolute=False,
    )


def validate_public_path(value: str) -> str:
    """Validate a normalized public path rooted at the site origin."""
    value = _validate_normalized_posix_path(
        value,
        type_name="PublicPath",
        require_absolute=True,
        allow_root=True,
        allow_trailing_slash=True,
    )
    if "?" in value or "#" in value:
        raise ValueError("PublicPath must not include query or fragment components")
    return value


def validate_mount_source_ref(value: str) -> str:
    """Validate a stable mount-source reference token."""
    return _validate_no_structural_whitespace_or_controls(
        value, type_name="MountSourceRef"
    )
