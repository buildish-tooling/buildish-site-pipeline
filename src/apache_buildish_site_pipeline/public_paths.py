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

"""Canonical helpers for normalized public-route paths.

Planning, staging, and evaluation all derive public-facing paths, but they do so
for slightly different call sites:

* planning builds directory-like publication roots such as ``/docs/spark/``
* staging builds concrete page or asset routes such as ``/docs/spark/index.html``
* evaluation normalizes link targets before route lookups

This module is the shared source of truth for those path-shaping rules so the
layers above do not drift apart over time.
"""

from __future__ import annotations

import posixpath


def normalize_public_path(path: str, *, trailing_slash: bool) -> str:
    """Normalize one public route path with an explicit slash style.

    ``trailing_slash=True`` is for directory-like publication roots that should
    stay stable across joins in planning. ``trailing_slash=False`` is for staged
    file routes and evaluated link targets where ``/docs/page`` and not
    ``/docs/page/`` is the canonical lookup key.
    """

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
    """Join a validated public base path and child segment into one route path.

    Callers pass the slash policy that matches their boundary:

    * planning joins publication prefixes and asks for a trailing slash
    * staging joins page-local suffixes and asks for no trailing slash
    """

    normalized_base = normalize_public_path(base_path, trailing_slash=False)
    normalized_segment = segment.strip("/")
    if not normalized_segment:
        return normalize_public_path(normalized_base, trailing_slash=trailing_slash)
    if normalized_base == "/":
        joined = f"/{normalized_segment}"
    else:
        joined = f"{normalized_base.rstrip('/')}/{normalized_segment}"
    return normalize_public_path(joined, trailing_slash=trailing_slash)