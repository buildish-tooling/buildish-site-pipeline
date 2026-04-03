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

"""Validation helpers for regex-bearing wire fields."""

from __future__ import annotations

import re


def validate_regex_string(value: str) -> str:
    """Validate a stored regex pattern string by compiling it."""
    if any(character in value for character in ("\x00", "\n", "\r")):
        raise ValueError("RegexString must not contain NUL or newline characters")
    try:
        re.compile(value)
    except re.error as exc:
        raise ValueError("RegexString must be a valid regular expression") from exc
    return value