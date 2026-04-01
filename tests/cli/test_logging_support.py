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

"""Direct tests for shared CLI logging helpers."""

from __future__ import annotations

from contextlib import contextmanager, redirect_stdout
import io
import logging
import pprint
import unittest

from buildish_site_pipeline.cli.logging_support import (
    CliLogMode,
    LIFECYCLE_LEVEL,
    configure_cli_logging,
    derive_cli_log_mode,
    guard_stdout_for_machine_output,
    log_lifecycle,
)


class LoggingSupportTests(unittest.TestCase):
    def test_derive_cli_log_mode_prefers_debug_then_verbose_then_quiet(self) -> None:
        self.assertIs(derive_cli_log_mode(["--quiet"]), CliLogMode.QUIET)
        self.assertIs(derive_cli_log_mode(["--quiet", "--verbose"]), CliLogMode.VERBOSE)
        self.assertIs(
            derive_cli_log_mode(["--quiet", "--verbose", "--debug"]),
            CliLogMode.DEBUG,
        )
        self.assertIs(derive_cli_log_mode([]), CliLogMode.DEFAULT)

    def test_guard_stdout_for_machine_output_redirects_plain_stdout_to_stderr(self) -> None:
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        with redirect_stdout(stdout_buffer):
            with guard_stdout_for_machine_output(enabled=True, stderr=stderr_buffer):
                pprint.pp("machine-unsafe line")

        self.assertEqual(stdout_buffer.getvalue(), "")
        self.assertEqual(stderr_buffer.getvalue(), "'machine-unsafe line'\n")

    def test_configure_cli_logging_sets_root_policy_for_human_logs(self) -> None:
        stderr_buffer = io.StringIO()
        logger = logging.getLogger("tests.cli.logging-support")

        with _preserve_root_logging():
            configure_cli_logging(mode=CliLogMode.DEFAULT, stderr=stderr_buffer)
            log_lifecycle(logger, "build %s", "ready")
            logger.info("extra detail that should stay hidden")

            self.assertEqual(logging.getLogger().level, LIFECYCLE_LEVEL)
            self.assertEqual(stderr_buffer.getvalue(), "build ready\n")


@contextmanager
def _preserve_root_logging():
    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)
    original_level = root_logger.level
    try:
        yield
    finally:
        root_logger.handlers.clear()
        for handler in original_handlers:
            root_logger.addHandler(handler)
        root_logger.setLevel(original_level)
        logging.captureWarnings(False)