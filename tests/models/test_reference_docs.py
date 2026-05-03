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

"""Tests for bounded rich-text reference-doc metadata."""

from __future__ import annotations

import unittest

from apache_buildish_site_pipeline.docs.reference_docs import (
    ExternalLinkTarget,
    ReferenceCodeBlock,
    ReferenceDocError,
    ReferenceDocumentation,
    ReferenceList,
    ReferenceMarkdown,
    ReferenceParagraph,
    ReferenceSection,
    TypeReferenceTarget,
    parse_reference_document,
    parse_reference_link_target,
    render_reference_markdown,
    render_reference_schema_text,
)


class ReferenceDocsTests(unittest.TestCase):
    """Verify the constrained Markdown-like subset and typed metadata wrappers."""

    def test_parse_and_render_supported_subset(self) -> None:
        document = parse_reference_document(
            "See [components](type:SiteCatalogDocumentV1#components) and [site](https://buildish.apache.org/).\n\n"
            "- one\n- two\n\n"
            "```yaml\ncomponents: []\n```"
        )

        self.assertIsInstance(document.blocks[0], ReferenceParagraph)
        self.assertIsInstance(document.blocks[1], ReferenceList)
        self.assertIsInstance(document.blocks[2], ReferenceCodeBlock)
        self.assertEqual(
            render_reference_markdown(
                document,
                resolve_type_target=lambda target: f"#{target.type_name.lower()}-{target.field_name}",
            ),
            "See [components](#sitecatalogdocumentv1-components) and [site](https://buildish.apache.org/).\n\n"
            "- one\n- two\n\n"
            "```yaml\ncomponents: []\n```",
        )
        self.assertEqual(
            render_reference_schema_text(document),
            "See components (SiteCatalogDocumentV1.components) and site (https://buildish.apache.org/).\n\n"
            "- one\n- two\n\n"
            "[yaml code]\ncomponents: []",
        )

    def test_parse_link_target_supports_symbolic_and_https_targets(self) -> None:
        self.assertEqual(
            parse_reference_link_target("type:SiteCatalogDocumentV1#components"),
            TypeReferenceTarget(type_name="SiteCatalogDocumentV1", field_name="components"),
        )
        self.assertEqual(
            parse_reference_link_target("https://buildish.apache.org/"),
            ExternalLinkTarget(url="https://buildish.apache.org/"),
        )

    def test_rejects_unsafe_or_unsupported_links(self) -> None:
        with self.assertRaisesRegex(ReferenceDocError, "Unsupported or unsafe link target"):
            parse_reference_link_target("javascript:alert(1)")

    def test_rejects_unsupported_markdown_constructs(self) -> None:
        with self.assertRaisesRegex(ReferenceDocError, "Unsupported block token"):
            parse_reference_document("# heading")
        with self.assertRaisesRegex(ReferenceDocError, "Unsupported inline token"):
            parse_reference_document("![alt](https://buildish.apache.org/logo.png)")
        with self.assertRaisesRegex(ReferenceDocError, "must declare a language tag"):
            parse_reference_document("```\nplain\n```")

    def test_reference_metadata_validates_content_at_construction_time(self) -> None:
        metadata = ReferenceDocumentation(
            summary=ReferenceMarkdown("Summary with [link](type:SiteCatalogDocumentV1)."),
            sections=(
                ReferenceSection(
                    title="Notes",
                    body=ReferenceMarkdown("Use `components` for participating components."),
                ),
            ),
        )

        self.assertEqual(metadata.summary.document.blocks[0].children[0].value, "Summary with ")
        with self.assertRaisesRegex(ValueError, "must not be blank"):
            ReferenceSection(title="   ", body=ReferenceMarkdown("Body"))
        with self.assertRaisesRegex(ReferenceDocError, "must not be blank"):
            ReferenceMarkdown("   ")


if __name__ == "__main__":
    unittest.main()
