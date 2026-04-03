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

"""Tests for the component repository document models and loader."""

from __future__ import annotations

import unittest

from apache_buildish_site_pipeline.models.component_repository import ComponentRepositoryDocumentV1
from apache_buildish_site_pipeline.models.enums import DocumentFormat
from apache_buildish_site_pipeline.models.loading import (
    DocumentValidationFailure,
    MissingSchemaVersionError,
    load_component_repository_document,
)


class ComponentRepositoryDocumentTests(unittest.TestCase):
    """Validate the authored component repository document contract."""

    def test_loads_valid_component_repository_document(self) -> None:
        document = load_component_repository_document(
            "schemaVersion: 1\ncomponent:\n  slug: spark\n  displayName: Apache Spark\ncontent:\n  pagesRoot: site/pages\n  docsRoot: docs\nlifecycle:\n  latestStable: 4.0.0\n  supportStatusVocabulary:\n    active:\n      displayName: Active\n      order: 10\n",
            document_format=DocumentFormat.YAML,
            source_name="site/component.yaml",
        )

        self.assertIsInstance(document, ComponentRepositoryDocumentV1)
        self.assertEqual(document.component.slug, "spark")
        self.assertEqual(document.content.pages_root, "site/pages")
        self.assertIn("active", document.lifecycle.support_status_vocabulary)

    def test_rejects_invalid_content_root_paths(self) -> None:
        with self.assertRaises(DocumentValidationFailure):
            load_component_repository_document(
                "schemaVersion: 1\ncomponent:\n  slug: spark\ncontent:\n  pagesRoot: ../site/pages\n",
                document_format=DocumentFormat.YAML,
                source_name="site/component.yaml",
            )

    def test_rejects_invalid_identifier_keys_and_python_field_names_from_external_input(self) -> None:
        with self.assertRaises(DocumentValidationFailure):
            load_component_repository_document(
                '{"schemaVersion":1,"component":{"slug":"spark"},"lifecycle":{"supportStatusVocabulary":{"GA Status":{"displayName":"GA"}}}}',
                document_format=DocumentFormat.JSON,
                source_name="site/component.json",
            )

        with self.assertRaises(MissingSchemaVersionError):
            load_component_repository_document(
                '{"schema_version":1,"component":{"slug":"spark"}}',
                document_format=DocumentFormat.JSON,
                source_name="site/component.json",
            )