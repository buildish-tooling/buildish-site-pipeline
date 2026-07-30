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

"""Command-line entry point for the site pipeline."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import logging
import sys
from pathlib import Path
from typing import Never, TextIO

from buildish_site_pipeline.models.enums import (
    CheckFailureThreshold,
    PlanningTarget,
)

from ..commands.component_source_roots import run_component_source_roots
from ..commands.watch import run_watch
from .contract import (
    ApplicationExitCode,
    BuildInvocation,
    CheckInvocation,
    ComponentSourceRootsInvocation,
    CommandInvocation,
    ReportModel,
    ReportRequest,
    PlanInvocation,
    RepositoryLayout,
    WatchEventRequest,
    WatchEventFormat,
    WatchInvocation,
)
from .dispatch import dispatch_command
from .errors import CommandExecutionError, InvocationError, SitePipelineCliError
from .logging_support import (
    configure_cli_logging,
    derive_cli_log_mode,
    guard_stdout_for_machine_output,
)
from .reporting import (
    build_report_request,
    build_watch_event_request,
    emit_report,
    revalidate_report_request,
    revalidate_watch_event_request,
)


_LOGGER = logging.getLogger(__name__)


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        raise InvocationError(message)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return the process exit code."""

    return _run(argv=argv, stdout=sys.stdout, stderr=sys.stderr)  # noqa: TID251


def _run(*, argv: Sequence[str] | None, stdout: TextIO, stderr: TextIO) -> int:
    configure_cli_logging(mode=derive_cli_log_mode(argv), stderr=stderr)
    try:
        invocation = parse_invocation(argv)
        if isinstance(invocation, WatchInvocation):
            return _run_watch_invocation(
                invocation=invocation, stdout=stdout, stderr=stderr
            )
        if isinstance(invocation, ComponentSourceRootsInvocation):
            return _run_component_source_roots_invocation(
                invocation=invocation, stdout=stdout
            )
        return _run_non_watch_invocation(invocation=invocation, stdout=stdout)
    except InvocationError as exc:
        _emit_error(str(exc), stderr=stderr)
        return int(ApplicationExitCode.INVOCATION_ERROR)
    except CommandExecutionError as exc:
        _emit_error(str(exc), stderr=stderr)
        return int(ApplicationExitCode.INTERNAL_FAILURE)
    except SitePipelineCliError as exc:
        _emit_error(str(exc), stderr=stderr)
        return int(ApplicationExitCode.INTERNAL_FAILURE)


def _run_watch_invocation(
    *, invocation: WatchInvocation, stdout: TextIO, stderr: TextIO
) -> int:
    normalized_invocation = _revalidate_watch_invocation_outputs(invocation)
    watch_event_request = normalized_invocation.unstable_event_request
    with guard_stdout_for_machine_output(
        enabled=watch_event_request is not None and watch_event_request.writes_to_stdout,
        stderr=stderr,
    ):
        result = run_watch(normalized_invocation, stdout=stdout)
        _emit_watch_terminal_report(
            report_request=normalized_invocation.report_request,
            watch_event_request=watch_event_request,
            report=result.report,
            text_output=result.text_output,
            stdout=stdout,
            stderr=stderr,
        )
    return int(result.exit_code)


def _run_non_watch_invocation(
    *, invocation: PlanInvocation | CheckInvocation | BuildInvocation, stdout: TextIO
) -> int:
    result = dispatch_command(invocation)
    emit_report(
        request=_revalidate_report_request_for_layout(
            layout=invocation.layout,
            request=invocation.report_request,
        ),
        report=result.report,
        text_output=result.text_output,
        stdout=stdout,
    )
    return int(result.exit_code)


def _run_component_source_roots_invocation(
    *, invocation: ComponentSourceRootsInvocation, stdout: TextIO
) -> int:
    source_roots = run_component_source_roots(invocation)
    if source_roots:
        stdout.write("".join(f"{path}\n" for path in source_roots))
        stdout.flush()
    return int(ApplicationExitCode.SUCCESS)


