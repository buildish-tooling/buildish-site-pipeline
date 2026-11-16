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

"""Component provider binding, composition, and explicit profile coverage."""

import io
import json
import unittest
from unittest import mock

import yaml

from buildish_site_pipeline.cli import _run
from buildish_site_pipeline.cli.errors import InputDiagnosticError
from buildish_site_pipeline.commands.shared import load_workspace_inputs
from buildish_site_pipeline.models.enums import ExecutionProfile, MaterializationStatus
from tests.support.workspace import _workspace, _cwd


def configure_snapshot(
    root, requirement="publication", path="docs/releases/provider-snapshot.json"
):
    catalog_path = root / "site/catalog.yaml"
    catalog = yaml.safe_load(catalog_path.read_text())
    catalog["components"][0]["providerSnapshot"] = {
        "source": "runtime",
        "path": path,
        "requirement": requirement,
    }
    catalog_path.write_text(yaml.safe_dump(catalog, sort_keys=False))
    aggregate_path = root / "site/provider-snapshot.json"
    aggregate = json.loads(aggregate_path.read_text())
    record = aggregate["records"].pop()
    aggregate_path.write_text(json.dumps(aggregate))
    return root / "components/runtime" / path, {
        "schemaVersion": 1,
        "providers": aggregate["providers"],
        "records": [record],
    }


