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

"""Typed external models for the site pipeline."""

from .base import SitePipelineBaseModel
from .enums import DocumentFormat
from .loading import (
    DocumentDecodingError,
    DocumentRootTypeError,
    DocumentSyntaxError,
    DocumentValidationFailure,
    DuplicateKeyError,
    LoadingError,
    MissingSchemaVersionError,
    UnsupportedSchemaVersionError,
    load_json_mapping,
    load_versioned_document,
    load_yaml_mapping,
)
from .scalars import SchemaVersion

__all__ = [
    "DocumentDecodingError",
    "DocumentFormat",
    "DocumentRootTypeError",
    "DocumentSyntaxError",
    "DocumentValidationFailure",
    "DuplicateKeyError",
    "LoadingError",
    "MissingSchemaVersionError",
    "SchemaVersion",
    "SitePipelineBaseModel",
    "UnsupportedSchemaVersionError",
    "load_json_mapping",
    "load_versioned_document",
    "load_yaml_mapping",
]