def _revalidate_watch_invocation_outputs(invocation: WatchInvocation) -> WatchInvocation:
    report_request = _revalidate_report_request_for_layout(
        layout=invocation.layout,
        request=invocation.report_request,
    )
    watch_event_request = revalidate_watch_event_request(
        cwd=invocation.layout.cwd,
        request=invocation.unstable_event_request,
        forbidden_roots=(invocation.layout.stage_root, invocation.layout.work_root),
    )
    if (
        watch_event_request is not None
        and watch_event_request.output_path is not None
        and report_request.output_path is not None
        and watch_event_request.output_path == report_request.output_path
    ):
        raise InvocationError("--unstable-events-output must differ from --report-output")
    return WatchInvocation(
        layout=invocation.layout,
        fail_on_severity=invocation.fail_on_severity,
        report_request=report_request,
        unstable_event_request=watch_event_request,
    )


def _revalidate_report_request_for_layout(
    *, layout: RepositoryLayout, request: ReportRequest
) -> ReportRequest:
    if request.output_path is None:
        return request
    return revalidate_report_request(
        cwd=layout.cwd,
        request=request,
        forbidden_roots=(layout.stage_root, layout.work_root),
    )


def _emit_watch_terminal_report(
    *,
    report_request: ReportRequest,
    watch_event_request: WatchEventRequest | None,
    report: ReportModel,
    text_output: str,
    stdout: TextIO,
    stderr: TextIO,
) -> None:
    if report_request.output_path is not None:
        return
    if watch_event_request is None or not watch_event_request.writes_to_stdout:
        emit_report(
            request=report_request,
            report=report,
            text_output=text_output,
            stdout=stdout,
        )
        return
    _write_stream_output(stderr, text_output)


