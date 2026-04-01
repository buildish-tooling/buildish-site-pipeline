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

"""Boundary coverage for provider input reads before decode and parsing."""

from __future__ import annotations

import unittest
from unittest import mock

from buildish_site_pipeline.cli.errors import InputDiagnosticError
from buildish_site_pipeline.commands import shared as shared_module
from buildish_site_pipeline.commands.shared import load_workspace_inputs
from buildish_site_pipeline.evaluation import limits as evaluation_limits
from buildish_site_pipeline.planning import provider_index
from buildish_site_pipeline.resource_limits import DEFAULT_PROVIDER_SNAPSHOT_BYTES

from tests.support.workspace import _workspace


_MINIMAL_PROVIDER_JSON = b'{"schemaVersion":1,"providers":[],"records":[]}'


class ProviderInputBoundaryTests(unittest.TestCase):
    def test_documented_raw_provider_limit_is_sixteen_mibibytes(self) -> None:
        self.assertEqual(DEFAULT_PROVIDER_SNAPSHOT_BYTES, 16 * 1024 * 1024)
        self.assertEqual(
            shared_module.DEFAULT_PROVIDER_SNAPSHOT_BYTES,
            DEFAULT_PROVIDER_SNAPSHOT_BYTES,
        )
        self.assertEqual(
            provider_index.DEFAULT_PROVIDER_SNAPSHOT_BYTES,
            DEFAULT_PROVIDER_SNAPSHOT_BYTES,
        )
        self.assertEqual(
            evaluation_limits.DEFAULT_PROVIDER_SNAPSHOT_BYTES,
            DEFAULT_PROVIDER_SNAPSHOT_BYTES,
        )

    def test_exact_raw_byte_limit_is_accepted(self) -> None:
        with _workspace() as workspace_root:
            provider_path = workspace_root / "site/provider-snapshot.json"
            provider_path.write_bytes(_MINIMAL_PROVIDER_JSON)

            with mock.patch.object(
                shared_module,
                "DEFAULT_PROVIDER_SNAPSHOT_BYTES",
                len(_MINIMAL_PROVIDER_JSON),
            ):
                loaded = load_workspace_inputs(workspace_root)

        self.assertEqual(loaded.provider_snapshot.records, [])

    def test_limit_plus_one_is_rejected_before_provider_parsing(self) -> None:
        document = _MINIMAL_PROVIDER_JSON + b" "
        with _workspace() as workspace_root:
            provider_path = workspace_root / "site/provider-snapshot.json"
            provider_path.write_bytes(document)

            with (
                mock.patch.object(
                    shared_module,
                    "DEFAULT_PROVIDER_SNAPSHOT_BYTES",
                    len(document) - 1,
                ),
                mock.patch.object(
                    shared_module,
                    "load_provider_snapshot_document",
                ) as load_document,
                self.assertRaises(InputDiagnosticError) as raised,
            ):
                load_workspace_inputs(workspace_root)

        load_document.assert_not_called()
        self.assertEqual(
            raised.exception.diagnostic.code,
            "input-size-limit-exceeded",
        )
        issue = raised.exception.diagnostic.issues[0]
        self.assertIn("read at least", issue.message)
        self.assertEqual(issue.actual_bytes, len(document))
        self.assertEqual(issue.limit_bytes, len(document) - 1)

    def test_whitespace_heavy_document_is_bounded_by_raw_not_normalized_size(self) -> None:
        document = _MINIMAL_PROVIDER_JSON + (b" " * 128)
        with _workspace() as workspace_root:
            (workspace_root / "site/provider-snapshot.json").write_bytes(document)

            with mock.patch.object(
                shared_module,
                "DEFAULT_PROVIDER_SNAPSHOT_BYTES",
                len(_MINIMAL_PROVIDER_JSON),
            ), self.assertRaises(InputDiagnosticError) as raised:
                load_workspace_inputs(workspace_root)

        self.assertEqual(
            raised.exception.diagnostic.code,
            "input-size-limit-exceeded",
        )

    def test_multibyte_utf8_is_counted_as_raw_bytes(self) -> None:
        document = b"schemaVersion: 1\nproviders: []\nrecords: []\n# " + "é".encode()
        with _workspace() as workspace_root:
            (workspace_root / "site/provider-snapshot.json").unlink()
            (workspace_root / "site/provider-snapshot.yaml").write_bytes(document)

            with mock.patch.object(
                shared_module,
                "DEFAULT_PROVIDER_SNAPSHOT_BYTES",
                len(document) - 1,
            ), self.assertRaises(InputDiagnosticError) as raised:
                load_workspace_inputs(workspace_root)

        self.assertEqual(
            raised.exception.diagnostic.code,
            "input-size-limit-exceeded",
        )

    def test_invalid_utf8_within_limit_gets_stable_encoding_code(self) -> None:
        document = _MINIMAL_PROVIDER_JSON + b"\xff"
        with _workspace() as workspace_root:
            (workspace_root / "site/provider-snapshot.json").write_bytes(document)

            with mock.patch.object(
                shared_module,
                "DEFAULT_PROVIDER_SNAPSHOT_BYTES",
                len(document),
            ), self.assertRaises(InputDiagnosticError) as raised:
                load_workspace_inputs(workspace_root)

        self.assertEqual(
            raised.exception.diagnostic.code,
            "input-encoding-invalid",
        )
