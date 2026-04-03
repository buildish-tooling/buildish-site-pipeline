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

"""Shared enum types for wire-facing schema values."""

from enum import StrEnum


class DocumentFormat(StrEnum):
    """Supported serialized input formats for schema document loading."""

    YAML = "yaml"
    JSON = "json"


class MaterializationInputKind(StrEnum):
    """Planning/build/watch local-input category."""

    SITE_PAGES = "sitePages"
    SITE_ASSETS = "siteAssets"
    VENDOR_ASSETS = "vendorAssets"
    DEVELOPMENT = "development"
    NAMED_REF = "namedRef"
    LINE_HEAD = "lineHead"
    CANDIDATE = "candidate"
    RELEASED = "released"


class MaterializationStatus(StrEnum):
    """Readiness state of a required local input."""

    PRESENT = "present"
    MISSING = "missing"
    STALE = "stale"
    UNRESOLVED = "unresolved"


class DiagnosticSeverity(StrEnum):
    """Severity level for pipeline diagnostics."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class PlanningTarget(StrEnum):
    """Planning intent for later staging behavior."""

    BUILD = "build"
    WATCH = "watch"


class StageCommand(StrEnum):
    """Stable stage-producing command modes."""

    BUILD = "build"
    WATCH = "watch"


class RunStatus(StrEnum):
    """Overall diagnostic class for a run or cycle."""

    CLEAN = "clean"
    WARNINGS = "warnings"
    ERRORS = "errors"


class CheckFailureThreshold(StrEnum):
    """Lowest severity that causes ``check`` to fail."""

    ERROR = "error"
    WARNING = "warning"