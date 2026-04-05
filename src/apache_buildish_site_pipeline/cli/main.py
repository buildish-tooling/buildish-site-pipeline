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

"""Command-line entry point for the site pipeline."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
import sys
from pathlib import Path
from typing import Never, TextIO

from apache_buildish_site_pipeline.models.enums import CheckFailureThreshold, PlanningTarget

from ..commands.watch import run_watch
from .contract import (
    ApplicationExitCode,
    BuildInvocation,
    CheckInvocation,
    CommandInvocation,
    PlanInvocation,
    RepositoryLayout,
    WatchEventFormat,
    WatchInvocation,
)
from .dispatch import dispatch_command
from .errors import CommandExecutionError, InvocationError, SitePipelineCliError
from .reporting import build_report_request, emit_report, revalidate_report_request


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        raise InvocationError(message)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return the process exit code."""

    return _run(argv=argv, stdout=sys.stdout, stderr=sys.stderr)


def _run(*, argv: Sequence[str] | None, stdout: TextIO, stderr: TextIO) -> int:
    try:
        invocation = parse_invocation(argv)
        if isinstance(invocation, WatchInvocation):
            result = run_watch(invocation, stdout=stdout, stderr=stderr)
            if invocation.report_request.output_path is None:
                if invocation.unstable_event_format is None:
                    emit_report(
                        request=invocation.report_request,
                        report=result.report,
                        text_output=result.text_output,
                        stdout=stdout,
                    )
                else:
                    _write_stream_output(stderr, result.text_output)
            return int(result.exit_code)

        result = dispatch_command(invocation)
        report_request = invocation.report_request
        if report_request.output_path is not None:
            report_request = revalidate_report_request(
                cwd=invocation.layout.cwd,
                request=report_request,
                forbidden_roots=(invocation.layout.stage_root, invocation.layout.work_root),
            )
        emit_report(
            request=report_request,
            report=result.report,
            text_output=result.text_output,
            stdout=stdout,
        )
        return int(result.exit_code)
    except InvocationError as exc:
        _write_error(stderr, str(exc))
        return int(ApplicationExitCode.INVOCATION_ERROR)
    except CommandExecutionError as exc:
        _write_error(stderr, str(exc))
        return int(ApplicationExitCode.INTERNAL_FAILURE)
    except SitePipelineCliError as exc:
        _write_error(stderr, str(exc))
        return int(ApplicationExitCode.INTERNAL_FAILURE)


def parse_invocation(argv: Sequence[str] | None = None) -> CommandInvocation:
    """Parse CLI arguments into a typed invocation object."""

    parser = _build_parser()
    namespace = parser.parse_args(argv)
    cwd = Path.cwd().resolve()
    workspace_root = _resolve_cli_path(cwd=cwd, raw_path=namespace.workspace_root) if namespace.workspace_root else cwd
    catalog_path = (
        _resolve_cli_path(cwd=cwd, raw_path=namespace.catalog)
        if namespace.catalog
        else workspace_root / "site/components.yaml"
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
    report_request = build_report_request(
        cwd=cwd,
        report_format=namespace.report_format,
        schema_version=namespace.report_schema_version,
        report_output=namespace.report_output,
        forbidden_roots=(layout.stage_root, layout.work_root),
        forbid_stdout_json=namespace.command == "watch",
    )

    if namespace.command == "plan":
        return PlanInvocation(
            layout=layout,
            planning_target=PlanningTarget(namespace.planning_target),
            report_request=report_request,
        )
    if namespace.command == "check":
        return CheckInvocation(
            layout=layout,
            fail_on_severity=CheckFailureThreshold(namespace.fail_on_severity),
            report_request=report_request,
        )
    if namespace.command == "build":
        return BuildInvocation(layout=layout, report_request=report_request)
    return WatchInvocation(
        layout=layout,
        fail_on_severity=CheckFailureThreshold(namespace.fail_on_severity),
        report_request=report_request,
        unstable_event_format=WatchEventFormat(namespace.unstable_events) if namespace.unstable_events is not None else None,
        verbose=bool(namespace.verbose or namespace.debug),
        debug=bool(namespace.debug),
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(prog="site-pipeline", allow_abbrev=False)
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan", allow_abbrev=False)
    _add_workspace_arguments(plan_parser)
    plan_parser.add_argument("--for", dest="planning_target", choices=[value.value for value in PlanningTarget], default=PlanningTarget.BUILD.value)
    _add_report_arguments(plan_parser)

    check_parser = subparsers.add_parser("check", allow_abbrev=False)
    _add_workspace_arguments(check_parser)
    check_parser.add_argument(
        "--fail-on",
        dest="fail_on_severity",
        choices=[value.value for value in CheckFailureThreshold],
        default=CheckFailureThreshold.ERROR.value,
    )
    _add_report_arguments(check_parser)

    build_parser = subparsers.add_parser("build", allow_abbrev=False)
    _add_workspace_arguments(build_parser)
    _add_report_arguments(build_parser)

    watch_parser = subparsers.add_parser("watch", allow_abbrev=False)
    _add_workspace_arguments(watch_parser)
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
        help="Emit unstable machine-readable watch events to stdout using the selected encoding.",
    )
    watch_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Write human-facing watch cycle summaries to stderr.",
    )
    watch_parser.add_argument(
        "--debug",
        action="store_true",
        help="Write verbose watch summaries plus dirty-path/debug details to stderr.",
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


def _resolve_cli_path(*, cwd: Path, raw_path: str) -> Path:
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = cwd / candidate
    return candidate.absolute()


def _write_error(stderr: TextIO, message: str) -> None:
    stderr.write(f"site-pipeline: {message}\n")
    stderr.flush()


def _write_stream_output(stream: TextIO, message: str) -> None:
    stream.write(message)
    if not message.endswith("\n"):
        stream.write("\n")
    stream.flush()