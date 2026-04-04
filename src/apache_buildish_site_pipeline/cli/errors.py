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