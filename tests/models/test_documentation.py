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

"""Tests for type-attached contract documentation metadata."""

from __future__ import annotations

import unittest
from typing import cast

from apache_buildish_site_pipeline.models import ContractDocumentation, contract_documentation_for
from apache_buildish_site_pipeline.models.authored.component_metadata import ComponentIdentity
from apache_buildish_site_pipeline.models.authored.page_metadata import PageTranslationMetadata
from apache_buildish_site_pipeline.models.authored.site_catalog import ComponentCatalogEntry, SiteCatalogDocumentV1
from apache_buildish_site_pipeline.models.emitted.aggregates import RouteAggregateEntry
from apache_buildish_site_pipeline.models.emitted.planning_stage_contract import StageManifestV1
from apache_buildish_site_pipeline.models.emitted.staged_front_matter import PipelineFrontMatterNamespace
from apache_buildish_site_pipeline.models.provider.provider_snapshot import ProviderRecord
from apache_buildish_site_pipeline.staging.incremental_metadata import PersistedUnitContributionsV1


class ContractDocumentationTests(unittest.TestCase):
    """Verify every public contract family exposes category and ownership axes."""

    @staticmethod
    def _documentation_for(model: type[object]) -> ContractDocumentation:
        documentation = contract_documentation_for(cast(type, model))
        if documentation is None:
            raise AssertionError(f"missing contract documentation for {model!r}")
        return documentation

    def test_inherited_axes_cover_authored_provider_and_emitted_types(self) -> None:
        self.assertEqual(self._documentation_for(ComponentCatalogEntry).category, "authored")
        self.assertEqual(self._documentation_for(ComponentCatalogEntry).ownership, "consumer-owned")
        self.assertEqual(self._documentation_for(ComponentIdentity).ownership, "component-owned")
        self.assertEqual(self._documentation_for(PageTranslationMetadata).ownership, "component-owned")
        self.assertEqual(self._documentation_for(ProviderRecord).category, "provider")
        self.assertEqual(self._documentation_for(RouteAggregateEntry).category, "emitted")

    def test_file_path_hints_only_exist_for_whole_file_contracts(self) -> None:
        self.assertEqual(self._documentation_for(SiteCatalogDocumentV1).file_path, "site/catalog.yaml")
        self.assertEqual(self._documentation_for(StageManifestV1).file_path, "manifest.json")
        self.assertEqual(
            self._documentation_for(PersistedUnitContributionsV1).file_path,
            "data/_pipeline/unit-contributions.json",
        )
        self.assertIsNone(self._documentation_for(PipelineFrontMatterNamespace).file_path)
        self.assertIsNone(self._documentation_for(ComponentCatalogEntry).file_path)

    def test_reference_metadata_can_live_next_to_schema_grouping_hints(self) -> None:
        documentation = self._documentation_for(SiteCatalogDocumentV1)

        self.assertIsNotNone(documentation.reference)
        reference = documentation.reference
        if reference is None:
            raise AssertionError("expected generated reference metadata for SiteCatalogDocumentV1")
        self.assertIn("Consumer-owned catalog input", reference.summary.source)
        self.assertEqual(reference.sections[0].title, "Inheritance")


if __name__ == "__main__":
    unittest.main()