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

"""Executable contracts for growth-oriented and compatibility-status guides."""

from __future__ import annotations

import io
import json
import re
import unittest
from pathlib import Path

from buildish_site_pipeline.cli import _run, parse_invocation
from buildish_site_pipeline.cli.contract import BuildInvocation, CheckInvocation, PlanInvocation
from buildish_site_pipeline.models.authored.site_catalog import LocalizationConfig
from tests.support.workspace import _cwd, _workspace


_SMALL_GUIDE = Path("site/pages/getting-started/small.md")
_VERY_LARGE_GUIDE = Path("site/pages/getting-started/very-large.md")
_VERSIONING_GUIDE = Path("site/pages/how-to/model-versioning-and-redirects.md")
_GROUPS_GUIDE = Path(
    "site/pages/how-to/organize-grouped-components-and-publication-policy.md"
)
_PLANNING_GUIDE = Path("site/pages/how-to/plan-publication-and-materialization.md")
_SCALE_GUIDE = Path("site/pages/how-to/scale-site-pipeline-operations.md")
_ENRICHMENT_GUIDE = Path(
    "site/pages/how-to/integrate-provider-compatibility-and-translation-data.md"
)
_JEKYLL_STATUS = Path("site/pages/how-to/integrate-with-jekyll.md")
_MKDOCS_STATUS = Path("site/pages/how-to/integrate-with-mkdocs.md")
_DOCS_STRATEGY = Path("site/pages/maintenance/user-facing-docs-strategy.md")
_TARGET_GUIDES = (
    _SMALL_GUIDE,
    _VERY_LARGE_GUIDE,
    _VERSIONING_GUIDE,
    _GROUPS_GUIDE,
    _PLANNING_GUIDE,
    _SCALE_GUIDE,
    _ENRICHMENT_GUIDE,
    _JEKYLL_STATUS,
    _MKDOCS_STATUS,
    _DOCS_STRATEGY,
)
_MARKDOWN_LINK_PATTERN = re.compile(r"\[[^]]+\]\(([^)]+)\)")


