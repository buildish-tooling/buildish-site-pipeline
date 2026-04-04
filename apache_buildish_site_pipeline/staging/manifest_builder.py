# Copyright 2026 The Apache Software Foundation

"""Manifest-last assembly entry point for finalized stage data."""

from __future__ import annotations

from typing import Any

from apache_buildish_site_pipeline.models.planning_stage_contract import StageCommand, StageManifestV1
from apache_buildish_site_pipeline.models.provider_snapshot import ProviderSnapshotV1

from .aggregates import finalize_pages_and_write_aggregates
from .types import EffectiveBuildPlan, WorkRootLayout
from .worker_protocol import WorkerResultWire


def build_stage_manifest(
    *,
    layout: WorkRootLayout,
    command: StageCommand,
    build_plan: EffectiveBuildPlan,
    diagnostics: tuple[Any, ...],
    provider_snapshot: ProviderSnapshotV1,
    worker_results: tuple[WorkerResultWire, ...],
) -> StageManifestV1:
    """Write all aggregate data files and emit the stage manifest last."""

    return finalize_pages_and_write_aggregates(
        layout=layout,
        command=command,
        build_plan=build_plan,
        diagnostics=diagnostics,
        provider_snapshot=provider_snapshot,
        worker_results=worker_results,
    )