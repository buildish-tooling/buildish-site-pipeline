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

"""Effective component display names shared by planning and staged metadata."""

from __future__ import annotations

from .types import ResolvedComponentConfig


def component_display_name(component: ResolvedComponentConfig) -> str | None:
    """Return the catalog display name, then the component metadata one."""

    display_name = getattr(component.authored, "display_name", None)
    if isinstance(display_name, str):
        return display_name

    repository_document = getattr(component, "repository_document", None)
    repository_component = getattr(repository_document, "component", None)
    repository_display_name = getattr(repository_component, "display_name", None)
    return repository_display_name if isinstance(repository_display_name, str) else None
