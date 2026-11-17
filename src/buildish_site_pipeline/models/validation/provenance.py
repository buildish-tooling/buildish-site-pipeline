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

"""Narrow path checks for public original-source targets."""

from pathlib import PureWindowsPath

from .paths import validate_repo_relative_path


def validate_source_target_path(value: str) -> str:
    """Require a portable repository file path without Git-local metadata."""
    value = validate_repo_relative_path(value)
    if PureWindowsPath(value).drive or any(
        part.casefold() == ".git" for part in value.split("/")
    ):
        raise ValueError("Source target must not name a drive or Git-local metadata")
    return value
