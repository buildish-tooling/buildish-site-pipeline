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

"""Shared CLI logging policy and stdout-guard helpers."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager, redirect_stdout
from enum import Enum
import logging
import sys
from typing import TextIO

TRACE_LEVEL = 5
LIFECYCLE_LEVEL = 25


class CliLogMode(Enum):
    """Supported human-log verbosity modes for the CLI."""

    QUIET = "quiet"
    DEFAULT = "default"
    VERBOSE = "verbose"
    DEBUG = "debug"


_LOG_MODE_BY_FLAG = {
    "--quiet": CliLogMode.QUIET,
    "--verbose": CliLogMode.VERBOSE,
    "--debug": CliLogMode.DEBUG,
}
_LEVEL_BY_MODE = {
    CliLogMode.QUIET: logging.WARNING,
    CliLogMode.DEFAULT: LIFECYCLE_LEVEL,
    CliLogMode.VERBOSE: logging.INFO,
    CliLogMode.DEBUG: logging.DEBUG,
}


def configure_cli_logging(*, mode: CliLogMode, stderr: TextIO) -> None:
    """Configure root logging so all human-facing logs follow one CLI policy."""

    _ensure_custom_levels_registered()
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(_LEVEL_BY_MODE[mode])
    handler = logging.StreamHandler(stderr)
    handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.addHandler(handler)
    logging.captureWarnings(True)


def derive_cli_log_mode(argv: Sequence[str] | None) -> CliLogMode:
    """Best-effort early log-mode detection before full argparse processing."""

    raw_argv = sys.argv[1:] if argv is None else argv
    selected_modes = [
        _LOG_MODE_BY_FLAG[arg] for arg in raw_argv if arg in _LOG_MODE_BY_FLAG
    ]
    if CliLogMode.DEBUG in selected_modes:
        return CliLogMode.DEBUG
    if CliLogMode.VERBOSE in selected_modes:
        return CliLogMode.VERBOSE
    if CliLogMode.QUIET in selected_modes:
        return CliLogMode.QUIET
    return CliLogMode.DEFAULT


def log_lifecycle(logger: logging.Logger, message: str, *args: object) -> None:
    """Emit one human-facing lifecycle/progress log entry."""

    logger.log(LIFECYCLE_LEVEL, message, *args)


def log_trace(logger: logging.Logger, message: str, *args: object) -> None:
    """Emit one future trace-level log entry."""

    logger.log(TRACE_LEVEL, message, *args)


@contextmanager
def guard_stdout_for_machine_output(*, enabled: bool, stderr: TextIO) -> Iterator[None]:
    """Best-effort redirect plain stdout writes away from machine-only stdout."""

    if not enabled:
        yield
        return
    with redirect_stdout(stderr):
        yield


def _ensure_custom_levels_registered() -> None:
    logging.addLevelName(TRACE_LEVEL, "TRACE")
    logging.addLevelName(LIFECYCLE_LEVEL, "LIFECYCLE")
