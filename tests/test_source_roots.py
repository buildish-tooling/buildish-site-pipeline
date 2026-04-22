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

"""Tests for canonical component source-root resolution."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from apache_buildish_site_pipeline.models import SiteCatalogDocumentV1
from apache_buildish_site_pipeline.models.authored.site_catalog import (
    ComponentCatalogEntry,
)
from apache_buildish_site_pipeline.source_roots import (
    normalize_workspace_relative_locator,
    resolve_catalog_source_bindings,
    resolve_component_content_source_binding,
    resolve_component_source_roots,
    resolve_repo_path,
)


class SourceRootResolutionTests(unittest.TestCase):
    def test_resolve_catalog_source_bindings_applies_default_metadata_path(self) -> None:
        catalog = _catalog(
            {
                "defaults": {
                    "metadataFile": "site/component.yaml",
                    "publication": {"origin": "docs"},
                },
                "sources": {"runtime": {"localDir": "components/runtime"}},
                "components": [],
            }
        )

        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            bindings = resolve_catalog_source_bindings(
                catalog=catalog, workspace_root=workspace_root
            )

        binding = bindings["runtime"]
        self.assertEqual(binding.local_dir, workspace_root / "components/runtime")
        self.assertEqual(binding.export_locator, Path("components/runtime"))
        self.assertEqual(
            binding.metadata_file,
            workspace_root / "components/runtime/site/component.yaml",
        )

    def test_resolve_component_content_source_binding_supports_implicit_component_local_dir(
        self,
    ) -> None:
        catalog = _catalog(
            {
                "defaults": {
                    "metadataFile": "site/component.yaml",
                    "publication": {"origin": "docs"},
                },
                "components": [
                    {
                        "slug": "spark",
                        "localDir": "components/runtime",
                        "publication": {"mountPath": "/spark/"},
                        "artifacts": [],
                    }
                ],
            }
        )
        component = catalog.components[0]

        with tempfile.TemporaryDirectory() as tempdir:
            workspace_root = Path(tempdir)
            binding = resolve_component_content_source_binding(
                component=component,
                source_bindings={},
                workspace_root=workspace_root,
                default_metadata_file="site/component.yaml",
            )

        self.assertIsNotNone(binding)
        if binding is None:
            self.fail("expected an implicit component content source binding")
        self.assertEqual(binding.key, "component:spark")
        self.assertEqual(binding.local_dir, workspace_root / "components/runtime")
        self.assertEqual(binding.export_locator, Path("components/runtime"))
        self.assertEqual(
            binding.metadata_file,
            workspace_root / "components/runtime/site/component.yaml",
        )

    def test_normalize_workspace_relative_locator_normalizes_syntax(self) -> None:
        self.assertEqual(
            normalize_workspace_relative_locator("./components/runtime/"),
            Path("components/runtime"),
        )

    def test_resolve_component_source_roots_merges_content_and_artifact_usage(self) -> None:
        catalog = _catalog(
            {
                "defaults": {
                    "metadataFile": "site/component.yaml",
                    "docsRoot": "docs",
                    "publication": {"origin": "docs"},
                },
                "sources": {"runtime": {"localDir": "components/runtime"}},
                "components": [
                    {
                        "slug": "spark",
                        "content": {"source": "runtime"},
                        "publication": {"mountPath": "/spark/"},
                        "artifacts": [
                            {
                                "key": "runtime",
                                "source": "runtime",
                                "versioning": {
                                    "developmentRef": "main",
                                    "tagPattern": "^v.*$",
                                },
                            }
                        ],
                    }
                ],
            }
        )

        with tempfile.TemporaryDirectory() as tempdir:
            roots = resolve_component_source_roots(
                catalog=catalog, workspace_root=Path(tempdir)
            )

        self.assertEqual(len(roots), 1)
        root = roots[0]
        self.assertEqual(root.component_slug, "spark")
        self.assertEqual(root.local_dir.name, "runtime")
        self.assertEqual(root.export_locator, Path("components/runtime"))
        self.assertEqual(len(root.usages), 1)
        usage = root.usages[0]
        self.assertEqual(usage.source_binding.key, "runtime")
        self.assertTrue(usage.owns_component_content)
        self.assertEqual(usage.artifact_keys, ("runtime",))

    def test_resolve_component_source_roots_preserves_multiple_roots_for_one_component(
        self,
    ) -> None:
        catalog = _catalog(
            {
                "defaults": {
                    "docsRoot": "docs",
                    "publication": {"origin": "docs"},
                },
                "sources": {
                    "runtime": {"localDir": "components/runtime"},
                    "api": {"localDir": "components/api"},
                },
                "components": [
                    {
                        "slug": "spark",
                        "content": {"source": "runtime"},
                        "publication": {"mountPath": "/spark/"},
                        "artifacts": [
                            {
                                "key": "runtime",
                                "source": "runtime",
                                "docsRoot": "docs/runtime",
                                "versioning": {
                                    "developmentRef": "main",
                                    "tagPattern": "^v.*$",
                                },
                            },
                            {
                                "key": "api",
                                "source": "api",
                                "docsRoot": "docs",
                                "versioning": {
                                    "developmentRef": "main",
                                    "tagPattern": "^api-v.*$",
                                },
                            },
                        ],
                    }
                ],
            }
        )

        with tempfile.TemporaryDirectory() as tempdir:
            roots = resolve_component_source_roots(
                catalog=catalog, workspace_root=Path(tempdir)
            )

        self.assertEqual([root.local_dir.name for root in roots], ["runtime", "api"])
        self.assertEqual(
            [root.export_locator for root in roots],
            [Path("components/runtime"), Path("components/api")],
        )
        self.assertTrue(roots[0].usages[0].owns_component_content)
        self.assertEqual(roots[0].usages[0].artifact_keys, ("runtime",))
        self.assertFalse(roots[1].usages[0].owns_component_content)
        self.assertEqual(roots[1].usages[0].artifact_keys, ("api",))

    def test_resolve_component_content_source_binding_rejects_unknown_source(self) -> None:
        component = ComponentCatalogEntry.model_validate(
            {
                "slug": "spark",
                "content": {"source": "missing"},
                "publication": {"mountPath": "/spark/"},
                "artifacts": [],
            },
            by_alias=True,
            by_name=False,
        )

        with tempfile.TemporaryDirectory() as tempdir, self.assertRaisesRegex(
            ValueError, "references unknown source 'missing'"
        ):
            resolve_component_content_source_binding(
                component=component,
                source_bindings={},
                workspace_root=Path(tempdir),
                default_metadata_file=None,
            )

    def test_resolve_repo_path_rejects_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir, self.assertRaisesRegex(
            ValueError, "escapes declared root"
        ):
            resolve_repo_path(Path(tempdir), "../outside")


def _catalog(payload: dict[str, object]) -> SiteCatalogDocumentV1:
    document = {
        "schemaVersion": 1,
        "site": {},
        "origins": {"docs": {"baseUrl": "https://docs.example.org"}},
        **payload,
    }
    return SiteCatalogDocumentV1.model_validate(
        document,
        by_alias=True,
        by_name=False,
    )
