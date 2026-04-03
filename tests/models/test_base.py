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

"""Tests for the shared external-model base class."""

from __future__ import annotations

import unittest

from pydantic import ValidationError

from apache_buildish_site_pipeline.models.base import SitePipelineBaseModel


class ExampleModel(SitePipelineBaseModel):
    """Example model used to prove shared base configuration."""

    schema_version: int
    display_name: str


class SitePipelineBaseModelTests(unittest.TestCase):
    """Validate the shared base-model configuration."""

    def test_allows_wire_format_field_names(self) -> None:
        model = ExampleModel.model_validate({"schemaVersion": 1, "displayName": "Docs"})
        self.assertEqual(model.schema_version, 1)
        self.assertEqual(model.display_name, "Docs")

    def test_allows_python_field_names_for_internal_construction(self) -> None:
        model = ExampleModel(schema_version=1, display_name="Docs")
        self.assertEqual(model.schema_version, 1)
        self.assertEqual(model.display_name, "Docs")

    def test_rejects_python_field_names_when_alias_only_validation_is_requested(self) -> None:
        with self.assertRaises(ValidationError):
            ExampleModel.model_validate(
                {"schema_version": 1, "display_name": "Docs"},
                by_alias=True,
                by_name=False,
            )

    def test_rejects_unknown_fields(self) -> None:
        with self.assertRaises(ValidationError):
            ExampleModel.model_validate(
                {"schemaVersion": 1, "displayName": "Docs", "unexpectedField": True}
            )

    def test_is_immutable_after_construction(self) -> None:
        model = ExampleModel.model_validate({"schemaVersion": 1, "displayName": "Docs"})

        with self.assertRaises(ValidationError):
            model.display_name = "Other Docs"  # type: ignore[misc]

    def test_serializes_with_camel_case_aliases(self) -> None:
        model = ExampleModel.model_validate({"schemaVersion": 1, "displayName": "Docs"})

        self.assertEqual(model.model_dump(), {"schemaVersion": 1, "displayName": "Docs"})
        self.assertEqual(model.model_dump_json(), '{"schemaVersion":1,"displayName":"Docs"}')