class GrowthGuideDocumentationTests(unittest.TestCase):
    """Keep copied growth examples aligned with executable pipeline behavior."""

    def test_small_site_packet_matches_versioned_single_artifact_fixture(self) -> None:
        guide_text = _SMALL_GUIDE.read_text(encoding="utf-8")

        for expected in (
            "provider-snapshot.json",
            "mode: allAuthored",
            "mode: latestPerLine",
            "line-head:spark:runtime:4.0",
            "/spark/releases/4.0.0/",
            "data/releases.json",
            "data/refs.json",
        ):
            self.assertIn(expected, guide_text)

        with _workspace(with_content_file=True) as workspace_root:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(argv=["build"], stdout=stdout, stderr=stderr)
            routes = json.loads(
                (workspace_root / "site/.stage/data/routes.json").read_text(
                    encoding="utf-8"
                )
            )["items"]
            paths_by_target = {entry["targetId"]: entry["path"] for entry in routes}

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(
            paths_by_target["development:spark:runtime"],
            "/spark/development/",
        )
        self.assertEqual(
            paths_by_target["line-head:spark:runtime:4.0"],
            "/spark/development/4.0/",
        )
        self.assertEqual(
            paths_by_target["released:spark:runtime:4.0.0"],
            "/spark/releases/4.0.0/",
        )

    def test_versioning_redirect_example_resolves_to_documented_output(self) -> None:
        guide_text = _VERSIONING_GUIDE.read_text(encoding="utf-8")
        with _workspace(with_content_file=True) as workspace_root:
            catalog_path = workspace_root / "site/catalog.yaml"
            catalog_text = catalog_path.read_text(encoding="utf-8")
            catalog_text = catalog_text.replace(
                "    publication:\n      mountPath: /spark/\n",
                "    publication:\n"
                "      mountPath: /spark/\n"
                "      redirects:\n"
                "        - fromPath: /spark/development/docs/\n"
                "          target: release:spark/runtime@4.0.0\n"
                "          status: 308\n"
                "          reason: Current docs live on the latest release route.\n",
                1,
            )
            catalog_path.write_text(catalog_text, encoding="utf-8")
            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(argv=["build"], stdout=stdout, stderr=stderr)
            redirects = json.loads(
                (workspace_root / "site/.stage/data/redirects.json").read_text(
                    encoding="utf-8"
                )
            )["items"]
            redirect = next(
                entry
                for entry in redirects
                if entry["fromUrl"]
                == "https://docs.example.org/spark/development/docs/"
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(
            redirect["toUrl"],
            "https://docs.example.org/spark/releases/4.0.0/",
        )
        self.assertEqual(redirect["status"], 308)
        for value in (redirect["fromUrl"], redirect["toUrl"], redirect["reason"]):
            self.assertIn(value, guide_text)

    def test_group_and_enrichment_guides_match_grouped_fixture(self) -> None:
        group_text = _GROUPS_GUIDE.read_text(encoding="utf-8")
        enrichment_text = _ENRICHMENT_GUIDE.read_text(encoding="utf-8")
        with _workspace(
            with_content_file=True,
            topology="grouped_large",
        ) as workspace_root:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with _cwd(workspace_root):
                exit_code = _run(argv=["build"], stdout=stdout, stderr=stderr)
            stage_root = workspace_root / "site/.stage"
            routes = json.loads(
                (stage_root / "data/routes.json").read_text(encoding="utf-8")
            )["items"]
            compatibility = json.loads(
                (stage_root / "data/compatibility.json").read_text(
                    encoding="utf-8"
                )
            )["items"]

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr.getvalue(), "")
        route_paths = {entry["path"] for entry in routes}
        self.assertIn("/platform/spark/", route_paths)
        self.assertIn("/platform/spark-operator/", route_paths)
        self.assertIn("/platform/spark/", group_text)
        self.assertIn("/platform/spark-operator/", group_text)
        self.assertTrue(
            any(
                entry["subjectId"] == "component:spark"
                and entry["targetId"] == "component:spark-operator"
                and entry["relation"] == "testedWith"
                for entry in compatibility
            )
        )
        self.assertIn('"subjectId": "component:spark"', enrichment_text)
        self.assertIn('"targetId": "component:spark-operator"', enrichment_text)

    def test_planning_guides_use_stable_commands_and_report_fields(self) -> None:
        planning_text = _PLANNING_GUIDE.read_text(encoding="utf-8")
        scale_text = _SCALE_GUIDE.read_text(encoding="utf-8")
        plan_args = [
            "plan",
            "--for",
            "build",
            "--report-format",
            "json",
            "--report-schema-version",
            "1",
        ]

        self.assertIsInstance(parse_invocation(plan_args), PlanInvocation)
        self.assertIsInstance(parse_invocation(["check"]), CheckInvocation)
        self.assertIsInstance(parse_invocation(["build"]), BuildInvocation)
        documented_plan = "site-pipeline " + " ".join(plan_args)
        self.assertIn(documented_plan, planning_text)
        for expected in (
            '"schemaVersion": 1',
            '"target": "build"',
            '"inputKind": "released"',
            '"status": "present"',
            '"watchEligible": false',
        ):
            self.assertIn(expected, planning_text)
        self.assertIn("materialization-report.json", scale_text)
        self.assertIn("check-report.json", scale_text)

    def test_localization_examples_use_the_current_authored_contract(self) -> None:
        very_large_text = _VERY_LARGE_GUIDE.read_text(encoding="utf-8")
        enrichment_text = _ENRICHMENT_GUIDE.read_text(encoding="utf-8")
        localization = LocalizationConfig.model_validate(
            {
                "supportedLocales": ["en", "de"],
                "defaultLocale": "en",
                "fallbackLocale": "en",
                "routeMode": "prefixAll",
            },
            by_alias=True,
            by_name=False,
        )

        self.assertEqual(localization.default_locale, "en")
        for guide_text in (very_large_text, enrichment_text):
            for expected in (
                "supportedLocales: [en, de]",
                "defaultLocale: en",
                "fallbackLocale: en",
                "routeMode: prefixAll",
                "data/translations.json",
            ):
                self.assertIn(expected, guide_text)

    def test_unverified_renderer_pages_are_honest_status_records(self) -> None:
        for status_path, renderer in (
            (_JEKYLL_STATUS, "Jekyll"),
            (_MKDOCS_STATUS, "MkDocs"),
        ):
            status_text = status_path.read_text(encoding="utf-8")
            normalized_status_text = " ".join(status_text.split())
            with self.subTest(renderer=renderer):
                self.assertIn(f"title: {renderer} integration status", status_text)
                self.assertIn(
                    "has not been verified locally",
                    normalized_status_text,
                )
                self.assertIn(
                    "does not provide a turnkey recipe",
                    normalized_status_text,
                )
                self.assertIn("## Acceptance criteria for a real guide", status_text)
                self.assertIn("[Hugo](../integrate-with-hugo/)", status_text)
                self.assertIn("[Roq](../integrate-with-roq/)", status_text)

    def test_strategy_describes_the_current_concepts_layer(self) -> None:
        strategy_text = _DOCS_STRATEGY.read_text(encoding="utf-8")

        self.assertIn("The `concepts/` layer now provides", strategy_text)
        self.assertNotIn("The missing layer today is `concepts/`", strategy_text)
        self.assertIn("renderer status pages", strategy_text)

    def test_growth_guide_links_use_relative_pretty_routes(self) -> None:
        for guide_path in _TARGET_GUIDES:
            guide_text = guide_path.read_text(encoding="utf-8")
            for target in _MARKDOWN_LINK_PATTERN.findall(guide_text):
                with self.subTest(guide=guide_path.as_posix(), target=target):
                    self.assertFalse(target.startswith("/"))
                    self.assertNotIn(".md", target)
                    self.assertNotIn("site/pages/", target)
                    self.assertNotEqual(target, "docs/")
                    self.assertFalse(target.startswith("docs/"))
                    self.assertNotIn("/docs/", target)


if __name__ == "__main__":
    unittest.main()
