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

"""License-policy validation for preliminary release-legal inventory."""

from __future__ import annotations

import re

from .release_models import DistributionInventoryEntry

_SPDX_TOKEN_PATTERN = re.compile(r"\(|\)|[A-Za-z0-9.+-]+")
_SPDX_OPERATORS = {"AND", "OR", "WITH"}
_CATEGORY_X_SPDX_IDS = {
    "AGPL-3.0",
    "AGPL-3.0-ONLY",
    "AGPL-3.0-OR-LATER",
    "APSL-2.0",
    "BSD-2-CLAUSE-PATENT",
    "BSD-4-CLAUSE",
    "BUSL-1.1",
    "CPOL-1.02",
    "GPL-1.0",
    "GPL-1.0-ONLY",
    "GPL-1.0-OR-LATER",
    "GPL-2.0",
    "GPL-2.0-ONLY",
    "GPL-2.0-OR-LATER",
    "GPL-3.0",
    "GPL-3.0-ONLY",
    "GPL-3.0-OR-LATER",
    "JSON",
    "LGPL-2.0",
    "LGPL-2.0-ONLY",
    "LGPL-2.0-OR-LATER",
    "LGPL-2.1",
    "LGPL-2.1-ONLY",
    "LGPL-2.1-OR-LATER",
    "LGPL-3.0",
    "LGPL-3.0-ONLY",
    "LGPL-3.0-OR-LATER",
    "MS-LPL",
    "NPL-1.0",
    "NPL-1.1",
    "QPL-1.0",
    "SLEEPYCAT",
    "SSPL-1.0",
}
_CATEGORY_X_STRING_MARKERS = (
    "AFFERO GPL",
    "AGPL",
    "APPLE PUBLIC SOURCE LICENSE",
    "APSL-2.0",
    "BSD-4-CLAUSE",
    "BSD 4-CLAUSE",
    "BUSINESS SOURCE LICENSE",
    "BUSL-1.1",
    "COMMONS CLAUSE",
    "CPOL",
    "GNU AFFERO GENERAL PUBLIC LICENSE",
    "GNU GENERAL PUBLIC LICENSE",
    "GNU GPL",
    "JSON LICENSE",
    "LESSER GENERAL PUBLIC LICENSE",
    "LGPL",
    "MICROSOFT LIMITED PUBLIC LICENSE",
    "MS-LPL",
    "NETSCAPE PUBLIC LICENSE",
    "NPL 1.0",
    "NPL 1.1",
    "Q PUBLIC LICENSE",
    "QPL",
    "SERVER SIDE PUBLIC LICENSE",
    "SLEEPYCAT",
    "SSPL",
)
_CLASSPATH_EXCEPTION_SPDX_ID = "CLASSPATH-EXCEPTION-2.0"
_GPL_2_ONLY_SPDX_IDS = {"GPL-2.0", "GPL-2.0-ONLY"}


def raise_for_category_x_licenses(
    entries: tuple[DistributionInventoryEntry, ...],
) -> None:
    """Reject inventory whose declared metadata resolves to Category X."""

    violations: list[str] = []
    for entry in entries:
        violation_reason = category_x_violation_reason(entry)
        if violation_reason is not None:
            violations.append(f"{entry.name} {entry.version}: {violation_reason}")
    if violations:
        violation_list = "\n - ".join(("", *violations))
        raise RuntimeError(
            "Refusing to generate release-legal artifacts because Apache Category X "
            f"license metadata was detected:{violation_list}"
        )


def category_x_violation_reason(entry: DistributionInventoryEntry) -> str | None:
    """Return the policy violation in one inventory entry, if any."""

    if entry.license_expression is not None and spdx_expression_is_category_x(
        entry.license_expression
    ):
        return (
            "SPDX license expression "
            f"{entry.license_expression!r} resolves to an Apache Category X license"
        )
    for metadata_value in (entry.license_field, *entry.license_classifiers):
        if metadata_value is None:
            continue
        marker = _category_x_string_marker(metadata_value)
        if marker is not None:
            return (
                f"declared license metadata {metadata_value!r} matched prohibited "
                f"marker {marker!r}"
            )
    return None


def spdx_expression_is_category_x(expression: str) -> bool:
    """Evaluate Category X policy across a small SPDX AND/OR/WITH expression."""

    tokens = _SPDX_TOKEN_PATTERN.findall(expression)
    if not tokens:
        return False
    parsed_value, next_index = _parse_spdx_or_expression(tokens, 0)
    if next_index != len(tokens):
        return any(
            _spdx_identifier_is_category_x(token)
            for token in tokens
            if token.upper() not in _SPDX_OPERATORS and token not in {"(", ")"}
        )
    return parsed_value


def _parse_spdx_or_expression(tokens: list[str], start_index: int) -> tuple[bool, int]:
    value, index = _parse_spdx_and_expression(tokens, start_index)
    while index < len(tokens) and tokens[index].upper() == "OR":
        next_value, next_index = _parse_spdx_and_expression(tokens, index + 1)
        value = value and next_value
        index = next_index
    return value, index


def _parse_spdx_and_expression(tokens: list[str], start_index: int) -> tuple[bool, int]:
    value, index = _parse_spdx_factor(tokens, start_index)
    while index < len(tokens) and tokens[index].upper() == "AND":
        next_value, next_index = _parse_spdx_factor(tokens, index + 1)
        value = value or next_value
        index = next_index
    return value, index


def _parse_spdx_factor(tokens: list[str], start_index: int) -> tuple[bool, int]:
    if start_index >= len(tokens):
        raise ValueError("Unexpected end of SPDX expression")
    current_symbol = tokens[start_index]
    if current_symbol == "(":
        value, index = _parse_spdx_or_expression(tokens, start_index + 1)
        if index >= len(tokens) or tokens[index] != ")":
            raise ValueError("Unbalanced SPDX parentheses")
        return value, index + 1
    if current_symbol in {"AND", "OR", "WITH", ")"}:
        raise ValueError(f"Unexpected SPDX token {current_symbol!r}")

    license_id = _normalize_spdx_identifier(current_symbol)
    next_index = start_index + 1
    if next_index + 1 < len(tokens) and tokens[next_index].upper() == "WITH":
        exception_id = _normalize_spdx_identifier(tokens[next_index + 1])
        return (
            _spdx_with_expression_is_category_x(license_id, exception_id),
            next_index + 2,
        )
    return _spdx_identifier_is_category_x(license_id), next_index


def _spdx_with_expression_is_category_x(license_id: str, exception_id: str) -> bool:
    if (
        license_id in _GPL_2_ONLY_SPDX_IDS
        and exception_id == _CLASSPATH_EXCEPTION_SPDX_ID
    ):
        return False
    return _spdx_identifier_is_category_x(license_id)


def _spdx_identifier_is_category_x(identifier: str) -> bool:
    return _normalize_spdx_identifier(identifier) in _CATEGORY_X_SPDX_IDS


def _normalize_spdx_identifier(identifier: str) -> str:
    return identifier.strip().upper()


def _category_x_string_marker(metadata_value: str) -> str | None:
    upper_value = metadata_value.upper()
    return next(
        (marker for marker in _CATEGORY_X_STRING_MARKERS if marker in upper_value),
        None,
    )
