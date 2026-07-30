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

"""Tests for safe external YAML and JSON loading helpers."""

from __future__ import annotations

import unittest
from typing import Literal

from buildish_site_pipeline.models.base import SitePipelineBaseModel
from buildish_site_pipeline.models.enums import DocumentFormat
from buildish_site_pipeline.models.loading import (
    DocumentDecodingError,
    DocumentRootTypeError,
    DocumentSyntaxError,
    DocumentValidationFailure,
    DuplicateKeyError,
    MissingSchemaVersionError,
    UnsupportedSchemaVersionError,
    load_json_mapping,
    load_versioned_document,
    load_yaml_mapping,
)


class ExampleDocumentV1(SitePipelineBaseModel):
    """Example schema-versioned document model for loader tests."""

    schema_version: Literal[1]
    name: str


class ExampleDocumentV2(SitePipelineBaseModel):
    """Second model used to prove version dispatch."""

    schema_version: Literal[2]
    title: str


class LoadingTests(unittest.TestCase):
    """Exercise safe parsing, dispatch, and failure behavior."""

    def test_loads_yaml_mapping_and_rejects_duplicate_keys(self) -> None:
        mapping = load_yaml_mapping("schemaVersion: 1\nname: Docs\n", source_name="component.yaml")
        self.assertEqual(mapping["schemaVersion"], 1)
        self.assertEqual(mapping["name"], "Docs")

        with self.assertRaises(DuplicateKeyError):
            load_yaml_mapping("schemaVersion: 1\nname: one\nname: two\n", source_name="component.yaml")

    def test_loads_json_mapping_and_rejects_duplicate_nested_keys(self) -> None:
        mapping = load_json_mapping('{"schemaVersion":1,"payload":{"name":"Docs"}}', source_name="report.json")
        self.assertEqual(mapping["schemaVersion"], 1)

        with self.assertRaises(DuplicateKeyError):
            load_json_mapping(
                '{"schemaVersion":1,"payload":{"name":"Docs","name":"Shadowed"}}',
                source_name="report.json",
            )

    def test_rejects_malformed_utf8(self) -> None:
        with self.assertRaises(DocumentDecodingError):
            load_yaml_mapping(b"\xff\xfe", source_name="component.yaml")

    def test_rejects_malformed_yaml_and_json_syntax(self) -> None:
        with self.assertRaises(DocumentSyntaxError):
            load_yaml_mapping("schemaVersion: [1\n", source_name="component.yaml")

        with self.assertRaises(DocumentSyntaxError):
            load_json_mapping('{"schemaVersion": 1,', source_name="report.json")

    def test_rejects_wrong_root_container_type(self) -> None:
        with self.assertRaises(DocumentRootTypeError):
            load_json_mapping("[]", source_name="report.json")

    def test_dispatches_to_the_requested_schema_version_model(self) -> None:
        model = load_versioned_document(
            "schemaVersion: 1\nname: Docs\n",
            document_format=DocumentFormat.YAML,
            schema_version_models={1: ExampleDocumentV1, 2: ExampleDocumentV2},
            source_name="component.yaml",
        )
        self.assertIsInstance(model, ExampleDocumentV1)
        self.assertEqual(model.name, "Docs")

    def test_rejects_missing_or_unsupported_schema_versions(self) -> None:
        with self.assertRaises(MissingSchemaVersionError):
            load_versioned_document(
                "name: Docs\n",
                document_format=DocumentFormat.YAML,
                schema_version_models={1: ExampleDocumentV1},
                source_name="component.yaml",
            )

        with self.assertRaises(UnsupportedSchemaVersionError):
            load_versioned_document(
                "schemaVersion: 99\nname: Docs\n",
                document_format=DocumentFormat.YAML,
                schema_version_models={1: ExampleDocumentV1},
                source_name="component.yaml",
            )

        with self.assertRaises(UnsupportedSchemaVersionError):
            load_versioned_document(
                '{"schemaVersion":true,"name":"Docs"}',
                document_format=DocumentFormat.JSON,
                schema_version_models={1: ExampleDocumentV1},
                source_name="report.json",
            )

    def test_wraps_pydantic_validation_failures_without_returning_partial_objects(self) -> None:
        with self.assertRaises(DocumentValidationFailure) as context:
            load_versioned_document(
                "schemaVersion: 1\nunknownField: Docs\n",
                document_format=DocumentFormat.YAML,
                schema_version_models={1: ExampleDocumentV1},
                source_name="component.yaml",
            )

        error = context.exception.validation_error
        self.assertIn("name", str(error))
        self.assertIn("unknownField", str(error))