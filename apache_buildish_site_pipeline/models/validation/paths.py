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


def validate_local_path_string(value: str) -> str:
    """Reject obviously malformed machine-local path strings."""
    if "\x00" in value:
        raise ValueError("Local paths must not contain NUL bytes")
    return value


def validate_stage_relative_path(value: str) -> str:
    """Require a normalized stage-relative POSIX path with no traversal syntax."""
    if value.startswith("/"):
        raise ValueError("Stage-relative paths must not be absolute")
    if "\\" in value:
        raise ValueError("Stage-relative paths must use forward slashes")

    segments = value.split("/")
    if any(segment in {"", ".", ".."} for segment in segments):
        raise ValueError("Stage-relative paths must be normalized and traversal-free")
    return value