def parse_invocation(argv: Sequence[str] | None = None) -> CommandInvocation:
    """Parse CLI arguments into a typed invocation object."""

    parser = _build_parser()
    namespace = parser.parse_args(argv)
    cwd = Path.cwd().resolve()
    workspace_root = (
        _resolve_cli_path(cwd=cwd, raw_path=namespace.workspace_root)
        if namespace.workspace_root
        else cwd
    )
    catalog_path = (
        _resolve_cli_path(cwd=cwd, raw_path=namespace.catalog)
        if namespace.catalog
        else workspace_root / "site/catalog.yaml"
    )
    site_root = catalog_path.parent
    layout = RepositoryLayout(
        cwd=cwd,
        workspace_root=workspace_root,
        catalog_path=catalog_path,
        site_root=site_root,
        stage_root=site_root / ".stage",
        work_root=site_root / ".site-pipeline-work",
    )
    report_request = None
    watch_event_request = None
    if namespace.command in {"plan", "check", "build", "watch"}:
        report_request = build_report_request(
            cwd=cwd,
            report_format=namespace.report_format,
            schema_version=namespace.report_schema_version,
            report_output=namespace.report_output,
            forbidden_roots=(layout.stage_root, layout.work_root),
            forbid_stdout_json=namespace.command == "watch",
        )
        watch_event_request = build_watch_event_request(
            cwd=cwd,
            event_format=namespace.unstable_events
            if namespace.command == "watch"
            else None,
            event_output=namespace.unstable_events_output
            if namespace.command == "watch"
            else None,
            forbidden_roots=(layout.stage_root, layout.work_root),
        )
        if (
            watch_event_request is not None
            and watch_event_request.output_path is not None
            and report_request.output_path is not None
            and watch_event_request.output_path == report_request.output_path
        ):
            raise InvocationError(
                "--unstable-events-output must differ from --report-output"
            )

    if namespace.command == "plan":
        if report_request is None:
            raise AssertionError("plan requires a report request")
        return PlanInvocation(
            layout=layout,
            planning_target=PlanningTarget(namespace.planning_target),
            report_request=report_request,
        )
    if namespace.command == "check":
        if report_request is None:
            raise AssertionError("check requires a report request")
        return CheckInvocation(
            layout=layout,
            fail_on_severity=CheckFailureThreshold(namespace.fail_on_severity),
            report_request=report_request,
        )
    if namespace.command == "build":
        if report_request is None:
            raise AssertionError("build requires a report request")
        return BuildInvocation(layout=layout, report_request=report_request)
    if namespace.command == "component-source-roots":
        return ComponentSourceRootsInvocation(layout=layout)
    if report_request is None:
        raise AssertionError("watch requires a report request")
    return WatchInvocation(
        layout=layout,
        fail_on_severity=CheckFailureThreshold(namespace.fail_on_severity),
        report_request=report_request,
        unstable_event_request=watch_event_request,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(prog="site-pipeline", allow_abbrev=False)
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan", allow_abbrev=False)
    _add_workspace_arguments(plan_parser)
    _add_logging_arguments(plan_parser)
    plan_parser.add_argument(
        "--for",
        dest="planning_target",
        choices=[value.value for value in PlanningTarget],
        default=PlanningTarget.BUILD.value,
    )
    _add_report_arguments(plan_parser)

    check_parser = subparsers.add_parser("check", allow_abbrev=False)
    _add_workspace_arguments(check_parser)
    _add_logging_arguments(check_parser)
    check_parser.add_argument(
        "--fail-on",
        dest="fail_on_severity",
        choices=[value.value for value in CheckFailureThreshold],
        default=CheckFailureThreshold.ERROR.value,
    )
    _add_report_arguments(check_parser)

    build_parser = subparsers.add_parser("build", allow_abbrev=False)
    _add_workspace_arguments(build_parser)
    _add_logging_arguments(build_parser)
    _add_report_arguments(build_parser)

    component_source_roots_parser = subparsers.add_parser(
        "component-source-roots", allow_abbrev=False
    )
    _add_workspace_arguments(component_source_roots_parser)
    _add_logging_arguments(component_source_roots_parser)

    watch_parser = subparsers.add_parser("watch", allow_abbrev=False)
    _add_workspace_arguments(watch_parser)
    _add_logging_arguments(watch_parser)
    watch_parser.add_argument(
        "--fail-on",
        dest="fail_on_severity",
        choices=[value.value for value in CheckFailureThreshold],
        default=CheckFailureThreshold.ERROR.value,
    )
    watch_parser.add_argument(
        "--unstable-events",
        choices=[value.value for value in WatchEventFormat],
        default=None,
        help="Emit unstable machine-readable watch events using the selected encoding.",
    )
    watch_parser.add_argument(
        "--unstable-events-output",
        metavar="PATH|-",
        default=None,
        help="Write unstable watch events to PATH or '-' for stdout (default).",
    )
    _add_report_arguments(watch_parser)
    return parser


def _add_workspace_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace-root", default=None)
    parser.add_argument("--catalog", default=None)


def _add_report_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--report-format", choices=["text", "json"], default="text")
    parser.add_argument("--report-schema-version", type=int, default=None)
    parser.add_argument("--report-output", default="-")


def _add_logging_arguments(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress lifecycle and informational human logs; warnings/errors still go to stderr.",
    )
    group.add_argument(
        "--verbose",
        action="store_true",
        help="Write informational human logs to stderr in addition to default lifecycle progress logs.",
    )
    group.add_argument(
        "--debug",
        action="store_true",
        help="Write detailed debugging diagnostics to stderr in addition to verbose logs.",
    )


def _resolve_cli_path(*, cwd: Path, raw_path: str) -> Path:
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = cwd / candidate
    return candidate.absolute()


def _emit_error(message: str, *, stderr: TextIO) -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        _LOGGER.error("site-pipeline: %s", message)
        return
    stderr.write(f"site-pipeline: {message}\n")
    stderr.flush()


def _write_stream_output(stream: TextIO, message: str) -> None:
    stream.write(message)
    if not message.endswith("\n"):
        stream.write("\n")
    stream.flush()
