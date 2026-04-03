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

"""Typed external models for the site pipeline."""

from .base import SitePipelineBaseModel
from .enums import (
    CheckFailureThreshold,
    DiagnosticSeverity,
    DocumentFormat,
    MaterializationInputKind,
    MaterializationStatus,
    PlanningTarget,
    RunStatus,
    StageCommand,
)
from .loading import (
    DocumentDecodingError,
    DocumentRootTypeError,
    DocumentSyntaxError,
    DocumentValidationFailure,
    DuplicateKeyError,
    LoadingError,
    MissingSchemaVersionError,
    UnsupportedSchemaVersionError,
    load_check_report,
    load_json_mapping,
    load_resolved_materialization_report,
    load_stage_manifest,
    load_stage_run_report,
    load_versioned_document,
    load_yaml_mapping,
)
from .planning_stage_contract import (
    CheckReportV1,
    CheckSummary,
    PipelineDiagnosticEntry,
    ReducedDiagnosticDetailsSummary,
    ResolvedMaterializationEntry,
    ResolvedMaterializationReportV1,
    StageDataFiles,
    StageManifestV1,
    StageRoots,
    StageRunReportV1,
    StageRunSummary,
)
from .scalars import ExtensionsObject, LocalPathString, SchemaVersion, StageRelativePath, TimestampString

__all__ = [
    "CheckFailureThreshold",
    "CheckReportV1",
    "CheckSummary",
    "DiagnosticSeverity",
    "DocumentDecodingError",
    "DocumentFormat",
    "DocumentRootTypeError",
    "DocumentSyntaxError",
    "DocumentValidationFailure",
    "DuplicateKeyError",
    "ExtensionsObject",
    "LocalPathString",
    "LoadingError",
    "MaterializationInputKind",
    "MaterializationStatus",
    "MissingSchemaVersionError",
    "PipelineDiagnosticEntry",
    "PlanningTarget",
    "ReducedDiagnosticDetailsSummary",
    "ResolvedMaterializationEntry",
    "ResolvedMaterializationReportV1",
    "RunStatus",
    "SchemaVersion",
    "SitePipelineBaseModel",
    "StageCommand",
    "StageDataFiles",
    "StageManifestV1",
    "StageRelativePath",
    "StageRoots",
    "StageRunReportV1",
    "StageRunSummary",
    "TimestampString",
    "UnsupportedSchemaVersionError",
    "load_check_report",
    "load_json_mapping",
    "load_resolved_materialization_report",
    "load_stage_manifest",
    "load_stage_run_report",
    "load_versioned_document",
    "load_yaml_mapping",
]