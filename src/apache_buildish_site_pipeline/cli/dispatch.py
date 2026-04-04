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

"""CLI invocation dispatch to concrete command handlers."""

from __future__ import annotations

from ..commands.build import run_build
from ..commands.check import run_check
from ..commands.plan import run_plan
from .contract import BuildInvocation, CheckInvocation, CommandInvocation, CommandResult, PlanInvocation


def dispatch_command(invocation: CommandInvocation) -> CommandResult:
    """Execute the handler matching one parsed invocation."""

    if isinstance(invocation, PlanInvocation):
        return run_plan(invocation)
    if isinstance(invocation, CheckInvocation):
        return run_check(invocation)
    if isinstance(invocation, BuildInvocation):
        return run_build(invocation)
    raise AssertionError(f"Unsupported invocation type: {type(invocation)!r}")