# Copyright 2026 The Apache Software Foundation

"""CLI-specific exception vocabulary."""

from __future__ import annotations


class SitePipelineCliError(Exception):
    """Base class for operator-visible CLI failures."""


class InvocationError(SitePipelineCliError):
    """The caller supplied invalid arguments or an unsafe output path."""


class UnsupportedReportSchemaVersionError(InvocationError):
    """The caller requested a report schema version that is not supported."""


class CommandExecutionError(SitePipelineCliError):
    """The command failed after successful invocation parsing."""


class ReportWriteError(CommandExecutionError):
    """The CLI could not safely persist a report output."""


class StageIntegrityError(CommandExecutionError):
    """The CLI could not safely publish a finalized stage tree."""


class RetainedStageError(CommandExecutionError):
    """A watch cycle failed, but the previously published stage remains trustworthy."""