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

"""Report validation, rendering, and emission for the CLI."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from apache_buildish_site_pipeline.models.emitted.planning_stage_contract import (
    CheckReportV1,
    PipelineDiagnosticEntry,
    ResolvedMaterializationReportV1,
)
from apache_buildish_site_pipeline.path_trust import path_resolves_through_symlink

from .contract import (
    ReportFormat,
    ReportModel,
    ReportRequest,
    WatchEventFormat,
    WatchEventRequest,
)
from .errors import (
    InvocationError,
    ReportWriteError,
    UnsupportedReportSchemaVersionError,
)


def build_report_request(
    *,
    cwd: Path,
    report_format: str,
    schema_version: int | None,
    report_output: str,
    forbidden_roots: tuple[Path, ...] = (),
    forbid_stdout_json: bool = False,
) -> ReportRequest:
    """Normalize and validate one CLI report request.

    ``report_output`` is a machine-local filesystem path. It is intentionally
    interpreted using the host operating system's native path semantics rather
    than the pipeline's POSIX-only contract path scalars.
    """

    normalized_format = ReportFormat(report_format)
    if normalized_format is ReportFormat.JSON:
        if schema_version is None:
            raise InvocationError(
                "JSON report output requires --report-schema-version 1"
            )
        if schema_version != 1:
            raise UnsupportedReportSchemaVersionError(
                "JSON report output currently supports only --report-schema-version 1",
            )
    elif schema_version is not None:
        raise InvocationError(
            "--report-schema-version is only valid together with --report-format json"
        )

    if report_output == "-":
        if forbid_stdout_json and normalized_format is ReportFormat.JSON:
            raise InvocationError(
                "watch JSON reports must be written to a file, not stdout"
            )
        return ReportRequest(
            report_format=normalized_format,
            schema_version=schema_version,
            output_path=None,
        )

    output_path = _validate_safe_output_path(
        cwd=cwd,
        raw_path=_parse_cli_local_path(report_output),
        forbidden_roots=forbidden_roots,
    )
    return ReportRequest(
        report_format=normalized_format,
        schema_version=schema_version,
        output_path=output_path,
    )


def revalidate_report_request(
    *,
    cwd: Path,
    request: ReportRequest,
    forbidden_roots: tuple[Path, ...] = (),
) -> ReportRequest:
    """Re-run output-path safety checks before rewriting a report file."""

    if request.output_path is None:
        return request
    return ReportRequest(
        report_format=request.report_format,
        schema_version=request.schema_version,
        output_path=_validate_safe_output_path(
            cwd=cwd,
            raw_path=request.output_path,
            forbidden_roots=forbidden_roots,
        ),
    )


def build_watch_event_request(
    *,
    cwd: Path,
    event_format: str | None,
    event_output: str | None,
    forbidden_roots: tuple[Path, ...] = (),
) -> WatchEventRequest | None:
    """Normalize and validate one unstable watch-event stream request."""

    if event_format is None:
        if event_output is not None:
            raise InvocationError(
                "--unstable-events-output is only valid together with --unstable-events"
            )
        return None

    normalized_format = WatchEventFormat(event_format)
    raw_event_output = event_output
    if raw_event_output is None or raw_event_output == "-":
        return WatchEventRequest(event_format=normalized_format, output_path=None)

    output_path = _validate_safe_output_path(
        cwd=cwd,
        raw_path=_parse_cli_local_path(raw_event_output),
        forbidden_roots=forbidden_roots,
        path_label="Watch event output",
    )
    return WatchEventRequest(event_format=normalized_format, output_path=output_path)


def revalidate_watch_event_request(
    *,
    cwd: Path,
    request: WatchEventRequest | None,
    forbidden_roots: tuple[Path, ...] = (),
) -> WatchEventRequest | None:
    """Re-run output-path safety checks before opening a watch-event file sink."""

    if request is None or request.output_path is None:
        return request
    return WatchEventRequest(
        event_format=request.event_format,
        output_path=_validate_safe_output_path(
            cwd=cwd,
            raw_path=request.output_path,
            forbidden_roots=forbidden_roots,
            path_label="Watch event output",
        ),
    )


def emit_report(
    *, request: ReportRequest, report: ReportModel, text_output: str, stdout: TextIO
) -> None:
    """Emit the final operator-facing report to stdout or a file."""

    serialized = _serialize_report(
        report=report, request=request, text_output=text_output
    )
    if request.output_path is None:
        stdout.write(serialized)
        if not serialized.endswith("\n"):
            stdout.write("\n")
        stdout.flush()
        return
    _write_report_file(path=request.output_path, content=serialized)


def _serialize_report(
    *, report: ReportModel, request: ReportRequest, text_output: str
) -> str:
    if request.report_format is ReportFormat.TEXT:
        return text_output
    return report.model_dump_json(indent=2, exclude_none=True)


def render_text_report(report: ReportModel) -> str:
    """Render a human-readable report summary plus diagnostic entries."""

    summary = render_text_report_summary(report)
    rendered_diagnostics = _render_text_diagnostics(report.diagnostics)
    if not rendered_diagnostics:
        return summary
    return f"{summary}\ndiagnostics:\n{rendered_diagnostics}"


def render_text_report_summary(report: ReportModel) -> str:
    """Render a compact one-line human-readable report summary."""

    if isinstance(report, ResolvedMaterializationReportV1):
        return (
            f"plan {report.target.value}: {len(report.entries)} entries, "
            f"diagnostics={len(report.diagnostics)}"
        )
    if isinstance(report, CheckReportV1):
        check_summary = report.summary
        return (
            f"check {check_summary.status.value}: passed={'yes' if check_summary.passed else 'no'}, "
            f"errors={check_summary.error_count}, warnings={check_summary.warning_count}, infos={check_summary.info_count}"
        )
    stage_report = report
    stage_summary = stage_report.summary
    return (
        f"{stage_report.command.value} {stage_summary.status.value}: succeeded={'yes' if stage_summary.succeeded else 'no'}, "
        f"stage={'usable' if stage_summary.stage_usable else 'unusable'}, "
        f"errors={stage_summary.error_count}, warnings={stage_summary.warning_count}, infos={stage_summary.info_count}"
    )


def _render_text_diagnostics(diagnostics: Sequence[PipelineDiagnosticEntry]) -> str:
    return "\n".join(_render_text_diagnostic(entry) for entry in diagnostics)


def _render_text_diagnostic(entry: PipelineDiagnosticEntry) -> str:
    context_parts: list[str] = []
    if entry.component_slug is not None:
        context_parts.append(f"component={entry.component_slug}")
    if entry.artifact_key is not None:
        context_parts.append(f"artifact={entry.artifact_key}")
    if entry.target_id is not None:
        context_parts.append(f"target={entry.target_id}")
    context_suffix = f" [{' '.join(context_parts)}]" if context_parts else ""
    return f"- {entry.severity.value} {entry.code}{context_suffix}: {entry.message}"


def _validate_safe_output_path(
    *,
    cwd: Path,
    raw_path: Path,
    forbidden_roots: tuple[Path, ...],
    path_label: str = "Report output",
) -> Path:
    absolute_path = _absolute_path(cwd=cwd, raw_path=raw_path)
    normalized_path = absolute_path.resolve(strict=False)
    parent_path = absolute_path.parent
    if not parent_path.exists() or not parent_path.is_dir():
        raise InvocationError(
            f"{path_label} parent directory does not exist: {parent_path}"
        )
    if path_resolves_through_symlink(parent_path):
        raise InvocationError(
            f"{path_label} parent directory resolves through a symlink: {parent_path}"
        )
    if absolute_path.exists() and absolute_path.is_symlink():
        raise InvocationError(
            f"{path_label} path must not be a symlink: {absolute_path}"
        )
    for forbidden_root in forbidden_roots:
        if normalized_path.is_relative_to(forbidden_root.resolve(strict=False)):
            raise InvocationError(f"{path_label} must live outside {forbidden_root}")
    return absolute_path


def _parse_cli_local_path(raw_path: str) -> Path:
    """Interpret an operator-supplied local filesystem path using host-native semantics."""

    return Path(raw_path)


def _absolute_path(*, cwd: Path, raw_path: Path) -> Path:
    return raw_path if raw_path.is_absolute() else cwd / raw_path


def _write_report_file(*, path: Path, content: str) -> None:
    absolute_path = _absolute_path(cwd=Path.cwd(), raw_path=path)
    parent_path = absolute_path.parent
    if path_resolves_through_symlink(parent_path):
        raise ReportWriteError(
            f"Report output parent directory resolves through a symlink: {parent_path}"
        )
    if absolute_path.exists() and absolute_path.is_symlink():
        raise ReportWriteError(
            f"Report output path must not be a symlink: {absolute_path}"
        )

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=parent_path,
            prefix=f".{absolute_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_file.write(content)
            temp_file.flush()
            os.fsync(temp_file.fileno())
            temp_path = Path(temp_file.name)
        temp_path.replace(absolute_path)
    except OSError as exc:
        raise ReportWriteError(
            f"Could not write report to {absolute_path}: {exc}"
        ) from exc
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink(missing_ok=True)
