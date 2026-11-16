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

"""Context-owned storage boundaries shared by scanning, staging, and watch."""

from pathlib import Path


def context_exclusions(kind: str | None, *, versioned: bool = True) -> tuple[str, ...]:
    """Development owns authored docs, not nested version materializations."""
    return (
        (".git", "releases", "candidates")
        if kind == "development" and versioned
        else (".git",)
    )


def excluded_relative_path(relative: Path, exclusions: tuple[str, ...]) -> bool:
    """Match an exact source-relative excluded file or subtree."""
    return any(
        relative == Path(item) or Path(item) in relative.parents for item in exclusions
    )
