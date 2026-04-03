# Copyright 2026 The Apache Software Foundation

"""CLI invocation dispatch to concrete command handlers."""

from __future__ import annotations

from .cli_contract import BuildInvocation, CheckInvocation, CommandInvocation, CommandResult, PlanInvocation, WatchInvocation
from .commands.build import run_build
from .commands.check import run_check
from .commands.plan import run_plan
from .commands.watch import run_watch


def dispatch_command(invocation: CommandInvocation) -> CommandResult:
    """Execute the handler matching one parsed invocation."""

    if isinstance(invocation, PlanInvocation):
        return run_plan(invocation)
    if isinstance(invocation, CheckInvocation):
        return run_check(invocation)
    if isinstance(invocation, BuildInvocation):
        return run_build(invocation)
    if isinstance(invocation, WatchInvocation):
        run_watch()
    raise AssertionError(f"Unsupported invocation type: {type(invocation)!r}")