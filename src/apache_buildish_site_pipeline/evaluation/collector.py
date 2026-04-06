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

"""Diagnostic collection and bounded-detail reduction."""

from __future__ import annotations

import hashlib
import json
from typing import cast

from apache_buildish_site_pipeline.models.enums import DiagnosticSeverity
from apache_buildish_site_pipeline.models.emitted.planning_stage_contract import (
    ExtensionsObject,
    PipelineDiagnosticEntry,
    ReducedDiagnosticDetailsSummary,
)

from .types import DiagnosticCounts

_DETAILS_LIMIT_BYTES = 8 * 1024
_SEVERITY_ORDER = {
    DiagnosticSeverity.ERROR: 0,
    DiagnosticSeverity.WARNING: 1,
    DiagnosticSeverity.INFO: 2,
}


class DiagnosticCollector:
    """Collect deterministic diagnostics while enforcing size ceilings."""

    def __init__(self) -> None:
        self._entries: list[PipelineDiagnosticEntry] = []

    def add(
        self,
        *,
        severity: DiagnosticSeverity,
        code: str,
        message: str,
        component_slug: str | None = None,
        artifact_key: str | None = None,
        target_id: str | None = None,
        details: object | None = None,
    ) -> None:
        reduced_details = _reduce_details_if_needed(details)
        self._entries.append(
            PipelineDiagnosticEntry(
                severity=severity,
                code=code,
                message=message,
                component_slug=component_slug,
                artifact_key=artifact_key,
                target_id=target_id,
                details=reduced_details,
            ),
        )

    def extend(self, diagnostics: tuple[PipelineDiagnosticEntry, ...]) -> None:
        self._entries.extend(diagnostics)

    def build(self) -> tuple[PipelineDiagnosticEntry, ...]:
        return tuple(sorted(self._entries, key=_diagnostic_sort_key))

    def counts(self) -> DiagnosticCounts:
        diagnostics = self.build()
        return DiagnosticCounts(
            error_count=sum(
                1 for entry in diagnostics if entry.severity is DiagnosticSeverity.ERROR
            ),
            warning_count=sum(
                1
                for entry in diagnostics
                if entry.severity is DiagnosticSeverity.WARNING
            ),
            info_count=sum(
                1 for entry in diagnostics if entry.severity is DiagnosticSeverity.INFO
            ),
        )


def _reduce_details_if_needed(
    details: object | None,
) -> ReducedDiagnosticDetailsSummary | ExtensionsObject | None:
    if details is None:
        return None
    if not isinstance(details, dict):
        raise TypeError("Diagnostic details must be a JSON object when present")
    encoded = json.dumps(details, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) <= _DETAILS_LIMIT_BYTES:
        return cast(ExtensionsObject, details)
    digest = hashlib.sha256(encoded).hexdigest()[:16]
    summary = json.dumps(details, sort_keys=True)[:120]
    return ReducedDiagnosticDetailsSummary(
        omitted=True,
        reason="sizeLimitExceeded",
        actual_bytes=len(encoded),
        limit_bytes=_DETAILS_LIMIT_BYTES,
        summary=summary,
        fingerprint=digest,
    )


def _diagnostic_sort_key(entry: PipelineDiagnosticEntry) -> tuple[object, ...]:
    return (
        _SEVERITY_ORDER[entry.severity],
        entry.code,
        entry.component_slug or "",
        entry.artifact_key or "",
        entry.target_id or "",
        entry.message,
    )
