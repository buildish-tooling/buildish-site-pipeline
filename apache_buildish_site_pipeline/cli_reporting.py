# Copyright 2026 The Apache Software Foundation

"""Report validation, rendering, and emission for the CLI."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import TextIO

from apache_buildish_site_pipeline.models.planning_stage_contract import (
    CheckReportV1,
    ResolvedMaterializationReportV1,
    StageRunReportV1,
)

from .cli_contract import ReportFormat, ReportModel, ReportRequest
from .cli_errors import InvocationError, ReportWriteError, UnsupportedReportSchemaVersionError


def build_report_request(
    *,
    cwd: Path,
    report_format: str,
    schema_version: int | None,
    report_output: str,
    forbidden_roots: tuple[Path, ...] = (),
    forbid_stdout_json: bool = False,
) -> ReportRequest:
    """Normalize and validate one CLI report request."""

    normalized_format = ReportFormat(report_format)
    if normalized_format is ReportFormat.JSON:
        if schema_version != 1:
            raise UnsupportedReportSchemaVersionError(
                "JSON report output currently supports only --report-schema-version 1",
            )
    elif schema_version is not None:
        raise InvocationError("--report-schema-version is only valid together with --report-format json")

    if report_output == "-":
        if forbid_stdout_json and normalized_format is ReportFormat.JSON:
            raise InvocationError("watch JSON reports must be written to a file, not stdout")
        return ReportRequest(report_format=normalized_format, schema_version=schema_version, output_path=None)

    output_path = _validate_safe_output_path(cwd=cwd, raw_path=Path(report_output), forbidden_roots=forbidden_roots)
    return ReportRequest(report_format=normalized_format, schema_version=schema_version, output_path=output_path)


def emit_report(*, request: ReportRequest, report: ReportModel, text_output: str, stdout: TextIO) -> None:
    """Emit the final operator-facing report to stdout or a file."""

    serialized = _serialize_report(report=report, request=request, text_output=text_output)
    if request.output_path is None:
        stdout.write(serialized)
        if not serialized.endswith("\n"):
            stdout.write("\n")
        stdout.flush()
        return
    _write_report_file(path=request.output_path, content=serialized)


def _serialize_report(*, report: ReportModel, request: ReportRequest, text_output: str) -> str:
    if request.report_format is ReportFormat.TEXT:
        return text_output
    return report.model_dump_json(indent=2, exclude_none=True)


def render_text_report(report: ReportModel) -> str:
    """Render a compact human-readable report summary."""

    if isinstance(report, ResolvedMaterializationReportV1):
        return (
            f"plan {report.target.value}: {len(report.entries)} entries, "
            f"diagnostics={len(report.diagnostics)}"
        )
    if isinstance(report, CheckReportV1):
        summary = report.summary
        return (
            f"check {summary.status.value}: passed={'yes' if summary.passed else 'no'}, "
            f"errors={summary.error_count}, warnings={summary.warning_count}, infos={summary.info_count}"
        )
    summary = report.summary
    return (
        f"{report.command.value} {summary.status.value}: succeeded={'yes' if summary.succeeded else 'no'}, "
        f"stage={'usable' if summary.stage_usable else 'unusable'}, "
        f"errors={summary.error_count}, warnings={summary.warning_count}, infos={summary.info_count}"
    )


def _validate_safe_output_path(*, cwd: Path, raw_path: Path, forbidden_roots: tuple[Path, ...]) -> Path:
    candidate_path = raw_path if raw_path.is_absolute() else cwd / raw_path
    normalized_path = candidate_path.resolve(strict=False)
    parent_path = normalized_path.parent
    if not parent_path.exists() or not parent_path.is_dir():
        raise InvocationError(f"Report output parent directory does not exist: {parent_path}")
    if _contains_symlink(parent_path):
        raise InvocationError(f"Report output parent directory resolves through a symlink: {parent_path}")
    if normalized_path.exists() and normalized_path.is_symlink():
        raise InvocationError(f"Report output path must not be a symlink: {normalized_path}")
    for forbidden_root in forbidden_roots:
        if normalized_path.is_relative_to(forbidden_root.resolve(strict=False)):
            raise InvocationError(f"Report output must live outside {forbidden_root}")
    return normalized_path


def _contains_symlink(path: Path) -> bool:
    current = Path(path.anchor) if path.is_absolute() else Path()
    for part in path.parts:
        if current == Path(path.anchor) and part == path.anchor:
            continue
        current = current / part if current != Path() else Path(part)
        if current.exists() and current.is_symlink():
            return True
    return False


def _write_report_file(*, path: Path, content: str) -> None:
    parent_path = path.parent
    if _contains_symlink(parent_path):
        raise ReportWriteError(f"Report output parent directory resolves through a symlink: {parent_path}")
    if path.exists() and path.is_symlink():
        raise ReportWriteError(f"Report output path must not be a symlink: {path}")

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=parent_path,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp_file:
            temp_file.write(content)
            temp_file.flush()
            os.fsync(temp_file.fileno())
            temp_path = Path(temp_file.name)
        os.replace(temp_path, path)
    except OSError as exc:
        raise ReportWriteError(f"Could not write report to {path}: {exc}") from exc
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink(missing_ok=True)