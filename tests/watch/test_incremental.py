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

"""Incremental watch equivalence tests against fresh clean builds."""

from __future__ import annotations

import io
import json
import threading
import unittest
import unittest.mock

from buildish_site_pipeline.cli import _run
from buildish_site_pipeline.commands.shared import load_workspace_inputs
from buildish_site_pipeline.evaluation import EvaluationMode, EvaluationRequest, run_evaluation
from buildish_site_pipeline.models.enums import RecordKind
from buildish_site_pipeline.models.enums import PlanningTarget
from buildish_site_pipeline.planning import evaluate_planning
from buildish_site_pipeline.staging.coordinator import materialize_stage_tree
from tests.support.staging import _expand_workspace_for_multiple_owned_units, _stage_snapshot
from tests.support.workspace import _cwd, _fake_watch_event_stream_factory, _workspace


class WatchIncrementalTests(unittest.TestCase):
    def test_component_edit_matches_fresh_clean_build(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            _expand_workspace_for_multiple_owned_units(workspace_root)
            watched_file = workspace_root / "components/runtime/docs/releases/4.0.0/index.md"

            def _mutate_component_page():
                watched_file.write_text("hello from incremental watch\n", encoding="utf-8")
                return (watched_file,)

            watch_snapshot = _run_watch_then_snapshot(
                workspace_root=workspace_root,
                responses=[(True, _mutate_component_page), (False, None)],
            )
            build_exit_code, build_snapshot = _run_clean_build_snapshot(workspace_root)

        self.assertEqual(build_exit_code, 0)
        self.assertEqual(watch_snapshot, build_snapshot)

    def test_provider_snapshot_edit_matches_fresh_clean_build(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            _expand_workspace_for_multiple_owned_units(workspace_root)
            provider_snapshot_path = workspace_root / "site/provider-snapshot.json"

            def _mutate_provider_snapshot():
                document = json.loads(provider_snapshot_path.read_text(encoding="utf-8"))
                document["providers"][0]["fetchedAt"] = "2026-04-04T00:00:00Z"
                provider_snapshot_path.write_text(json.dumps(document) + "\n", encoding="utf-8")
                return (provider_snapshot_path,)

            watch_snapshot = _run_watch_then_snapshot(
                workspace_root=workspace_root,
                responses=[(True, _mutate_provider_snapshot), (False, None)],
            )
            build_exit_code, build_snapshot = _run_clean_build_snapshot(workspace_root)

        self.assertEqual(build_exit_code, 0)
        self.assertEqual(watch_snapshot, build_snapshot)

    def test_catalog_mount_path_edit_matches_fresh_clean_build(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            _expand_workspace_for_multiple_owned_units(workspace_root)
            catalog_path = workspace_root / "site/catalog.yaml"

            def _mutate_catalog_mount_path():
                catalog_text = catalog_path.read_text(encoding="utf-8")
                catalog_path.write_text(catalog_text.replace("mountPath: /spark/", "mountPath: /spark-docs/"), encoding="utf-8")
                return (catalog_path,)

            watch_snapshot = _run_watch_then_snapshot(
                workspace_root=workspace_root,
                responses=[(True, _mutate_catalog_mount_path), (False, None)],
            )
            build_exit_code, build_snapshot = _run_clean_build_snapshot(workspace_root)

        self.assertEqual(build_exit_code, 0)
        self.assertEqual(watch_snapshot, build_snapshot)

    def test_catalog_alias_route_edit_matches_fresh_clean_build(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            _expand_workspace_for_multiple_owned_units(workspace_root)
            catalog_path = workspace_root / "site/catalog.yaml"

            def _mutate_catalog_alias_route():
                return _rewrite_catalog(
                    catalog_path,
                    replacements=(
                        (
                            "    publication:\n      mountPath: /spark/\n",
                            "    publication:\n      mountPath: /spark/\n      aliases:\n        - path: /spark/development/docs/\n",
                        ),
                    ),
                )

            watch_snapshot = _run_watch_then_snapshot(
                workspace_root=workspace_root,
                responses=[(True, _mutate_catalog_alias_route), (False, None)],
            )
            build_exit_code, build_snapshot = _run_clean_build_snapshot(workspace_root)

        self.assertEqual(build_exit_code, 0)
        self.assertEqual(watch_snapshot, build_snapshot)

    def test_catalog_redirect_edit_matches_fresh_clean_build(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            _expand_workspace_for_multiple_owned_units(workspace_root)
            catalog_path = workspace_root / "site/catalog.yaml"

            def _mutate_catalog_redirect():
                return _rewrite_catalog(
                    catalog_path,
                    replacements=(
                        (
                            "    publication:\n      mountPath: /spark/\n",
                            "    publication:\n      mountPath: /spark/\n      redirects:\n        - fromPath: /spark/development/docs/\n          target: route:/spark/\n",
                        ),
                    ),
                )

            watch_snapshot = _run_watch_then_snapshot(
                workspace_root=workspace_root,
                responses=[(True, _mutate_catalog_redirect), (False, None)],
            )
            build_exit_code, build_snapshot = _run_clean_build_snapshot(workspace_root)

        self.assertEqual(build_exit_code, 0)
        self.assertEqual(watch_snapshot, build_snapshot)

    def test_catalog_canonical_path_edit_matches_fresh_clean_build(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            _expand_workspace_for_multiple_owned_units(workspace_root)
            catalog_path = workspace_root / "site/catalog.yaml"

            def _mutate_catalog_canonical_path():
                return _rewrite_catalog(
                    catalog_path,
                    replacements=(
                        (
                            "    publication:\n      mountPath: /spark/\n",
                            "    publication:\n      mountPath: /spark/\n      canonicalPath: /spark/development/\n",
                        ),
                    ),
                )

            watch_snapshot = _run_watch_then_snapshot(
                workspace_root=workspace_root,
                responses=[(True, _mutate_catalog_canonical_path), (False, None)],
            )
            build_exit_code, build_snapshot = _run_clean_build_snapshot(workspace_root)

        self.assertEqual(build_exit_code, 0)
        self.assertEqual(watch_snapshot, build_snapshot)

    def test_catalog_origin_edit_matches_fresh_clean_build(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            _expand_workspace_for_multiple_owned_units(workspace_root)
            catalog_path = workspace_root / "site/catalog.yaml"

            def _mutate_catalog_origin():
                return _rewrite_catalog(
                    catalog_path,
                    replacements=(
                        (
                            "origins:\n  docs:\n    baseUrl: https://docs.example.org\n",
                            "origins:\n  docs:\n    baseUrl: https://docs.example.org\n  archive:\n    baseUrl: https://archive.example.org\n",
                        ),
                        (
                            "    publication:\n      mountPath: /spark/\n",
                            "    publication:\n      origin: archive\n      mountPath: /spark/\n",
                        ),
                    ),
                )

            watch_snapshot = _run_watch_then_snapshot(
                workspace_root=workspace_root,
                responses=[(True, _mutate_catalog_origin), (False, None)],
            )
            build_exit_code, build_snapshot = _run_clean_build_snapshot(workspace_root)

        self.assertEqual(build_exit_code, 0)
        self.assertEqual(watch_snapshot, build_snapshot)

    def test_catalog_trust_class_edit_matches_fresh_clean_build(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            _expand_workspace_for_multiple_owned_units(workspace_root)
            catalog_path = workspace_root / "site/catalog.yaml"
            _install_artifact_mount(catalog_path)
            (workspace_root / "generated/api").mkdir(parents=True, exist_ok=True)
            (workspace_root / "generated/api/index.json").write_text("{}\n", encoding="utf-8")

            def _mutate_catalog_trust_class():
                return _rewrite_catalog(
                    catalog_path,
                    replacements=(("trustClass: passive", "trustClass: active"),),
                )

            watch_snapshot = _run_watch_then_snapshot(
                workspace_root=workspace_root,
                responses=[(True, _mutate_catalog_trust_class), (False, None)],
            )
            build_exit_code, build_snapshot = _run_clean_build_snapshot(workspace_root)

        self.assertEqual(build_exit_code, 0)
        self.assertEqual(watch_snapshot, build_snapshot)

    def test_latest_candidate_selection_stays_consistent_across_planning_build_and_watch(
        self,
    ) -> None:
        with _workspace(with_content_file=True, topology="rich_lifecycle") as workspace_root:
            loaded_inputs = load_workspace_inputs(workspace_root)
            planning = evaluate_planning(
                target=PlanningTarget.BUILD,
                catalog=loaded_inputs.catalog,
                provider_snapshot=loaded_inputs.provider_snapshot,
                workspace_root=workspace_root,
                component_documents=loaded_inputs.component_documents,
                stage_root=workspace_root / "site/.stage",
                work_root=workspace_root / ".buildish/work",
            )

            self.assertEqual(
                _selected_context_summary(planning.selected_versions),
                {
                    (RecordKind.DEVELOPMENT, None, None),
                    (RecordKind.LINE_HEAD, None, "4.0"),
                    (RecordKind.LINE_HEAD, None, "4.1"),
                    (RecordKind.RELEASED, "4.0.2", None),
                    (RecordKind.RELEASED, "4.1.0", None),
                    (RecordKind.CANDIDATE, "4.2.0-rc2", None),
                },
            )

            evaluation = run_evaluation(
                request=EvaluationRequest(mode=EvaluationMode.BUILD),
                planning=planning,
            )

            self.assertTrue(evaluation.stage_gate.allowed)
            self.assertIsNotNone(evaluation.build_plan)
            self.assertEqual(
                _selected_context_summary(evaluation.build_plan.selected_versions),
                _selected_context_summary(planning.selected_versions),
            )

            build_exit_code, _build_snapshot = _run_clean_build_snapshot(workspace_root)
            watch_snapshot = _run_watch_then_snapshot(
                workspace_root=workspace_root,
                responses=[(True, None)],
            )
            clean_stage_root = workspace_root / "site/.stage-clean"
            watch_stage_root = workspace_root / "site/.stage"
            clean_route_paths = _route_path_by_target_id(clean_stage_root)
            clean_candidate_versions = _candidate_versions(clean_stage_root)
            clean_snapshot = _stage_snapshot_without_manifest(clean_stage_root)
            watch_route_paths = _route_path_by_target_id(watch_stage_root)
            watch_candidate_versions = _candidate_versions(watch_stage_root)

        self.assertEqual(build_exit_code, 0)
        self.assertEqual(
            clean_route_paths["candidate:spark:runtime:4.2.0-rc2"],
            "/spark/development/candidates/4.2.0-rc2/",
        )
        self.assertNotIn(
            "candidate:spark:runtime:4.2.0-rc1",
            clean_route_paths,
        )
        self.assertEqual(clean_candidate_versions, ["4.2.0-rc2"])
        self.assertEqual(
            watch_route_paths["candidate:spark:runtime:4.2.0-rc2"],
            "/spark/development/candidates/4.2.0-rc2/",
        )
        self.assertNotIn(
            "candidate:spark:runtime:4.2.0-rc1",
            watch_route_paths,
        )
        self.assertEqual(watch_candidate_versions, ["4.2.0-rc2"])
        self.assertEqual(
            watch_snapshot,
            clean_snapshot,
        )

    def test_release_redirect_resolution_stays_consistent_across_check_build_and_watch(
        self,
    ) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            _expand_workspace_for_multiple_owned_units(workspace_root)
            catalog_path = workspace_root / "site/catalog.yaml"
            _rewrite_catalog(
                catalog_path,
                replacements=(
                    (
                        "    publication:\n      mountPath: /spark/\n",
                        "    publication:\n      mountPath: /spark/\n      redirects:\n        - fromPath: /spark/development/docs/\n          target: release:spark/runtime@4.0.0\n          reason: Current docs live on the latest release route.\n",
                    ),
                ),
            )

            check_exit_code, check_report = _run_check_json_report(workspace_root)
            build_exit_code, clean_snapshot = _run_clean_build_snapshot(workspace_root)
            watch_snapshot = _run_watch_then_snapshot(
                workspace_root=workspace_root,
                responses=[(True, None)],
            )
            clean_stage_root = workspace_root / "site/.stage-clean"
            watch_stage_root = workspace_root / "site/.stage"
            clean_redirects = _redirect_entry_by_source(clean_stage_root)
            watch_redirects = _redirect_entry_by_source(watch_stage_root)

        self.assertEqual(check_exit_code, 0)
        self.assertTrue(check_report["summary"]["passed"])
        self.assertFalse(
            any(diagnostic["code"].startswith("redirect-") for diagnostic in check_report["diagnostics"])
        )
        self.assertEqual(build_exit_code, 0)
        self.assertEqual(
            clean_redirects["https://docs.example.org/spark/development/docs/"]["toUrl"],
            "https://docs.example.org/spark/releases/4.0.0/",
        )
        self.assertEqual(
            clean_redirects["https://docs.example.org/spark/development/docs/"]["reason"],
            "Current docs live on the latest release route.",
        )
        self.assertEqual(
            watch_redirects["https://docs.example.org/spark/development/docs/"]["toUrl"],
            "https://docs.example.org/spark/releases/4.0.0/",
        )
        self.assertEqual(
            watch_redirects["https://docs.example.org/spark/development/docs/"]["reason"],
            "Current docs live on the latest release route.",
        )
        self.assertEqual(watch_snapshot, clean_snapshot)


    def test_noisy_watch_event_burst_matches_fresh_clean_build(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            _expand_workspace_for_multiple_owned_units(workspace_root)
            watched_file = workspace_root / "components/runtime/docs/releases/4.0.0/index.md"

            def _mutate_component_page() -> None:
                watched_file.write_text("hello from noisy watch burst\n", encoding="utf-8")

            watch_snapshot = _run_watch_then_snapshot_from_raw_batches(
                workspace_root=workspace_root,
                before_first_batch=_mutate_component_page,
                raw_batches=(
                    {(None, str(watched_file))},
                    {(None, str(watched_file.parent))},
                    {(None, str(watched_file.parent.parent)), (None, str(watched_file))},
                    set(),
                ),
            )
            build_exit_code, build_snapshot = _run_clean_build_snapshot(workspace_root)

        self.assertEqual(build_exit_code, 0)
        self.assertEqual(watch_snapshot, build_snapshot)

    def test_renderer_probe_stays_consistent_during_noisy_watch_burst(self) -> None:
        with _workspace(with_content_file=True) as workspace_root:
            _expand_workspace_for_multiple_owned_units(workspace_root)
            stage_root = workspace_root / "site/.stage"
            watched_file = workspace_root / "components/runtime/docs/releases/4.0.0/index.md"
            release_page = stage_root / "content/spark/releases/4.0.0/index.md"
            failures: list[str] = []
            stop_event = threading.Event()
            raw_batches = (
                {(None, str(watched_file))},
                {(None, str(watched_file.parent))},
                {(None, str(watched_file.parent.parent)), (None, str(watched_file))},
                set(),
            )

            class _MutatingRawEventBatches:
                def __init__(self) -> None:
                    self._batch_index = 0

                def __iter__(self):
                    return self

                def __next__(self):
                    if self._batch_index >= len(raw_batches):
                        raise StopIteration
                    watched_file.write_text(f"renderer burst {self._batch_index}\n", encoding="utf-8")
                    batch = raw_batches[self._batch_index]
                    self._batch_index += 1
                    return batch

            def _manifest_changed(manifest_path, manifest_text: str) -> bool:
                try:
                    return manifest_path.read_text(encoding="utf-8") != manifest_text
                except FileNotFoundError:
                    return True

            def _probe() -> None:
                while not stop_event.is_set():
                    manifest_path = stage_root / "manifest.json"
                    if not manifest_path.exists():
                        continue
                    try:
                        manifest_text = manifest_path.read_text(encoding="utf-8")
                        manifest = json.loads(manifest_text)
                        for relative_path in manifest.get("dataFiles", {}).values():
                            if relative_path is None:
                                continue
                            if not (stage_root / relative_path).is_file():
                                if _manifest_changed(manifest_path, manifest_text):
                                    break
                                failures.append(f"missing data file: {relative_path}")
                                stop_event.set()
                                return
                        if not release_page.is_file():
                            if _manifest_changed(manifest_path, manifest_text):
                                continue
                            failures.append(str(release_page.relative_to(stage_root)))
                            stop_event.set()
                            return
                        release_page.read_text(encoding="utf-8")
                    except FileNotFoundError:
                        continue

            probe_thread = threading.Thread(target=_probe)
            probe_thread.start()
            try:
                with _cwd(workspace_root), unittest.mock.patch(
                    "buildish_site_pipeline.commands.watch_events.watch",
                    return_value=_MutatingRawEventBatches(),
                ):
                    exit_code = _run(argv=["watch"], stdout=io.StringIO(), stderr=io.StringIO())
            finally:
                stop_event.set()
                probe_thread.join(timeout=5)

        self.assertEqual(exit_code, 0)
        self.assertEqual(failures, [])


def _run_watch_then_snapshot(*, workspace_root, responses: list[tuple[bool, object]]) -> dict[str, object]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with _cwd(workspace_root), unittest.mock.patch(
        "buildish_site_pipeline.commands.watch._open_watch_event_stream",
        new=_fake_watch_event_stream_factory(responses=responses),
    ):
        exit_code = _run(argv=["watch"], stdout=stdout, stderr=stderr)

    if exit_code != 0:
        raise AssertionError(f"watch exited {exit_code}: {stderr.getvalue()}")
    return _stage_snapshot_without_manifest(workspace_root / "site/.stage")


def _run_watch_then_snapshot_from_raw_batches(
    *,
    workspace_root,
    before_first_batch,
    raw_batches: tuple[set[tuple[object, str]], ...],
) -> dict[str, object]:
    stdout = io.StringIO()
    stderr = io.StringIO()

    class _MutatingRawEventBatches:
        def __init__(self) -> None:
            self._batch_index = 0

        def __iter__(self):
            return self

        def __next__(self):
            if self._batch_index == 0:
                before_first_batch()
            if self._batch_index >= len(raw_batches):
                raise StopIteration
            batch = raw_batches[self._batch_index]
            self._batch_index += 1
            return batch

    with _cwd(workspace_root), unittest.mock.patch(
        "buildish_site_pipeline.commands.watch_events.watch",
        return_value=_MutatingRawEventBatches(),
    ):
        exit_code = _run(argv=["watch"], stdout=stdout, stderr=stderr)

    if exit_code != 0:
        raise AssertionError(f"watch exited {exit_code}: {stderr.getvalue()}")
    return _stage_snapshot_without_manifest(workspace_root / "site/.stage")


def _run_check_json_report(workspace_root) -> tuple[int, dict[str, object]]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with _cwd(workspace_root):
        exit_code = _run(
            argv=["check", "--report-format", "json", "--report-schema-version", "1"],
            stdout=stdout,
            stderr=stderr,
        )

    if stderr.getvalue() != "":
        raise AssertionError(f"check wrote unexpected stderr: {stderr.getvalue()}")
    return exit_code, json.loads(stdout.getvalue())


def _run_clean_build_snapshot(workspace_root) -> tuple[int, dict[str, object]]:
    clean_stage_root = workspace_root / "site/.stage-clean"
    loaded_inputs = load_workspace_inputs(workspace_root)
    planning = evaluate_planning(
        target=PlanningTarget.BUILD,
        catalog=loaded_inputs.catalog,
        provider_snapshot=loaded_inputs.provider_snapshot,
        workspace_root=workspace_root,
        component_documents=loaded_inputs.component_documents,
        stage_root=clean_stage_root,
        work_root=workspace_root / ".buildish/clean-work",
    )
    evaluation = run_evaluation(
        request=EvaluationRequest(mode=EvaluationMode.BUILD),
        planning=planning,
    )
    if evaluation.build_plan is None:
        return 3, {}
    materialize_stage_tree(
        stage_root=clean_stage_root,
        build_plan=evaluation.build_plan,
        diagnostics=evaluation.diagnostics,
        provider_snapshot=loaded_inputs.provider_snapshot,
    )
    return 0, _stage_snapshot_without_manifest(clean_stage_root)


def _stage_snapshot_without_manifest(stage_root) -> dict[str, object]:
    snapshot = _stage_snapshot(stage_root)
    snapshot.pop("manifest.json", None)
    return snapshot


def _rewrite_catalog(catalog_path, *, replacements: tuple[tuple[str, str], ...]) -> tuple[object, ...]:
    catalog_text = catalog_path.read_text(encoding="utf-8")
    for source_text, target_text in replacements:
        if source_text not in catalog_text:
            raise AssertionError(f"missing expected catalog text: {source_text!r}")
        catalog_text = catalog_text.replace(source_text, target_text, 1)
    catalog_path.write_text(catalog_text, encoding="utf-8")
    return (catalog_path,)


def _install_artifact_mount(catalog_path) -> None:
    _rewrite_catalog(
        catalog_path,
        replacements=(
            (
                "          releases:\n            - version: '4.0.0'\n",
                "          releases:\n            - version: '4.0.0'\n        mounts:\n          - source: generated/api\n            mountPath: /spark/api/\n            kind: generatedApi\n            trustClass: passive\n",
            ),
        ),
    )


def _selected_context_summary(selected_versions) -> set[tuple[RecordKind, str | None, str | None]]:
    contexts = (
        selected_versions.contexts
        if hasattr(selected_versions, "contexts")
        else selected_versions
    )
    return {
        (context.kind, context.version, context.release_line)
        for context in contexts
    }


def _route_path_by_target_id(stage_root) -> dict[str, str]:
    items = json.loads((stage_root / "data/routes.json").read_text(encoding="utf-8"))["items"]
    return {entry["targetId"]: entry["path"] for entry in items}


def _candidate_versions(stage_root) -> list[str]:
    items = json.loads((stage_root / "data/candidates.json").read_text(encoding="utf-8"))["items"]
    return [entry["version"] for entry in items]


def _redirect_entry_by_source(stage_root) -> dict[str, dict[str, object]]:
    items = json.loads((stage_root / "data/redirects.json").read_text(encoding="utf-8"))["items"]
    return {entry["fromUrl"]: entry for entry in items}
