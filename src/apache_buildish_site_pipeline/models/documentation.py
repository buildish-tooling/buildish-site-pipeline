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

"""Documentation metadata for public contract models.

The category and ownership axes live on the public model types themselves so
schema export and future reference-generation code can group contracts without
maintaining a parallel registry keyed by model class.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Literal

from apache_buildish_site_pipeline.models.base import SitePipelineBaseModel
from apache_buildish_site_pipeline.models.reference_docs import ReferenceDocumentation

ContractCategory = Literal["authored", "provider", "emitted"]
ContractOwnership = Literal[
    "consumer-owned", "component-owned", "provider-derived", "pipeline-derived"
]


@dataclass(frozen=True)
class ContractDocumentation:
    """Structured grouping hints for one public contract model or export."""

    category: ContractCategory
    ownership: ContractOwnership
    summary: str | None = None
    file_path: str | None = None
    reference: ReferenceDocumentation | None = None

    def as_schema_extension(self) -> dict[str, str]:
        """Return the stable vendor extension used in exported JSON Schema files."""

        extension: dict[str, str] = {
            "category": self.category,
            "ownership": self.ownership,
        }
        if self.summary is not None:
            extension["summary"] = self.summary
        if self.file_path is not None:
            extension["filePath"] = self.file_path
        return extension


class DocumentedContractModel(SitePipelineBaseModel):
    """Base class for public wire models that expose contract metadata."""

    contract_documentation: ClassVar[ContractDocumentation | None] = None


class ConsumerOwnedAuthoredModel(DocumentedContractModel):
    """Base class for consumer-authored wire models."""

    contract_documentation: ClassVar[ContractDocumentation] = ContractDocumentation(
        category="authored",
        ownership="consumer-owned",
    )


class ComponentOwnedAuthoredModel(DocumentedContractModel):
    """Base class for component-authored wire models."""

    contract_documentation: ClassVar[ContractDocumentation] = ContractDocumentation(
        category="authored",
        ownership="component-owned",
    )


class ProviderDerivedModel(DocumentedContractModel):
    """Base class for provider-derived wire models."""

    contract_documentation: ClassVar[ContractDocumentation] = ContractDocumentation(
        category="provider",
        ownership="provider-derived",
    )


class PipelineDerivedModel(DocumentedContractModel):
    """Base class for pipeline-emitted wire models."""

    contract_documentation: ClassVar[ContractDocumentation] = ContractDocumentation(
        category="emitted",
        ownership="pipeline-derived",
    )


def contract_documentation_for(
    model: type[SitePipelineBaseModel],
) -> ContractDocumentation | None:
    """Return documentation metadata for one public contract model if available."""

    documentation = getattr(model, "contract_documentation", None)
    return documentation if isinstance(documentation, ContractDocumentation) else None
