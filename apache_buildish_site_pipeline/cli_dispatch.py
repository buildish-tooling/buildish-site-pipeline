# Copyright 2026 The Apache Software Foundation

"""CLI invocation dispatch to concrete command handlers."""

from __future__ import annotations

from .cli_contract import BuildInvocation, CheckInvocation, CommandInvocation, CommandResult, PlanInvocation
from .commands.build import run_build
from .commands.check import run_check
from .commands.plan import run_plan


def dispatch_command(invocation: CommandInvocation) -> CommandResult:
    """Execute the handler matching one parsed invocation."""

    if isinstance(invocation, PlanInvocation):
        return run_plan(invocation)
    if isinstance(invocation, CheckInvocation):
        return run_check(invocation)
    if isinstance(invocation, BuildInvocation):
        return run_build(invocation)
    raise AssertionError(f"Unsupported invocation type: {type(invocation)!r}")