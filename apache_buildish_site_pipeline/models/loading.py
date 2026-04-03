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

"""Safe document-loading helpers for external YAML and JSON schema documents."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import cast

import yaml
from pydantic import ValidationError

from .base import SitePipelineBaseModel
from .enums import DocumentFormat


class LoadingError(Exception):
    """Base class for document-loading failures."""

    def __init__(self, message: str, *, source_name: str | None = None) -> None:
        super().__init__(message)
        self.source_name = source_name


class DocumentDecodingError(LoadingError):
    """Raised when bytes input cannot be decoded as UTF-8."""


class DocumentSyntaxError(LoadingError):
    """Raised when YAML or JSON syntax is invalid."""


class DuplicateKeyError(DocumentSyntaxError):
    """Raised when a mapping/object repeats the same key."""


class DocumentRootTypeError(LoadingError):
    """Raised when the document root is not the required container type."""


class MissingSchemaVersionError(LoadingError):
    """Raised when a versioned root document omits ``schemaVersion``."""


class UnsupportedSchemaVersionError(LoadingError):
    """Raised when a versioned root document uses an unsupported schema version."""


class DocumentValidationFailure(LoadingError):
    """Raised when Pydantic rejects a syntactically valid document."""

    def __init__(
        self,
        message: str,
        *,
        source_name: str | None = None,
        validation_error: ValidationError,
    ) -> None:
        super().__init__(message, source_name=source_name)
        self.validation_error = validation_error


class _UniqueKeySafeLoader(yaml.SafeLoader):
    """YAML safe loader that rejects duplicate mapping keys."""


def _construct_unique_mapping(
    loader: _UniqueKeySafeLoader,
    node: yaml.nodes.MappingNode,
    deep: bool = False,
) -> dict[object, object]:
    loader.flatten_mapping(node)
    mapping: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            line_number = key_node.start_mark.line + 1
            raise DuplicateKeyError(
                f"Duplicate YAML key {key!r} at line {line_number}",
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def _decode_document_text(document: str | bytes, *, source_name: str) -> str:
    if isinstance(document, str):
        return document
    try:
        return document.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DocumentDecodingError(
            f"Could not decode {source_name} as UTF-8",
            source_name=source_name,
        ) from exc


def _reject_duplicate_json_object(pairs: list[tuple[object, object]]) -> dict[object, object]:
    mapping: dict[object, object] = {}
    for key, value in pairs:
        if key in mapping:
            raise DuplicateKeyError(f"Duplicate JSON key {key!r}")
        mapping[key] = value
    return mapping


def _require_mapping_root(raw_document: object, *, source_name: str) -> Mapping[str, object]:
    if not isinstance(raw_document, dict):
        raise DocumentRootTypeError(
            "Expected document root to be a mapping/object",
            source_name=source_name,
        )
    return cast(Mapping[str, object], raw_document)


def load_yaml_mapping(document: str | bytes, *, source_name: str = "<memory>") -> Mapping[str, object]:
    """Decode and parse one YAML document with duplicate-key rejection."""
    document_text = _decode_document_text(document, source_name=source_name)
    try:
        # This custom loader subclasses yaml.SafeLoader and only adds duplicate-key
        # rejection; it does not enable arbitrary object construction.
        raw_document = yaml.load(document_text, Loader=_UniqueKeySafeLoader)  # noqa: S506
    except DuplicateKeyError as exc:
        if exc.source_name is None:
            exc.source_name = source_name
        raise
    except yaml.YAMLError as exc:
        raise DocumentSyntaxError(
            f"Invalid YAML syntax in {source_name}",
            source_name=source_name,
        ) from exc
    return _require_mapping_root(raw_document, source_name=source_name)


def load_json_mapping(document: str | bytes, *, source_name: str = "<memory>") -> Mapping[str, object]:
    """Decode and parse one JSON document with duplicate-key rejection."""
    document_text = _decode_document_text(document, source_name=source_name)
    try:
        raw_document = json.loads(document_text, object_pairs_hook=_reject_duplicate_json_object)
    except DuplicateKeyError as exc:
        if exc.source_name is None:
            exc.source_name = source_name
        raise
    except json.JSONDecodeError as exc:
        raise DocumentSyntaxError(
            f"Invalid JSON syntax in {source_name}",
            source_name=source_name,
        ) from exc
    return _require_mapping_root(raw_document, source_name=source_name)


def load_versioned_document[DocumentModelT: SitePipelineBaseModel](
    document: str | bytes,
    *,
    document_format: DocumentFormat,
    schema_version_models: Mapping[int, type[DocumentModelT]],
    source_name: str = "<memory>",
) -> DocumentModelT:
    """Load one versioned mapping document into the matching Pydantic model."""
    if document_format is DocumentFormat.YAML:
        raw_document = load_yaml_mapping(document, source_name=source_name)
    else:
        raw_document = load_json_mapping(document, source_name=source_name)

    raw_schema_version = raw_document.get("schemaVersion")
    if raw_schema_version is None:
        raise MissingSchemaVersionError(
            f"Missing required schemaVersion in {source_name}",
            source_name=source_name,
        )
    if isinstance(raw_schema_version, bool) or not isinstance(raw_schema_version, int):
        raise UnsupportedSchemaVersionError(
            f"Unsupported schemaVersion {raw_schema_version!r} in {source_name}",
            source_name=source_name,
        )

    model_type = schema_version_models.get(raw_schema_version)
    if model_type is None:
        raise UnsupportedSchemaVersionError(
            f"Unsupported schemaVersion {raw_schema_version} in {source_name}",
            source_name=source_name,
        )
    try:
        return model_type.model_validate(raw_document)
    except ValidationError as exc:
        raise DocumentValidationFailure(
            f"Document validation failed for {source_name}",
            source_name=source_name,
            validation_error=exc,
        ) from exc