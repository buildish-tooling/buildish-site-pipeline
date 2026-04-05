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

from .validation.common import (
    validate_artifact_key,
    validate_identifier,
    validate_provider_key,
    validate_ref_string,
    validate_slug,
    validate_source_key,
    validate_version_string,
)
from .validation.extensions import validate_extensions_object
from .validation.paths import (
    validate_local_path_string,
    validate_mount_source_ref,
    validate_public_path,
    validate_repo_relative_path,
    validate_stage_relative_path,
)
from .validation.regex import validate_regex_string
from .validation.references import validate_reference_string
from .validation.urls import (
    validate_hostname_string,
    validate_provider_base_url,
    validate_url_string,
)

NonEmptyString = Annotated[str, StringConstraints(min_length=1)]
NonNegativeInteger = Annotated[int, Field(strict=True, ge=0)]
PositiveInteger = Annotated[int, Field(strict=True, gt=0)]

Identifier = Annotated[
    str, StringConstraints(min_length=1), AfterValidator(validate_identifier)
]
Slug = Annotated[str, StringConstraints(min_length=1), AfterValidator(validate_slug)]
ArtifactKey = Annotated[
    str, StringConstraints(min_length=1), AfterValidator(validate_artifact_key)
]
OriginKey = Identifier
SourceKey = Annotated[
    str, StringConstraints(min_length=1), AfterValidator(validate_source_key)
]
ProviderKey = Annotated[
    str, StringConstraints(min_length=1), AfterValidator(validate_provider_key)
]
VersionString = Annotated[
    str,
    StringConstraints(min_length=1),
    AfterValidator(validate_version_string),
]
RefString = Annotated[
    str, StringConstraints(min_length=1), AfterValidator(validate_ref_string)
]
RegexString = Annotated[
    str, StringConstraints(min_length=1), AfterValidator(validate_regex_string)
]
ReferenceString = Annotated[
    str,
    StringConstraints(min_length=1),
    AfterValidator(validate_reference_string),
]
SchemaVersion = Annotated[int, Field(strict=True, ge=1)]
TimestampString = AwareDatetime
LocalPathString = Annotated[
    str,
    StringConstraints(min_length=1),
    AfterValidator(validate_local_path_string),
]
RepoRelativePath = Annotated[
    str,
    StringConstraints(min_length=1),
    AfterValidator(validate_repo_relative_path),
]
StageRelativePath = Annotated[
    str,
    StringConstraints(min_length=1),
    AfterValidator(validate_stage_relative_path),
]
MountSourceRef = Annotated[
    str,
    StringConstraints(min_length=1),
    AfterValidator(validate_mount_source_ref),
]
PublicPath = Annotated[
    str,
    StringConstraints(min_length=1),
    AfterValidator(validate_public_path),
]
HostnameString = Annotated[
    str,
    StringConstraints(min_length=1),
    AfterValidator(validate_hostname_string),
]
UrlString = Annotated[
    str, StringConstraints(min_length=1), AfterValidator(validate_url_string)
]
ProviderBaseUrl = Annotated[
    str,
    StringConstraints(min_length=1),
    AfterValidator(validate_provider_base_url),
]
ExtensionsObject = Annotated[
    dict[str, object],
    AfterValidator(validate_extensions_object),
]
