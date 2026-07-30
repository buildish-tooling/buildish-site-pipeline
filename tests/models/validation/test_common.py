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

"""Tests for shared scalar validators in models.validation.common."""

from __future__ import annotations

import unittest

from buildish_site_pipeline.models.validation.common import (
    validate_artifact_key,
    validate_identifier,
    validate_provider_key,
    validate_ref_string,
    validate_slug,
    validate_source_key,
    validate_version_string,
)


class CommonValidationTests(unittest.TestCase):
    """Exercise the reusable scalar-string validation helpers directly."""

    def test_accepts_identifier_like_scalar_values(self) -> None:
        for validator, value in (
            (validate_identifier, "stable.id_1"),
            (validate_slug, "spark-runtime"),
            (validate_artifact_key, "spark.runtime"),
            (validate_source_key, "release-notes_v2"),
            (validate_provider_key, "apache-mirror"),
        ):
            with self.subTest(validator=validator.__name__, value=value):
                self.assertEqual(validator(value), value)

    def test_rejects_identifier_like_whitespace_and_character_violations(self) -> None:
        for validator, value in (
            (validate_identifier, " leading"),
            (validate_slug, "internal space"),
            (validate_artifact_key, "bad\x00key"),
            (validate_source_key, "UpperCase"),
            (validate_provider_key, "trailing-"),
        ):
            with self.subTest(validator=validator.__name__, value=value), self.assertRaises(ValueError):
                validator(value)

    def test_accepts_opaque_version_and_ref_strings_without_structural_whitespace(self) -> None:
        self.assertEqual(validate_version_string("4.0.0-rc1+build.7"), "4.0.0-rc1+build.7")
        self.assertEqual(validate_ref_string("refs/tags/release-4.0.0"), "refs/tags/release-4.0.0")

    def test_rejects_version_string_with_whitespace_or_control_characters(self) -> None:
        for value in (" 4.0.0", "4.0.0 rc1", "4.0.0\n"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_version_string(value)

    def test_rejects_ref_string_absolute_or_empty_segments(self) -> None:
        for value in ("/refs/heads/main", "refs//heads/main", "refs/heads/main/"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_ref_string(value)

    def test_rejects_ref_string_traversal_tokens(self) -> None:
        for value in (".", ".."):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_ref_string(value)


if __name__ == "__main__":
    unittest.main()
