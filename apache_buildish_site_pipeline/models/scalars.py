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

"""Reusable scalar aliases for external schema models."""
from typing import Annotated

from pydantic import AwareDatetime, AfterValidator, Field, StringConstraints

from .validation.extensions import validate_extensions_object
from .validation.paths import validate_local_path_string, validate_stage_relative_path

NonEmptyString = Annotated[str, StringConstraints(min_length=1)]
NonNegativeInteger = Annotated[int, Field(strict=True, ge=0)]
PositiveInteger = Annotated[int, Field(strict=True, gt=0)]

SchemaVersion = Annotated[int, Field(strict=True, ge=1)]
TimestampString = AwareDatetime
LocalPathString = Annotated[
    str,
    StringConstraints(min_length=1),
    AfterValidator(validate_local_path_string),
]
StageRelativePath = Annotated[
    str,
    StringConstraints(min_length=1),
    AfterValidator(validate_stage_relative_path),
]
ExtensionsObject = Annotated[
    dict[str, object],
    AfterValidator(validate_extensions_object),
]
