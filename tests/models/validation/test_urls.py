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

"""Tests for reusable URL validators."""

from __future__ import annotations

import unittest

from apache_buildish_site_pipeline.models.validation.urls import (
    validate_hostname_string,
    validate_provider_base_url,
    validate_url_string,
)


class UrlValidationTests(unittest.TestCase):
    """Exercise the shared URL validators used by schema scalars."""

    def test_accepts_absolute_http_and_https_urls(self) -> None:
        self.assertEqual(validate_url_string("https://example.org/docs"), "https://example.org/docs")
        self.assertEqual(validate_url_string("http://example.org/docs"), "http://example.org/docs")

    def test_rejects_disallowed_or_relative_urls(self) -> None:
        for value in ("javascript:alert(1)", "data:text/plain,hi", "/docs/latest", "https://user:pass@example.org"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                    validate_url_string(value)

    def test_rejects_non_public_or_raw_api_provider_base_urls(self) -> None:
        for value in (
            "https://localhost/project",
            "https://127.0.0.1/project",
            "https://api.github.com/repos/apache/spark",
            "https://example.org/project?view=api",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                    validate_provider_base_url(value)

    def test_accepts_bare_hostnames_and_rejects_url_fragments(self) -> None:
        self.assertEqual(validate_hostname_string("docs.example.org"), "docs.example.org")
        self.assertEqual(validate_hostname_string("203.0.113.10"), "203.0.113.10")

        for value in ("https://docs.example.org", "docs.example.org/path", "bad host"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                    validate_hostname_string(value)