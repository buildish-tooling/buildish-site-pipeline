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

"""Direct coverage for route-validation helper branches."""

from __future__ import annotations

import unittest
from unittest import mock

from buildish_site_pipeline.evaluation.collector import DiagnosticCollector
from buildish_site_pipeline.evaluation.reference_index import KnownRoute, build_reference_index
from buildish_site_pipeline.evaluation import routes as route_evaluation


class RouteValidationTests(unittest.TestCase):
    def test_register_route_rejects_non_context_collisions_for_same_component(self) -> None:
        collector = DiagnosticCollector()
        published_route = self._route(route_id="component:spark", path="/spark/", route_kind="published")
        routes_by_lookup_key = {("docs", "/spark/"): published_route}

        route_evaluation._register_route(  # noqa: SLF001
            route=self._route(route_id="alias:spark:0", path="/spark/", route_kind="alias"),
            collector=collector,
            routes_by_lookup_key=routes_by_lookup_key,
        )

        self.assertEqual([entry.code for entry in collector.build()], ["publication-route-collision"])

    def test_validate_redirect_target_ignores_external_targets(self) -> None:
        collector = DiagnosticCollector()
        redirect_edges: dict[tuple[str, str], tuple[str, str]] = {}

        route_evaluation._validate_redirect_target(  # noqa: SLF001
            reference="https://example.org/spark/",
            source_origin_key="docs",
            source_path="/spark/legacy/",
            component_slug="spark",
            redirect_id="redirect:spark:0",
            collector=collector,
            reference_index=build_reference_index(routes_by_lookup_key={}, targets_by_reference={}),
            redirect_edges=redirect_edges,
        )

        self.assertEqual(collector.build(), ())
        self.assertEqual(redirect_edges, {})

    def test_validate_redirect_loops_reports_duplicate_cycles_only_once(self) -> None:
        collector = DiagnosticCollector()
        cycle = (("docs", "/a/"), ("docs", "/b/"))
        routes_by_lookup_key = {
            ("docs", "/a/"): self._route(route_id="redirect:a", path="/a/", route_kind="redirect"),
            ("docs", "/b/"): self._route(route_id="redirect:b", path="/b/", route_kind="redirect"),
        }
        redirect_edges = {
            ("docs", "/a/"): ("docs", "/b/"),
            ("docs", "/b/"): ("docs", "/a/"),
        }

        with mock.patch(
            "buildish_site_pipeline.evaluation.routes._find_cycle",
            side_effect=[cycle, tuple(reversed(cycle))],
        ):
            route_evaluation._validate_redirect_loops(  # noqa: SLF001
                redirect_edges=redirect_edges,
                routes_by_lookup_key=routes_by_lookup_key,
                collector=collector,
            )

        self.assertEqual([entry.code for entry in collector.build()], ["redirect-loop"])

    def test_find_cycle_returns_none_when_chain_reaches_visited_node(self) -> None:
        self.assertIsNone(
            route_evaluation._find_cycle(  # noqa: SLF001
                start=("docs", "/a/"),
                redirect_edges={("docs", "/a/"): ("docs", "/b/")},
                visited={("docs", "/b/")},
            )
        )

    @staticmethod
    def _route(*, route_id: str, path: str, route_kind: str) -> KnownRoute:
        return KnownRoute(
            route_id=route_id,
            origin_key="docs",
            path=path,
            component_slug="spark",
            route_kind=route_kind,
        )