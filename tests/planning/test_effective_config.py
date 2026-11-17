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

"""Tests for effective planning configuration resolution."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from buildish_site_pipeline.models import (
    ComponentMetadataDocumentV1,
    SiteCatalogDocumentV1,
)
from buildish_site_pipeline.planning.effective_config import (
    _join_public_path,
    _resolve_repo_path,
    resolve_site_config,
)


class EffectiveConfigResolutionTests(unittest.TestCase):
    def test_resolves_component_local_dir_into_implicit_content_source(self) -> None:
        catalog = SiteCatalogDocumentV1.model_validate(
            {
                "schemaVersion": 1,
                "defaults": {
                    "metadataFile": "site/component.yaml",
                    "publication": {"origin": "docs"},
                },
                "site": {},
                "origins": {"docs": {"baseUrl": "https://docs.example.org"}},
                "components": [
                    {
                        "slug": "spark",
                        "localDir": "components/runtime",
                        "publication": {"mountPath": "/spark/"},
                        "artifacts": [],
                    },
                ],
            },
            by_alias=True,
            by_name=False,
        )

        with tempfile.TemporaryDirectory() as tempdir:
            site = resolve_site_config(catalog=catalog, workspace_root=Path(tempdir))

        component = site.components[0]
        self.assertEqual(component.content_source.key, "component:spark")
        self.assertEqual(component.content_source.local_dir, site.workspace_root / "components/runtime")
        self.assertEqual(
            component.content_source.metadata_file,
            site.workspace_root / "components/runtime/site/component.yaml",
        )

    def test_resolves_defaults_groups_and_component_documents(self) -> None:
        catalog = SiteCatalogDocumentV1.model_validate(
            {
                "schemaVersion": 1,
                "defaults": {
                    "metadataFile": "site/component.yaml",
                    "pagesRoot": "site/pages",
                    "docsRoot": "site/docs",
                    "assetsRoot": "site/assets",
                    "publication": {"origin": "docs"},
                },
                "site": {
                    "pagesRoot": "site/root-pages",
                    "assetsRoot": "site/root-assets",
                    "vendorAssets": [
                        {"source": "vendor/brand", "mountPath": "/assets/vendor/brand/"}
                    ],
                },
                "origins": {"docs": {"baseUrl": "https://docs.example.org"}},
                "sources": {"runtime": {"localDir": "components/runtime"}},
                "groups": {"streaming": {"pathPrefix": "/streaming/"}},
                "components": [
                    {
                        "slug": "spark",
                        "group": "streaming",
                        "content": {"source": "runtime"},
                        "publication": {"pathSegment": "spark"},
                        "artifacts": [
                            {
                                "key": "runtime",
                                "source": "runtime",
                            },
                        ],
                    },
                ],
            },
            by_alias=True,
            by_name=False,
        )
        component_document = ComponentMetadataDocumentV1.model_validate(
            {
                "schemaVersion": 1,
                "component": {"slug": "spark"},
                "artifacts": [{"key": "runtime"}],
                "content": {
                    "pagesRoot": "docs/pages",
                    "docsRoot": "docs/rendered",
                    "assetsRoot": "docs/assets",
                },
            },
            by_alias=True,
            by_name=False,
        )

        with tempfile.TemporaryDirectory() as tempdir:
            site = resolve_site_config(
                catalog=catalog,
                workspace_root=Path(tempdir),
                component_documents={"spark": component_document},
            )

        component = site.components[0]
        artifact = component.artifacts[0]
        self.assertEqual(component.publication.component_path, "/streaming/spark/")
        self.assertEqual(
            component.publication.development_url,
            "https://docs.example.org/streaming/spark/development/",
        )
        self.assertEqual(
            component.publication.docs_url,
            "https://docs.example.org/streaming/spark/development/",
        )
        self.assertEqual(
            component.publication.assets_url,
            "https://docs.example.org/streaming/spark/assets/",
        )
        self.assertEqual(component.pages_root.name, "pages")
        self.assertEqual(component.docs_root.name, "rendered")
        self.assertEqual(artifact.docs_root.name, "rendered")

    def test_preserves_explicit_nested_publication_segments(self) -> None:
        catalog = SiteCatalogDocumentV1.model_validate(
            {
                "schemaVersion": 1,
                "defaults": {
                    "publication": {
                        "origin": "docs",
                        "developmentSegment": "development",
                        "docsSegment": "docs",
                        "assetsSegment": "assets",
                    },
                },
                "site": {},
                "origins": {"docs": {"baseUrl": "https://docs.example.org"}},
                "sources": {"runtime": {"localDir": "components/runtime"}},
                "components": [
                    {
                        "slug": "spark",
                        "content": {"source": "runtime"},
                        "publication": {"mountPath": "/spark/"},
                        "artifacts": [],
                    },
                ],
            },
            by_alias=True,
            by_name=False,
        )

        with tempfile.TemporaryDirectory() as tempdir:
            site = resolve_site_config(catalog=catalog, workspace_root=Path(tempdir))

        publication = site.components[0].publication
        self.assertEqual(publication.development_path, "/spark/development/")
        self.assertEqual(publication.docs_path, "/spark/development/docs/")
        self.assertEqual(publication.assets_path, "/spark/assets/")

    def test_rejects_unresolvable_component_publication_path(self) -> None:
        catalog = SiteCatalogDocumentV1.model_validate(
            {
                "schemaVersion": 1,
                "defaults": {"publication": {"origin": "docs"}},
                "site": {},
                "origins": {"docs": {"baseUrl": "https://docs.example.org"}},
                "sources": {"runtime": {"localDir": "components/runtime"}},
                "components": [{"slug": "spark", "artifacts": []}],
            },
            by_alias=True,
            by_name=False,
        )
        with tempfile.TemporaryDirectory() as tempdir, self.assertRaises(ValueError):
            resolve_site_config(catalog=catalog, workspace_root=Path(tempdir))

    def test_rejects_missing_publication_origin(self) -> None:
        catalog = SiteCatalogDocumentV1.model_validate(
            {
                "schemaVersion": 1,
                "site": {},
                "components": [
                    {
                        "slug": "spark",
                        "publication": {"mountPath": "/spark/"},
                        "artifacts": [],
                    },
                ],
            },
            by_alias=True,
            by_name=False,
        )

        with tempfile.TemporaryDirectory() as tempdir, self.assertRaisesRegex(
            ValueError, "cannot resolve a publication origin"
        ):
            resolve_site_config(catalog=catalog, workspace_root=Path(tempdir))

    def test_allows_component_without_bound_content_source(self) -> None:
        catalog = SiteCatalogDocumentV1.model_validate(
            {
                "schemaVersion": 1,
                "defaults": {"publication": {"origin": "docs"}},
                "site": {},
                "origins": {"docs": {"baseUrl": "https://docs.example.org"}},
                "components": [
                    {
                        "slug": "spark",
                        "publication": {"mountPath": "/spark/"},
                        "artifacts": [],
                    },
                ],
            },
            by_alias=True,
            by_name=False,
        )

        with tempfile.TemporaryDirectory() as tempdir:
            site = resolve_site_config(catalog=catalog, workspace_root=Path(tempdir))

        component = site.components[0]
        self.assertIsNone(component.content_source)
        self.assertIsNone(component.pages_root)
        self.assertIsNone(component.docs_root)
        self.assertIsNone(component.assets_root)

    def test_resolves_component_localization_from_defaults_and_overrides(self) -> None:
        catalog = SiteCatalogDocumentV1.model_validate(
            {
                "schemaVersion": 1,
                "defaults": {
                    "publication": {"origin": "docs"},
                    "localization": {
                        "supportedLocales": ["en", "de"],
                        "defaultLocale": "en",
                        "fallbackLocale": "de",
                        "routeMode": "prefixAll",
                    },
                },
                "site": {},
                "origins": {"docs": {"baseUrl": "https://docs.example.org"}},
                "sources": {"runtime": {"localDir": "components/runtime"}},
                "components": [
                    {
                        "slug": "spark",
                        "content": {"source": "runtime"},
                        "localization": {"supportedLocales": ["de", "fr"], "defaultLocale": "fr"},
                        "publication": {"mountPath": "/spark/"},
                        "artifacts": [],
                    },
                ],
            },
            by_alias=True,
            by_name=False,
        )

        with tempfile.TemporaryDirectory() as tempdir:
            site = resolve_site_config(catalog=catalog, workspace_root=Path(tempdir))

        localization = site.components[0].localization
        self.assertEqual(("de", "fr"), localization.supported_locales)
        self.assertEqual("fr", localization.default_locale)
        self.assertEqual("de", localization.fallback_locale)
        self.assertEqual("prefixAll", localization.route_mode.value)

    def test_resolves_site_link_check_policy(self) -> None:
        catalog = SiteCatalogDocumentV1.model_validate(
            {
                "schemaVersion": 1,
                "site": {},
                "validation": {
                    "linkChecks": {
                        "enabled": True,
                        "mode": "file-html",
                        "checkRootAbsolute": True,
                        "internalPrefixes": ["/components/", "/docs/"],
                    }
                },
                "origins": {"docs": {"baseUrl": "https://docs.example.org"}},
                "components": [
                    {
                        "slug": "spark",
                        "publication": {"origin": "docs", "mountPath": "/spark/"},
                        "artifacts": [],
                    },
                ],
            },
            by_alias=True,
            by_name=False,
        )

        with tempfile.TemporaryDirectory() as tempdir:
            site = resolve_site_config(catalog=catalog, workspace_root=Path(tempdir))

        self.assertIsNotNone(site.link_checks)
        self.assertTrue(site.link_checks.enabled)
        self.assertEqual(site.link_checks.mode.value, "file-html")
        self.assertEqual(site.link_checks.internal_prefixes, ("/components/", "/docs/"))

    def test_join_public_path_handles_root_prefix(self) -> None:
        self.assertEqual(_join_public_path("/", "spark"), "/spark/")

    def test_resolve_repo_path_rejects_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir, self.assertRaisesRegex(
            ValueError, "escapes declared root"
        ):
            _resolve_repo_path(Path(tempdir), "../outside")

class PublicationSelectionInheritanceTests(unittest.TestCase):
    @staticmethod
    def inputs():
        from buildish_site_pipeline.models import ProviderSnapshotDocumentV1

        catalog = {
            "schemaVersion": 1,
            "defaults": {"docsRoot": "docs", "publication": {"origin": "docs"}},
            "site": {},
            "origins": {"docs": {"baseUrl": "https://docs.example.org"}},
            "components": [{
                "slug": "spark", "localDir": "component",
                "publication": {"mountPath": "/spark/"},
                "artifacts": [{"key": "runtime"}],
            }],
        }
        document = ComponentMetadataDocumentV1.model_validate({
            "schemaVersion": 1, "component": {"slug": "spark"},
            "artifacts": [{"key": "runtime", "versioning": {
                "developmentRef": "main",
                "namedRefs": [{"key": "preview", "ref": "preview"}],
            }}],
        })
        snapshot = ProviderSnapshotDocumentV1.model_validate({
            "schemaVersion": 1, "providers": [], "records": [],
            "artifacts": [{"componentSlug": "spark", "artifactKey": "runtime",
                "latestStable": "1.0",
                "releaseLines": [{"key": "1", "latest": "1.0", "maintenanceRef": "v1"}],
                "releases": [{"version": "1.0", "releaseLine": "1"}],
            }],
        })
        return catalog, document, snapshot

    def resolve(self, catalog, document, snapshot):
        from buildish_site_pipeline.planning.provider_index import build_provider_snapshot_index

        authored = SiteCatalogDocumentV1.model_validate(catalog)
        before = (authored.model_dump(), document.model_dump(), snapshot.model_dump())
        site = resolve_site_config(
            catalog=authored, workspace_root=Path("/workspace"),
            component_documents={"spark": document}, provider_snapshot=snapshot,
        )
        index = build_provider_snapshot_index(provider_snapshot=snapshot, site=site)
        self.assertEqual(before, (authored.model_dump(), document.model_dump(), snapshot.model_dump()))
        return site, index

    def selected(self, catalog, document, snapshot):
        from buildish_site_pipeline.planning.selection import select_version_contexts

        site, index = self.resolve(catalog, document, snapshot)
        selected = select_version_contexts(site=site, provider_index=index)
        return [(c.kind.value, c.version, c.named_ref_key) for c in selected.contexts]

    def test_partial_artifact_preserves_component_development_and_release(self):
        catalog, document, snapshot = self.inputs()
        component = catalog["components"][0]
        component["publicationSelection"] = {
            "development": True, "lineHeads": {"mode": "none"},
            "releases": {"mode": "explicit", "versions": ["1.0"]},
        }
        component["artifacts"][0]["publicationSelection"] = {"namedRefs": []}
        self.assertEqual(self.selected(catalog, document, snapshot), [
            ("development", None, None), ("released", "1.0", None),
        ])

    def test_omitted_null_and_empty_policy_fields_inherit_at_both_levels(self):
        for level in ("component", "artifact"):
            for policy in (None, {}, {"development": None, "lineHeads": None,
                                      "releases": None, "namedRefs": None, "candidates": None}):
                with self.subTest(level=level, policy=policy):
                    catalog, document, snapshot = self.inputs()
                    component = catalog["components"][0]
                    target = component if level == "component" else component["artifacts"][0]
                    target["publicationSelection"] = policy
                    self.assertEqual(self.selected(catalog, document, snapshot), [
                        ("development", None, None), ("lineHead", None, None),
                        ("released", "1.0", None),
                    ])
                    site, _ = self.resolve(catalog, document, snapshot)
                    for resolved in (site.components[0], site.components[0].artifacts[0]):
                        self.assertTrue(all(value is not None for value in
                                            resolved.publication_selection.model_dump().values()))
        catalog, document, snapshot = self.inputs()
        catalog["components"][0]["publicationSelection"] = {"development": False}
        catalog["components"][0].pop("artifacts")
        self.assertEqual(self.selected(catalog, document, snapshot), [
            ("lineHead", None, None), ("released", "1.0", None),
        ])

    def test_full_override_disables_kinds_and_replaces_named_refs(self):
        catalog, document, snapshot = self.inputs()
        component = catalog["components"][0]
        component["publicationSelection"] = {"namedRefs": ["preview"]}
        component["artifacts"][0]["publicationSelection"] = {
            "development": False, "lineHeads": {"mode": "none"},
            "releases": {"mode": "none"}, "namedRefs": [], "candidates": {"mode": "none"},
        }
        self.assertEqual(self.selected(catalog, document, snapshot), [])
        component["artifacts"][0]["publicationSelection"]["namedRefs"] = ["preview"]
        self.assertEqual(self.selected(catalog, document, snapshot), [("namedRef", None, "preview")])

    def test_nested_modes_replace_atomically_and_artifacts_are_independent(self):
        for parent, child in (
            ({"releases": {"mode": "latestN", "count": 2}},
             {"releases": {"mode": "explicit", "versions": ["1.0"]}}),
            ({"releases": {"mode": "explicit", "versions": ["1.0"]}},
             {"releases": {"mode": "latestN", "count": 1}}),
            ({"lineHeads": {"mode": "explicit", "keys": ["1"]}},
             {"lineHeads": {"mode": "allAuthored"}}),
            ({"candidates": {"mode": "explicit", "versions": ["2-rc1"], "externalIds": ["rc1"]}},
             {"candidates": {"mode": "latest"}}),
        ):
            with self.subTest(parent=parent, child=child):
                catalog, document, snapshot = self.inputs()
                document = ComponentMetadataDocumentV1.model_validate({
                    **document.model_dump(by_alias=True),
                    "artifacts": [*document.model_dump(by_alias=True)["artifacts"], {"key": "other"}],
                })
                component = catalog["components"][0]
                component["publicationSelection"] = {**parent, "namedRefs": ["preview"]}
                component["artifacts"][0]["publicationSelection"] = {**child, "namedRefs": []}
                site, _ = self.resolve(catalog, document, snapshot)
                first, second = site.components[0].artifacts
                key = next(iter(child))
                actual = first.publication_selection.model_dump(by_alias=True, exclude_none=True)[key]
                self.assertEqual(actual, child[key])
                self.assertEqual(second.publication_selection.model_dump(by_alias=True, exclude_none=True)[key], parent[key])
                self.assertEqual(second.publication_selection.named_refs, ["preview"])
                self.assertEqual(first.publication_selection.named_refs, [])
                self.assertIsNot(first.publication_selection.named_refs, second.publication_selection.named_refs)

    def test_artifactless_components_apply_only_effective_development(self):
        from dataclasses import replace
        from buildish_site_pipeline.planning.selection import select_version_contexts

        for policy, expected in ((None, 1), ({}, 1), ({"namedRefs": []}, 1),
                                 ({"development": False}, 0)):
            with self.subTest(policy=policy):
                catalog, _, snapshot = self.inputs()
                component = catalog["components"][0]
                component["publicationSelection"] = policy
                component.pop("artifacts")
                document = ComponentMetadataDocumentV1.model_validate({
                    "schemaVersion": 1, "component": {"slug": "spark"},
                })
                snapshot = type(snapshot).model_validate({"schemaVersion": 1, "providers": [], "records": []})
                site, index = self.resolve(catalog, document, snapshot)
                selected = select_version_contexts(site=site, provider_index=index)
                self.assertEqual(len(selected.contexts), expected)
                for field in ("docs_root", "content_source"):
                    missing = replace(site, components=(replace(site.components[0], **{field: None}),))
                    self.assertEqual(select_version_contexts(site=missing, provider_index=index).contexts, ())

    def test_inherited_reference_errors_match_explicit_artifact_policies(self):
        from types import SimpleNamespace
        from buildish_site_pipeline.evaluation.collector import DiagnosticCollector
        from buildish_site_pipeline.evaluation.reference_index import _validate_selection_references
        from buildish_site_pipeline.planning.selection import select_version_contexts

        for field, value, message, detail in (
            ("releases", {"mode": "explicit", "versions": ["missing"]}, "unknown exact release", {"version": "missing"}),
            ("namedRefs", ["missing"], "Unknown namedRef key", {"namedRefKey": "missing"}),
            ("lineHeads", {"mode": "explicit", "keys": ["missing"]}, "Unknown selected release-line", None),
        ):
            results = []
            for placement in ("component", "partial-child", "artifact"):
                with self.subTest(field=field, placement=placement):
                    catalog, document, snapshot = self.inputs()
                    component = catalog["components"][0]
                    policy = {field: value}
                    if placement == "artifact":
                        component["artifacts"][0]["publicationSelection"] = policy
                    else:
                        component["publicationSelection"] = policy
                        if placement == "partial-child":
                            component["artifacts"][0]["publicationSelection"] = {"development": False}
                    site, index = self.resolve(catalog, document, snapshot)
                    if field != "releases":
                        with self.assertRaisesRegex(ValueError, message):
                            select_version_contexts(site=site, provider_index=index)
                    collector = DiagnosticCollector()
                    _validate_selection_references(
                        component_slug="spark", artifact=site.components[0].artifacts[0],
                        planning=SimpleNamespace(provider_index=index, snapshot_inputs=()), collector=collector,
                    )
                    diagnostics = collector.build()
                    results.append([(d.code, d.details) for d in diagnostics])
                    if detail is not None:
                        self.assertEqual(results[-1], [("reference-configuration-invalid", detail)])
            self.assertEqual(results[0], results[1])
            self.assertEqual(results[0], results[2])

    def test_explicit_suppression_removes_invalid_inherited_selectors(self):
        catalog, document, snapshot = self.inputs()
        component = catalog["components"][0]
        component["publicationSelection"] = {
            "releases": {"mode": "explicit", "versions": ["missing"]},
            "lineHeads": {"mode": "explicit", "keys": ["missing"]}, "namedRefs": ["missing"],
        }
        component["artifacts"][0]["publicationSelection"] = {
            "releases": {"mode": "none"}, "lineHeads": {"mode": "none"}, "namedRefs": [],
        }
        self.assertEqual(self.selected(catalog, document, snapshot), [("development", None, None)])
        from types import SimpleNamespace
        from buildish_site_pipeline.evaluation.collector import DiagnosticCollector
        from buildish_site_pipeline.evaluation.reference_index import _validate_selection_references

        site, index = self.resolve(catalog, document, snapshot)
        collector = DiagnosticCollector()
        _validate_selection_references(
            component_slug="spark", artifact=site.components[0].artifacts[0],
            planning=SimpleNamespace(provider_index=index, snapshot_inputs=()), collector=collector,
        )
        self.assertEqual(collector.build(), ())

    def test_release_line_integrity_is_checked_without_authored_selection_or_when_disabled(self):
        from types import SimpleNamespace
        from buildish_site_pipeline.evaluation.collector import DiagnosticCollector
        from buildish_site_pipeline.evaluation.reference_index import _validate_selection_references

        for policy in (None, {"releases": {"mode": "none"}}):
            with self.subTest(policy=policy):
                catalog, document, snapshot = self.inputs()
                catalog["components"][0]["publicationSelection"] = policy
                data = snapshot.model_dump(by_alias=True)
                data["artifacts"][0]["releases"][0]["releaseLine"] = "missing"
                data["artifacts"][0]["releaseLines"] = []
                data["artifacts"][0].pop("latestStable", None)
                snapshot = type(snapshot).model_validate(data)
                # Reference validation is tested independently of earlier latest-fact checks.
                site = resolve_site_config(
                    catalog=SiteCatalogDocumentV1.model_validate(catalog), workspace_root=Path("/workspace"),
                    component_documents={"spark": document}, provider_snapshot=snapshot,
                )
                _, index = self.resolve(*self.inputs())
                collector = DiagnosticCollector()
                _validate_selection_references(
                    component_slug="spark", artifact=site.components[0].artifacts[0],
                    planning=SimpleNamespace(provider_index=index, snapshot_inputs=()), collector=collector,
                )
                self.assertEqual([d.details for d in collector.build()], [
                    {"version": "1.0", "releaseLine": "missing"},
                ])

    def test_null_artifact_fields_retain_nondefault_component_choices(self):
        catalog, document, snapshot = self.inputs()
        component = catalog["components"][0]
        component["publicationSelection"] = {
            "development": False, "lineHeads": {"mode": "none"},
            "releases": {"mode": "none"}, "namedRefs": ["preview"],
            "candidates": {"mode": "latest"},
        }
        component["artifacts"][0]["publicationSelection"] = {
            key: None for key in component["publicationSelection"]
        }
        self.assertEqual(self.selected(catalog, document, snapshot), [("namedRef", None, "preview")])
        site, _ = self.resolve(catalog, document, snapshot)
        self.assertEqual(
            site.components[0].artifacts[0].publication_selection.model_dump(),
            site.components[0].publication_selection.model_dump(),
        )
