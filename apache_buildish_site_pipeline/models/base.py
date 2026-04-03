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

"""Shared base model conventions for external schema types."""

from pydantic import BaseModel, ConfigDict


def to_camel_case(field_name: str) -> str:
    """Convert a snake_case Python field name to the wire-format camelCase name."""
    head, *tail = field_name.split("_")
    return head + "".join(part.capitalize() for part in tail)


class SitePipelineBaseModel(BaseModel):
    """Shared immutable base model for all wire-facing schema objects."""

    model_config = ConfigDict(
        alias_generator=to_camel_case,
        extra="forbid",
        frozen=True,
        populate_by_name=False,
        serialize_by_alias=True,
    )