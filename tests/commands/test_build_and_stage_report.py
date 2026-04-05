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

"""Direct coverage for build-command and stage-report helper branches."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import mock

import apache_buildish_site_pipeline.commands.build as build_command
from apache_buildish_site_pipeline.cli.contract import (
    ApplicationExitCode,
    BuildInvocation,
    ReportFormat,
    ReportRequest,
    RepositoryLayout,
)
from apache_buildish_site_pipeline.commands.stage_report import _report_workspace_root
from apache_buildish_site_pipeline.models.enums import DiagnosticSeverity, StageCommand
from apache_buildish_site_pipeline.models.planning_stage_contract import (
    PipelineDiagnosticEntry,
)


class BuildAndStageReportTests(unittest.TestCase):
    def test_run_build_returns_domain_failure_when_stage_gate_blocks_publication(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            invocation = self._build_invocation(workspace_root)
            evaluation = SimpleNamespace(
                stage_gate=SimpleNamespace(allowed=False),
                build_plan=None,
                diagnostics=(self._diagnostic("build.blocked"),),
            )
            loaded_inputs = SimpleNamespace(
                catalog=object(),
                provider_snapshot=object(),
                component_documents=object(),
            )

            with mock.patch.object(
                build_command,
                "load_workspace_inputs",
                return_value=loaded_inputs,
            ), mock.patch.object(
                build_command,
                "evaluate_planning",
                return_value=object(),
            ), mock.patch.object(
                build_command,
                "run_evaluation",
                return_value=evaluation,
            ), mock.patch.object(
                build_command,
                "build_stage_run_report",
                return_value="failure-report",
            ) as build_report, mock.patch.object(
                build_command,
                "render_text_report",
                return_value="rendered failure",
            ) as render, mock.patch.object(build_command, "publish_stage") as publish_stage:
                result = build_command.run_build(invocation)

        self.assertEqual(result.exit_code, ApplicationExitCode.DOMAIN_FAILURE)
        self.assertEqual(result.report, "failure-report")
        self.assertEqual(result.text_output, "rendered failure")
        publish_stage.assert_not_called()
        render.assert_called_once_with("failure-report")
        build_report.assert_called_once_with(
            command=StageCommand.BUILD,
            evaluation=evaluation,
            succeeded=False,
            wrote_stage=False,
            stage_usable=False,
            stage_root_path=None,
            manifest_path=None,
            workspace_root=workspace_root,
            private_roots=(invocation.layout.work_root, invocation.layout.stage_root),
        )

    def test_run_build_publishes_stage_when_evaluation_allows_it(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            invocation = self._build_invocation(workspace_root)
            build_plan = object()
            diagnostics = (self._diagnostic("build.ok"),)
            provider_snapshot = object()
            evaluation = SimpleNamespace(
                stage_gate=SimpleNamespace(allowed=True),
                build_plan=build_plan,
                diagnostics=diagnostics,
            )
            publication = SimpleNamespace(
                stage_root=invocation.layout.stage_root,
                manifest_path=invocation.layout.stage_root / "manifest.json",
            )
            loaded_inputs = SimpleNamespace(
                catalog=object(),
                provider_snapshot=provider_snapshot,
                component_documents=object(),
            )

            with mock.patch.object(
                build_command,
                "load_workspace_inputs",
                return_value=loaded_inputs,
            ), mock.patch.object(
                build_command,
                "evaluate_planning",
                return_value=object(),
            ), mock.patch.object(
                build_command,
                "run_evaluation",
                return_value=evaluation,
            ), mock.patch.object(
                build_command,
                "publish_stage",
                return_value=publication,
            ) as publish_stage, mock.patch.object(
                build_command,
                "build_stage_run_report",
                return_value="success-report",
            ) as build_report, mock.patch.object(
                build_command,
                "render_text_report",
                return_value="rendered success",
            ) as render:
                result = build_command.run_build(invocation)

        self.assertEqual(result.exit_code, ApplicationExitCode.SUCCESS)
        self.assertEqual(result.report, "success-report")
        self.assertEqual(result.text_output, "rendered success")
        publish_stage.assert_called_once_with(
            build_plan=build_plan,
            diagnostics=diagnostics,
            provider_snapshot=provider_snapshot,
            stage_root=invocation.layout.stage_root,
        )
        render.assert_called_once_with("success-report")
        build_report.assert_called_once_with(
            command=StageCommand.BUILD,
            evaluation=evaluation,
            succeeded=True,
            wrote_stage=True,
            stage_usable=True,
            stage_root_path=publication.stage_root,
            manifest_path=publication.manifest_path,
            workspace_root=workspace_root,
            private_roots=(invocation.layout.work_root, invocation.layout.stage_root),
        )

    def test_report_workspace_root_returns_none_without_evaluation(self) -> None:
        self.assertIsNone(_report_workspace_root(None))

    def test_report_workspace_root_prefers_build_plan_workspace_root(self) -> None:
        build_plan_root = Path("/workspace/from-build-plan")
        evaluation = SimpleNamespace(
            build_plan=SimpleNamespace(workspace_root=build_plan_root),
            planning=SimpleNamespace(site=SimpleNamespace(workspace_root=Path("/workspace/from-planning"))),
        )

        self.assertEqual(_report_workspace_root(evaluation), build_plan_root)

    @staticmethod
    def _build_invocation(workspace_root: Path) -> BuildInvocation:
        site_root = workspace_root / "site"
        return BuildInvocation(
            layout=RepositoryLayout(
                cwd=workspace_root,
                workspace_root=workspace_root,
                catalog_path=site_root / "components.yaml",
                site_root=site_root,
                stage_root=site_root / ".stage",
                work_root=site_root / ".site-pipeline-work",
            ),
            report_request=ReportRequest(
                report_format=ReportFormat.TEXT,
                schema_version=None,
                output_path=None,
            ),
        )

    @staticmethod
    def _diagnostic(code: str) -> PipelineDiagnosticEntry:
        return PipelineDiagnosticEntry(
            severity=DiagnosticSeverity.ERROR,
            code=code,
            message=code,
        )