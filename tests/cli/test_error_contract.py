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

"""Stable human and JSON contracts for failures before a command report exists."""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from buildish_site_pipeline.cli import _run, parse_invocation
from buildish_site_pipeline.cli.dispatch import dispatch_command
from buildish_site_pipeline.cli.main import _build_parser
from buildish_site_pipeline.models.emitted.cli_failure import CliFailureReportV1

from tests.support.workspace import _cwd, _workspace


class CliErrorContractTests(unittest.TestCase):
    def test_help_describes_command_goals_and_shared_input_flags(self) -> None:
        parser = _build_parser()
        root_help = parser.format_help()

        for expected in (
            "Validate, plan, and stage renderer-neutral documentation-site inputs.",
            "plan",
            "check",
            "build",
            "component-source-roots",
            "watch",
        ):
            self.assertIn(expected, root_help)

        check_help = io.StringIO()
        with redirect_stdout(check_help), self.assertRaises(SystemExit) as raised:
            parser.parse_args(["check", "--help"])

        self.assertEqual(raised.exception.code, 0)
        for expected in (
            "Validate the workspace using the same gates required by build.",
            "--workspace-root PATH",
            "--catalog PATH",
            "--fail-on",
            "--report-format",
            "--report-output",
        ):
            self.assertIn(expected, check_help.getvalue())

    def test_schema_failure_human_output_includes_code_source_and_location(self) -> None:
        with _workspace() as workspace_root:
            catalog_path = workspace_root / "site/catalog.yaml"
            catalog_path.write_text(
                catalog_path.read_text(encoding="utf-8") + "unexpectedRoot: true\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            stderr = io.StringIO()

            with _cwd(workspace_root):
                exit_code = _run(argv=["check"], stdout=stdout, stderr=stderr)

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("input-validation-failed", stderr.getvalue())
        self.assertIn("[site/catalog.yaml]", stderr.getvalue())
        self.assertIn("unexpectedRoot", stderr.getvalue())
        self.assertNotIn(str(workspace_root), stderr.getvalue())

    def test_schema_failure_json_stdout_uses_distinct_failure_envelope(self) -> None:
        with _workspace() as workspace_root:
            catalog_path = workspace_root / "site/catalog.yaml"
            catalog_path.write_text(
                catalog_path.read_text(encoding="utf-8") + "unexpectedRoot: true\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            stderr = io.StringIO()

            with _cwd(workspace_root):
                exit_code = _run(
                    argv=[
                        "check",
                        "--report-format",
                        "json",
                        "--report-schema-version",
                        "1",
                    ],
                    stdout=stdout,
                    stderr=stderr,
                )

        report = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(report["schemaVersion"], 1)
        self.assertEqual(report["kind"], "cliFailure")
        self.assertEqual(report["command"], "check")
        self.assertEqual(report["exitCode"], 1)
        self.assertEqual(report["error"]["category"], "input")
        self.assertEqual(report["error"]["code"], "input-validation-failed")
        self.assertEqual(report["error"]["source"], "site/catalog.yaml")
        self.assertEqual(report["error"]["issues"][0]["location"], "unexpectedRoot")
        self.assertEqual(
            CliFailureReportV1.model_validate(report).to_json_payload(),
            report,
        )
        self.assertNotIn(str(workspace_root), stdout.getvalue())

    def test_json_input_failure_honors_report_output_file(self) -> None:
        with _workspace() as workspace_root:
            report_path = workspace_root / "failure.json"
            (workspace_root / "site/provider-snapshot.json").write_bytes(b"\xff")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with _cwd(workspace_root):
                exit_code = _run(
                    argv=[
                        "plan",
                        "--report-format",
                        "json",
                        "--report-schema-version",
                        "1",
                        "--report-output",
                        str(report_path),
                    ],
                    stdout=stdout,
                    stderr=stderr,
                )
            report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(report["error"]["code"], "input-encoding-invalid")

    def test_json_loader_failures_have_stable_codes(self) -> None:
        cases = {
            "syntax": (b'{"schemaVersion": 1,', "input-syntax-invalid"),
            "duplicate": (
                b'{"schemaVersion":1,"providers":[],"secretDuplicateName":[],"secretDuplicateName":[]}',
                "input-duplicate-key",
            ),
            "missing-version": (
                b'{"providers":[],"records":[]}',
                "input-schema-version-missing",
            ),
            "unsupported-version": (
                b'{"schemaVersion":2,"providers":[],"records":[]}',
                "input-schema-version-unsupported",
            ),
            "wrong-root-type": (b"[]", "input-root-type-invalid"),
        }
        for name, (document, expected_code) in cases.items():
            with self.subTest(name=name), _workspace() as workspace_root:
                (workspace_root / "site/provider-snapshot.json").write_bytes(document)
                stdout = io.StringIO()
                stderr = io.StringIO()

                with _cwd(workspace_root):
                    exit_code = _run(
                        argv=[
                            "check",
                            "--report-format",
                            "json",
                            "--report-schema-version",
                            "1",
                        ],
                        stdout=stdout,
                        stderr=stderr,
                    )

                report = json.loads(stdout.getvalue())
                self.assertEqual(exit_code, 1)
                self.assertEqual(stderr.getvalue(), "")
                self.assertEqual(report["error"]["code"], expected_code)
                if name == "duplicate":
                    self.assertNotIn("secretDuplicateName", stdout.getvalue())

    def test_yaml_syntax_failure_uses_the_same_machine_contract(self) -> None:
        with _workspace() as workspace_root:
            (workspace_root / "site/catalog.yaml").write_text(
                "schemaVersion: 1\ncomponents: [\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            stderr = io.StringIO()

            with _cwd(workspace_root):
                exit_code = _run(
                    argv=[
                        "check",
                        "--report-format",
                        "json",
                        "--report-schema-version",
                        "1",
                    ],
                    stdout=stdout,
                    stderr=stderr,
                )

        report = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(report["error"]["category"], "input")
        self.assertEqual(report["error"]["code"], "input-syntax-invalid")
        self.assertEqual(report["error"]["source"], "site/catalog.yaml")

    def test_external_input_source_redacts_parent_directories(self) -> None:
        with _workspace() as workspace_root, tempfile.TemporaryDirectory() as external:
            external_catalog = Path(external) / "catalog.yaml"
            external_catalog.write_text(
                (workspace_root / "site/catalog.yaml").read_text(encoding="utf-8")
                + "unexpectedRoot: true\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            stderr = io.StringIO()

            with _cwd(workspace_root):
                exit_code = _run(
                    argv=[
                        "check",
                        "--catalog",
                        str(external_catalog),
                        "--report-format",
                        "json",
                        "--report-schema-version",
                        "1",
                    ],
                    stdout=stdout,
                    stderr=stderr,
                )

        report = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(report["error"]["source"], "<external-input>/catalog.yaml")
        self.assertNotIn(external, stdout.getvalue())

    def test_oversized_validation_location_is_bounded(self) -> None:
        oversized_field = "private-field-" + ("x" * 10_000)
        with _workspace() as workspace_root:
            provider_path = workspace_root / "site/provider-snapshot.json"
            provider = json.loads(provider_path.read_text(encoding="utf-8"))
            provider[oversized_field] = True
            provider_path.write_text(json.dumps(provider), encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with _cwd(workspace_root):
                exit_code = _run(
                    argv=[
                        "check",
                        "--report-format",
                        "json",
                        "--report-schema-version",
                        "1",
                    ],
                    stdout=stdout,
                    stderr=stderr,
                )

        report = json.loads(stdout.getvalue())
        location = report["error"]["issues"][0]["location"]
        self.assertEqual(exit_code, 1)
        self.assertEqual(stderr.getvalue(), "")
        self.assertLessEqual(len(location), 200)
        self.assertTrue(location.endswith("…"))
        self.assertNotIn(oversized_field, stdout.getvalue())
        self.assertLess(len(stdout.getvalue()), 2_000)

    def test_validation_issue_count_is_bounded_and_reports_omissions(self) -> None:
        with _workspace() as workspace_root:
            provider_path = workspace_root / "site/provider-snapshot.json"
            provider = json.loads(provider_path.read_text(encoding="utf-8"))
            provider.update({f"unknownField{index}": True for index in range(25)})
            provider_path.write_text(json.dumps(provider), encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with _cwd(workspace_root):
                exit_code = _run(
                    argv=[
                        "check",
                        "--report-format",
                        "json",
                        "--report-schema-version",
                        "1",
                    ],
                    stdout=stdout,
                    stderr=stderr,
                )

        report = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(len(report["error"]["issues"]), 20)
        self.assertEqual(report["error"]["omittedIssueCount"], 5)

    def test_missing_input_uses_domain_exit_and_not_found_code(self) -> None:
        with _workspace() as workspace_root:
            (workspace_root / "site/catalog.yaml").unlink()
            stdout = io.StringIO()
            stderr = io.StringIO()

            with _cwd(workspace_root):
                exit_code = _run(
                    argv=[
                        "check",
                        "--report-format",
                        "json",
                        "--report-schema-version",
                        "1",
                    ],
                    stdout=stdout,
                    stderr=stderr,
                )

        report = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(report["error"]["code"], "input-not-found")

    def test_filesystem_read_failure_has_stable_code_without_os_details(self) -> None:
        with _workspace() as workspace_root:
            stdout = io.StringIO()
            stderr = io.StringIO()

            with mock.patch(
                "pathlib.Path.open",
                side_effect=PermissionError("private operating-system detail"),
            ), _cwd(workspace_root):
                exit_code = _run(
                    argv=[
                        "check",
                        "--report-format",
                        "json",
                        "--report-schema-version",
                        "1",
                    ],
                    stdout=stdout,
                    stderr=stderr,
                )

        report = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(report["error"]["code"], "input-read-failed")
        self.assertNotIn("private operating-system detail", stdout.getvalue())

    def test_wrong_input_file_type_has_stable_filesystem_category(self) -> None:
        with _workspace() as workspace_root:
            stdout = io.StringIO()
            stderr = io.StringIO()

            with _cwd(workspace_root):
                exit_code = _run(
                    argv=[
                        "check",
                        "--catalog",
                        "site",
                        "--report-format",
                        "json",
                        "--report-schema-version",
                        "1",
                    ],
                    stdout=stdout,
                    stderr=stderr,
                )

        report = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(report["error"]["category"], "input")
        self.assertEqual(report["error"]["code"], "input-not-file")

    def test_expected_planning_rejection_is_not_an_internal_failure(self) -> None:
        with _workspace() as workspace_root:
            provider_path = workspace_root / "site/provider-snapshot.json"
            provider = json.loads(provider_path.read_text(encoding="utf-8"))
            provider["records"][0]["artifactKey"] = "missing"
            provider_path.write_text(json.dumps(provider), encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()

            with _cwd(workspace_root):
                exit_code = _run(
                    argv=[
                        "plan",
                        "--report-format",
                        "json",
                        "--report-schema-version",
                        "1",
                    ],
                    stdout=stdout,
                    stderr=stderr,
                )

        report = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 1)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(report["error"]["category"], "planning")
        self.assertEqual(report["error"]["code"], "planning-input-invalid")

    def test_unexpected_failure_does_not_expose_exception_details(self) -> None:
        with _workspace() as workspace_root:
            stdout = io.StringIO()
            stderr = io.StringIO()

            with mock.patch(
                "buildish_site_pipeline.cli.main.dispatch_command",
                side_effect=RuntimeError("private implementation detail"),
            ), _cwd(workspace_root):
                exit_code = _run(
                    argv=[
                        "plan",
                        "--report-format",
                        "json",
                        "--report-schema-version",
                        "1",
                    ],
                    stdout=stdout,
                    stderr=stderr,
                )

        report = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 3)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(report["error"]["category"], "internal")
        self.assertEqual(report["error"]["code"], "internal-unexpected-failure")
        self.assertNotIn("private implementation detail", stdout.getvalue())

    def test_valid_json_report_serialization_is_unchanged(self) -> None:
        argv = [
            "plan",
            "--report-format",
            "json",
            "--report-schema-version",
            "1",
        ]
        with _workspace() as workspace_root, _cwd(workspace_root):
            invocation = parse_invocation(argv)
            result = dispatch_command(invocation)
            expected = result.report.model_dump_json(indent=2, exclude_none=True) + "\n"
            stdout = io.StringIO()
            stderr = io.StringIO()

            with mock.patch(
                "buildish_site_pipeline.cli.main.dispatch_command",
                return_value=result,
            ):
                exit_code = _run(argv=argv, stdout=stdout, stderr=stderr)

        self.assertEqual(exit_code, int(result.exit_code))
        self.assertEqual(stdout.getvalue(), expected)
        self.assertEqual(stderr.getvalue(), "")
        self.assertNotIn('"kind": "cliFailure"', stdout.getvalue())
