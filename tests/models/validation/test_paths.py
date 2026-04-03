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

"""Tests for reusable path validators."""

from __future__ import annotations

import unittest

from apache_buildish_site_pipeline.models.validation.paths import (
    validate_public_path,
    validate_repo_relative_path,
    validate_stage_relative_path,
)


class PathValidationTests(unittest.TestCase):
    """Exercise the shared path validators used by schema scalars."""

    def test_accepts_normalized_repo_and_stage_relative_paths(self) -> None:
        self.assertEqual(validate_repo_relative_path("docs/site"), "docs/site")
        self.assertEqual(validate_stage_relative_path("data/routes.json"), "data/routes.json")

    def test_rejects_absolute_or_traversing_relative_paths(self) -> None:
        for value in ("/docs/site", "./docs/site", "docs/../site", "docs//site"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_repo_relative_path(value)

        with self.assertRaises(ValueError):
            validate_stage_relative_path("../data/routes.json")

    def test_accepts_normalized_public_paths_and_rejects_queries_or_relative_forms(self) -> None:
        self.assertEqual(validate_public_path("/docs/latest/"), "/docs/latest/")
        self.assertEqual(validate_public_path("/"), "/")

        for value in ("docs/latest/", "/docs/../latest/", "/docs/latest/?a=1"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_public_path(value)