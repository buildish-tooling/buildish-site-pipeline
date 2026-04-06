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

from __future__ import annotations

import unittest

from apache_buildish_site_pipeline.public_paths import (
    join_public_path,
    normalize_public_path,
)


class PublicPathHelpersTests(unittest.TestCase):
    def test_join_public_path_supports_directory_and_document_style_outputs(self) -> None:
        self.assertEqual(
            join_public_path("/docs/", "spark", trailing_slash=True),
            "/docs/spark/",
        )
        self.assertEqual(
            join_public_path("/docs/", "guide", trailing_slash=False),
            "/docs/guide",
        )

    def test_normalize_public_path_coalesces_slashes_and_applies_style(self) -> None:
        self.assertEqual(
            normalize_public_path("//docs//spark//", trailing_slash=True),
            "/docs/spark/",
        )
        self.assertEqual(
            normalize_public_path("docs/guide/", trailing_slash=False),
            "/docs/guide",
        )