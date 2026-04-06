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

"""Canonical helpers for normalized public-route paths."""

from __future__ import annotations

import posixpath


def normalize_public_path(path: str, *, trailing_slash: bool) -> str:
    """Normalize a public route path with one canonical trailing-slash policy."""

    normalized = posixpath.normpath(path or "/")
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"
    if normalized.startswith("//"):
        normalized = f"/{normalized.lstrip('/')}"
    if normalized != "/":
        normalized = normalized.rstrip("/")
    if trailing_slash and normalized != "/":
        normalized = f"{normalized}/"
    return normalized or "/"


def join_public_path(base_path: str, segment: str, *, trailing_slash: bool) -> str:
    """Join a validated public base path and child segment into one route path."""

    normalized_base = normalize_public_path(base_path, trailing_slash=False)
    normalized_segment = segment.strip("/")
    if not normalized_segment:
        return normalize_public_path(normalized_base, trailing_slash=trailing_slash)
    if normalized_base == "/":
        joined = f"/{normalized_segment}"
    else:
        joined = f"{normalized_base.rstrip('/')}/{normalized_segment}"
    return normalize_public_path(joined, trailing_slash=trailing_slash)