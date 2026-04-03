# Copyright 2026 The Apache Software Foundation

"""Diagnostic collection and bounded-detail reduction."""

from __future__ import annotations

import hashlib
import json

from apache_buildish_site_pipeline.models.enums import DiagnosticSeverity
from apache_buildish_site_pipeline.models.planning_stage_contract import (
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
            )
        )

    def extend(self, diagnostics: tuple[PipelineDiagnosticEntry, ...]) -> None:
        self._entries.extend(diagnostics)

    def build(self) -> tuple[PipelineDiagnosticEntry, ...]:
        return tuple(sorted(self._entries, key=_diagnostic_sort_key))

    def counts(self) -> DiagnosticCounts:
        diagnostics = self.build()
        return DiagnosticCounts(
            error_count=sum(1 for entry in diagnostics if entry.severity is DiagnosticSeverity.ERROR),
            warning_count=sum(1 for entry in diagnostics if entry.severity is DiagnosticSeverity.WARNING),
            info_count=sum(1 for entry in diagnostics if entry.severity is DiagnosticSeverity.INFO),
        )


def _reduce_details_if_needed(details: object | None) -> object | None:
    if details is None:
        return None
    encoded = json.dumps(details, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) <= _DETAILS_LIMIT_BYTES:
        return details
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