class ComponentSnapshotTests(unittest.TestCase):
    def test_present_inventory_composes_and_preserves_timestamp_provenance(self):
        with _workspace() as root:
            path, snapshot = configure_snapshot(root)
            snapshot["providers"][0]["fetchedAt"] = "2026-11-16T00:00:00Z"
            path.write_text(json.dumps(snapshot))
            loaded = load_workspace_inputs(root)
            self.assertEqual(len(loaded.provider_snapshot.records), 3)
            self.assertEqual(
                loaded.snapshot_inputs[0].status, MaterializationStatus.PRESENT
            )
            self.assertEqual(
                loaded.provider_snapshot.providers[0].fetched_at,
                loaded.snapshot_inputs[0].fetched_at["github"],
            )
            self.assertIn(path, loaded.provider_snapshot_paths)
            self.assertNotEqual(
                loaded.snapshot_inputs[-1].fetched_at["github"],
                loaded.snapshot_inputs[0].fetched_at["github"],
            )

    def test_requirement_matrix_and_missing_path_retained(self):
        for requirement in ("publication", "required", "optional"):
            for profile in ExecutionProfile:
                with (
                    self.subTest(requirement=requirement, profile=profile),
                    _workspace() as root,
                ):
                    path, _ = configure_snapshot(
                        root, requirement, "absent/checkout/provider.json"
                    )
                    loaded = load_workspace_inputs(root, profile=profile)
                    entry = loaded.snapshot_inputs[0]
                    self.assertEqual(entry.status, MaterializationStatus.MISSING)
                    self.assertEqual(
                        entry.required,
                        requirement == "required"
                        or (
                            requirement == "publication"
                            and profile == ExecutionProfile.PUBLICATION
                        ),
                    )
                    self.assertIn(path, loaded.provider_snapshot_paths)

    def test_invalid_present_snapshot_and_owner_fail(self):
        for mutation in (
            "syntax",
            "owner",
            "artifact",
            "source",
            "descriptor",
            "directory",
        ):
            with self.subTest(mutation=mutation), _workspace() as root:
                path, snapshot = configure_snapshot(root)
                if mutation == "owner":
                    snapshot["records"][0]["componentSlug"] = "someone-else"
                if mutation == "artifact":
                    snapshot["records"][0]["artifactKey"] = "unknown"
                if mutation == "source":
                    snapshot["records"][0]["sourceKey"] = "unknown"
                if mutation == "descriptor":
                    snapshot["providers"][0]["type"] = "different"
                if mutation == "directory":
                    path.mkdir()
                else:
                    path.write_text(
                        "{" if mutation == "syntax" else json.dumps(snapshot)
                    )
                with self.assertRaises(InputDiagnosticError):
                    load_workspace_inputs(root)

    def test_duplicate_external_identity_reports_both_files(self):
        with _workspace() as root:
            path, snapshot = configure_snapshot(root)
            snapshot["records"][0]["externalId"] = "same"
            aggregate_path = root / "site/provider-snapshot.json"
            aggregate = json.loads(aggregate_path.read_text())
            aggregate["records"][0]["externalId"] = "same"
            aggregate_path.write_text(json.dumps(aggregate))
            path.write_text(json.dumps(snapshot))
            with self.assertRaisesRegex(
                InputDiagnosticError, "Duplicate provider record"
            ) as caught:
                load_workspace_inputs(root)
            self.assertIn("site/provider-snapshot.json", str(caught.exception))
            self.assertIn("docs/releases/provider-snapshot.json", str(caught.exception))

    def test_path_escape_rejected_including_symlink(self):
        with _workspace() as root:
            path, snapshot = configure_snapshot(root, path="escape/provider.json")
            path.parent.symlink_to(root / "site", target_is_directory=True)
            with self.assertRaises(InputDiagnosticError):
                load_workspace_inputs(root)

    def test_cli_profiles_are_explicit_and_reported(self):
        for command in ("plan", "check", "build"):
            with (
                self.subTest(command=command),
                _workspace(with_content_file=True) as root,
            ):
                output, errors = io.StringIO(), io.StringIO()
                with _cwd(root):
                    code = _run(
                        argv=[
                            command,
                            "--profile",
                            "publication",
                            "--report-format",
                            "json",
                            "--report-schema-version",
                            "1",
                        ],
                        stdout=output,
                        stderr=errors,
                    )
                self.assertEqual(code, 0, errors.getvalue())
                self.assertEqual(
                    json.loads(output.getvalue())["profile"], "publication"
                )

    def test_combined_budget_counts_aggregate_raw_bytes(self):
        with _workspace() as root:
            path, snapshot = configure_snapshot(root)
            path.write_text(json.dumps(snapshot))
            aggregate = root / "site/provider-snapshot.json"
            raw = aggregate.read_bytes()
            ceiling = len(raw) + 50
            aggregate.write_bytes(raw + b" " * (ceiling - len(raw)))
            with mock.patch(
                "buildish_site_pipeline.commands.shared.DEFAULT_PROVIDER_SNAPSHOT_BYTES",
                ceiling,
            ):
                with self.assertRaisesRegex(
                    InputDiagnosticError, "Combined provider inputs"
                ):
                    load_workspace_inputs(root)

    def test_failed_watch_report_preserves_publication_profile(self):
        from buildish_site_pipeline.cli.main import parse_invocation
        from buildish_site_pipeline.commands.watch import _run_watch_cycle

        with _workspace() as root:
            (root / "site/provider-snapshot.json").write_text("{")
            with _cwd(root):
                invocation = parse_invocation(["watch", "--profile", "publication"])
            outcome = _run_watch_cycle(
                invocation=invocation,
                cycle_number=0,
                trusted_stage=None,
                prior_watch_roots=(),
                dirty_paths=(),
            )
            self.assertEqual(outcome.report.profile, ExecutionProfile.PUBLICATION)

    def test_composition_uses_bytes_already_read_when_aggregate_disappears(self):
        from buildish_site_pipeline.commands import shared

        with _workspace() as root:
            path, snapshot = configure_snapshot(root)
            path.write_text(json.dumps(snapshot))
            original = shared._load_component_documents  # noqa: SLF001 - exercise a removal between input reads

            def remove_aggregate(*args, **kwargs):
                result = original(*args, **kwargs)
                (root / "site/provider-snapshot.json").unlink()
                return result

            with mock.patch.object(
                shared, "_load_component_documents", side_effect=remove_aggregate
            ):
                loaded = load_workspace_inputs(root)
            self.assertEqual(len(loaded.provider_snapshot.records), 3)

    def test_snapshot_only_source_is_exported_for_consumer_mounts(self):
        from buildish_site_pipeline.source_roots import resolve_component_source_roots

        with _workspace() as root:
            configure_snapshot(root)
            catalog_path = root / "site/catalog.yaml"
            catalog = yaml.safe_load(catalog_path.read_text())
            catalog["sources"]["inventory"] = {"localDir": "release-inventory"}
            catalog["components"][0]["providerSnapshot"]["source"] = "inventory"
            catalog_path.write_text(yaml.safe_dump(catalog, sort_keys=False))
            loaded = load_workspace_inputs(root)
            sources = resolve_component_source_roots(
                catalog=loaded.catalog, workspace_root=root
            )
            self.assertIn(
                root / "release-inventory", [item.local_dir for item in sources]
            )

    def test_real_watch_entrypoint_keeps_publication_requirements(self):
        with _workspace(with_content_file=True) as root:
            configure_snapshot(root)
            output, errors = io.StringIO(), io.StringIO()
            report_path = root / "site/watch-report.json"
            with mock.patch(
                "buildish_site_pipeline.commands.watch._open_watch_event_stream",
                side_effect=RuntimeError("Watcher must not start"),
            ) as watcher:
                with _cwd(root):
                    code = _run(
                        argv=[
                            "watch",
                            "--profile",
                            "publication",
                            "--report-format",
                            "json",
                            "--report-schema-version",
                            "1",
                            "--report-output",
                            str(report_path),
                        ],
                        stdout=output,
                        stderr=errors,
                    )
            watcher.assert_not_called()
            self.assertEqual(code, 3)
            report = json.loads(report_path.read_text())
            self.assertEqual(report["profile"], "publication")
            self.assertIn(
                "provider-snapshot-required",
                [item["code"] for item in report["diagnostics"]],
            )

    def test_typed_snapshot_paths_follow_public_diagnostic_redaction_rules(self):
        from buildish_site_pipeline.models.emitted.execution import SnapshotInput
        from buildish_site_pipeline.models.enums import SnapshotRequirement
        from buildish_site_pipeline.staging.public_safety import (
            sanitize_snapshot_inputs,
        )

        with _workspace() as root:
            item = SnapshotInput(
                expected_local_path=str(root / "private/input.json"),
                requirement=SnapshotRequirement.OPTIONAL,
                required=False,
                status=MaterializationStatus.PRESENT,
            )
            sanitized = sanitize_snapshot_inputs(
                (item,), workspace_root=root, private_roots=(root / "private",)
            )
            self.assertEqual(sanitized[0].expected_local_path, "[redacted-local-path]")
            self.assertEqual(
                SnapshotInput.model_validate_json(sanitized[0].model_dump_json()),
                sanitized[0],
            )

    def test_multiple_component_snapshots_share_provider_descriptors(self):
        import copy

        with _workspace() as root:
            path, snapshot = configure_snapshot(root)
            path.write_text(json.dumps(snapshot))
            catalog_path = root / "site/catalog.yaml"
            catalog = yaml.safe_load(catalog_path.read_text())
            second = copy.deepcopy(catalog["components"][0])
            second["slug"] = "other"
            second["publication"]["mountPath"] = "/other/"
            second["providerSnapshot"]["path"] = "other-provider.json"
            catalog["components"].append(second)
            catalog_path.write_text(yaml.safe_dump(catalog, sort_keys=False))
            other = copy.deepcopy(snapshot)
            other["providers"][0]["fetchedAt"] = "2026-11-16T00:00:00Z"
            other["records"][0]["componentSlug"] = "other"
            (root / "components/runtime/other-provider.json").write_text(
                json.dumps(other)
            )
            loaded = load_workspace_inputs(root)
            self.assertEqual(len(loaded.provider_snapshot.records), 4)
            self.assertEqual(len(loaded.provider_snapshot.providers), 1)
            self.assertEqual(len(loaded.snapshot_inputs), 3)
            self.assertEqual(
                {item.component_slug for item in loaded.snapshot_inputs},
                {"spark", "other", None},
            )

    def test_yaml_component_inventory_uses_same_loader_contract(self):
        for suffix in ("yaml", "yml"):
            with self.subTest(suffix=suffix), _workspace() as root:
                path, snapshot = configure_snapshot(root, path=f"provider.{suffix}")
                path.write_text(yaml.safe_dump(snapshot))
                loaded = load_workspace_inputs(root)
                self.assertEqual(len(loaded.provider_snapshot.records), 3)
