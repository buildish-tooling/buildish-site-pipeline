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

"""Tests for typed internal reference validation."""

from __future__ import annotations

import unittest

from buildish_site_pipeline.models.validation.references import validate_reference_string


class ReferenceValidationTests(unittest.TestCase):
    """Exercise the shared typed-reference validator."""

    def test_accepts_supported_reference_kinds(self) -> None:
        for value in (
            "route:/docs/development/",
            "component:spark",
            "artifact:spark/runtime",
            "line:spark/runtime@4.x",
            "release:spark/runtime@4.0.0",
        ):
            with self.subTest(value=value):
                self.assertEqual(validate_reference_string(value), value)

    def test_rejects_unknown_prefixes_and_malformed_payloads(self) -> None:
        for value in (
            "unknown:spark",
            "artifact:spark",
            "line:spark/runtime",
            "route:docs/latest/",
            "component:Spark",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_reference_string(value)

    def test_rejects_missing_typed_separator_or_empty_payload(self) -> None:
        for value in ("component", "component:"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_reference_string(value)

    def test_rejects_line_and_release_references_with_empty_qualifier(self) -> None:
        for value in ("line:spark/runtime@", "release:spark/runtime@"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_reference_string(value)