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

"""Contract coverage for shared authored-page parsing."""

from __future__ import annotations

import unittest

from buildish_site_pipeline.authored_page import (
    AuthoredPageParseError,
    parse_authored_page,
)


class AuthoredPageTests(unittest.TestCase):
    def test_parse_authored_page_accepts_lf_and_crlf_front_matter(self) -> None:
        for newline in ("\n", "\r\n"):
            with self.subTest(newline=repr(newline)):
                parsed = parse_authored_page(
                    newline.join(("---", "title: Guide", "---", "Body", ""))
                )

                self.assertEqual(parsed.metadata, {"title": "Guide"})
                self.assertEqual(parsed.content, f"Body{newline}")
                self.assertEqual(parsed.source_line_offset, 3)

    def test_parse_authored_page_accepts_empty_and_document_end_blocks(self) -> None:
        empty = parse_authored_page("---\n\n---\nBody\n")
        document_end = parse_authored_page("---\ntitle: Guide\n...\nBody\n")

        self.assertEqual(empty.metadata, {})
        self.assertEqual(empty.content, "Body\n")
        self.assertEqual(document_end.metadata, {"title": "Guide"})
        self.assertEqual(document_end.content, "Body\n")

    def test_parse_authored_page_reports_malformed_body_location(self) -> None:
        with self.assertRaises(AuthoredPageParseError) as raised:
            parse_authored_page("---\ntitle: [\n---\n[Guide](guide/)\n")

        self.assertEqual(raised.exception.content, "[Guide](guide/)\n")
        self.assertEqual(raised.exception.source_line_offset, 3)

    def test_parse_authored_page_rejects_unterminated_block(self) -> None:
        with self.assertRaises(AuthoredPageParseError) as raised:
            parse_authored_page("---\ntitle: Guide\n")

        self.assertIsNone(raised.exception.content)
        self.assertEqual(raised.exception.source_line_offset, 0)


if __name__ == "__main__":
    unittest.main()
