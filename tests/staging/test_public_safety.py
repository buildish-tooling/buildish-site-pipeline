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

"""Tests for public-output diagnostic sanitization helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from apache_buildish_site_pipeline.models.enums import DiagnosticSeverity
from apache_buildish_site_pipeline.models.emitted.planning_stage_contract import (
    PipelineDiagnosticEntry,
    ReducedDiagnosticDetailsSummary,
)
from apache_buildish_site_pipeline.staging.public_safety import (
    REDACTED_LOCAL_PATH,
    public_source_path,
    sanitize_public_diagnostics,
)


class PublicSafetyTests(unittest.TestCase):
    """Exercise privacy-preserving stage-output sanitization branches directly."""

    def test_redacts_local_detail_fields_outside_workspace_by_field_name(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            sanitized = sanitize_public_diagnostics(
                (
                    PipelineDiagnosticEntry(
                        severity=DiagnosticSeverity.WARNING,
                        code="demo.warning",
                        message="demo",
                        details={"sourcePath": "/opt/private/source.md"},
                    ),
                ),
                workspace_root=workspace_root,
            )

        self.assertEqual(sanitized[0].details["sourcePath"], REDACTED_LOCAL_PATH)

    def test_preserves_non_string_detail_values(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            sanitized = sanitize_public_diagnostics(
                (
                    PipelineDiagnosticEntry(
                        severity=DiagnosticSeverity.WARNING,
                        code="demo.warning",
                        message="demo",
                        details={"count": 7, "items": [True, 3, {"note": None}]},
                    ),
                ),
                workspace_root=workspace_root,
            )

        self.assertEqual(sanitized[0].details["count"], 7)
        self.assertEqual(sanitized[0].details["items"], [True, 3, {"note": None}])

    def test_preserves_absolute_paths_for_explicit_public_route_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            sanitized = sanitize_public_diagnostics(
                (
                    PipelineDiagnosticEntry(
                        severity=DiagnosticSeverity.WARNING,
                        code="demo.warning",
                        message="demo",
                        details={
                            "mirrorPath": "/srv/public/mirror/index.json",
                            "relativeHint": "docs/index.md",
                        },
                    ),
                ),
                workspace_root=workspace_root,
            )

        self.assertEqual(
            sanitized[0].details["mirrorPath"],
            "/srv/public/mirror/index.json",
        )
        self.assertEqual(sanitized[0].details["relativeHint"], "docs/index.md")

    def test_redacts_absolute_paths_for_unknown_field_names(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            sanitized = sanitize_public_diagnostics(
                (
                    PipelineDiagnosticEntry(
                        severity=DiagnosticSeverity.WARNING,
                        code="demo.warning",
                        message="demo",
                        details={
                            "unexpectedPath": "/srv/private/build/root/output.json",
                            "nested": {
                                "otherPath": "/srv/private/render-cache/result.json"
                            },
                        },
                    ),
                ),
                workspace_root=workspace_root,
            )

        self.assertEqual(sanitized[0].details["unexpectedPath"], REDACTED_LOCAL_PATH)
        self.assertEqual(
            sanitized[0].details["nested"]["otherPath"],
            REDACTED_LOCAL_PATH,
        )

    def test_public_source_path_returns_repo_relative_path_only_for_workspace_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            self.assertEqual(
                public_source_path(
                    source_path=str(workspace_root / "components/runtime/docs/index.md"),
                    workspace_root=workspace_root,
                ),
                "components/runtime/docs/index.md",
            )
            self.assertIsNone(
                public_source_path(
                    source_path="/srv/external/docs/index.md",
                    workspace_root=workspace_root,
                )
            )

    def test_leaves_reduced_detail_summaries_unchanged(self) -> None:
        summary = ReducedDiagnosticDetailsSummary(
            omitted=True,
            reason="sizeLimitExceeded",
            actual_bytes=20,
            limit_bytes=10,
            summary="trimmed",
        )
        entry = PipelineDiagnosticEntry(
            severity=DiagnosticSeverity.WARNING,
            code="demo.warning",
            message="demo",
            details=summary,
        )

        sanitized = sanitize_public_diagnostics((entry,), workspace_root=Path("/workspace"))

        self.assertIs(sanitized[0], entry)