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

"""Shared workspace loading helpers for CLI commands."""

from __future__ import annotations

from dataclasses import dataclass
import stat
from itertools import chain
from pathlib import Path

from buildish_site_pipeline.models import ProviderSnapshotDocumentV1
from buildish_site_pipeline.models.provider.provider_snapshot import (
    SnapshotArtifact,
    ProviderRecord,
)
from buildish_site_pipeline.models.authored.site_catalog import SiteCatalogDocumentV1
from buildish_site_pipeline.models.authored.component_metadata import (
    ComponentMetadataDocumentV1,
)
from buildish_site_pipeline.models.enums import (
    DocumentFormat,
    ExecutionProfile,
    SnapshotRequirement,
    MaterializationStatus,
)
from buildish_site_pipeline.models.emitted.execution import SnapshotInput
from buildish_site_pipeline.models.loading import (
    DocumentDecodingError,
    DocumentRootTypeError,
    DocumentSyntaxError,
    DocumentValidationFailure,
    DuplicateKeyError,
    LoadingError,
    MissingSchemaVersionError,
    UnsupportedSchemaVersionError,
    load_component_metadata_document,
    load_provider_snapshot_document,
    load_site_catalog_document,
)
from buildish_site_pipeline.resource_limits import DEFAULT_PROVIDER_SNAPSHOT_BYTES
from buildish_site_pipeline.source_roots import (
    resolve_repo_path,
    resolve_catalog_source_bindings,
    resolve_component_content_source_binding,
)

from ..cli.errors import CliDiagnosticIssue, InputDiagnosticError

_DEFAULT_CATALOG_PATH = Path("site/catalog.yaml")
_PROVIDER_SNAPSHOT_CANDIDATE_NAMES = (
    "provider-snapshot.yaml",
    "provider-snapshot.yml",
    "provider-snapshot.json",
)
_MAX_VALIDATION_ISSUES = 20
_MAX_ISSUE_MESSAGE_CHARACTERS = 400
_MAX_ISSUE_LOCATION_CHARACTERS = 200


@dataclass(frozen=True, slots=True)
class LoadedCatalogInput:
    """Catalog document plus its resolved path."""

    catalog: SiteCatalogDocumentV1
    catalog_path: Path


@dataclass(frozen=True, slots=True)
class LoadedWorkspaceInputs:
    """Fully loaded repository inputs for planning/evaluation."""

    catalog: SiteCatalogDocumentV1
    provider_snapshot: ProviderSnapshotDocumentV1
    component_documents: dict[str, ComponentMetadataDocumentV1]
    catalog_path: Path
    provider_snapshot_path: Path | None
    snapshot_inputs: tuple[SnapshotInput, ...] = ()
    provider_snapshot_paths: tuple[Path, ...] = ()


def load_catalog_input(
    workspace_root: Path, catalog_path: Path | None = None
) -> LoadedCatalogInput:
    """Load the authored catalog document for one workspace."""

    resolved_workspace_root = workspace_root.resolve(strict=False)
    resolved_catalog_path = (
        catalog_path.resolve(strict=False)
        if catalog_path is not None
        else (resolved_workspace_root / _DEFAULT_CATALOG_PATH).resolve(strict=False)
    )
    if not resolved_catalog_path.exists():
        raise InputDiagnosticError(
            "Catalog document does not exist",
            code="input-not-found",
            source=_display_input_path(resolved_catalog_path, resolved_workspace_root),
        )
    source_name = _display_input_path(
        resolved_catalog_path, resolved_workspace_root
    )
    try:
        catalog = load_site_catalog_document(
            _read_document_bytes(resolved_catalog_path, source_name=source_name),
            document_format=_infer_document_format(resolved_catalog_path),
            source_name=source_name,
        )
    except LoadingError as exc:
        raise _input_error_from_loading(exc) from exc
    return LoadedCatalogInput(catalog=catalog, catalog_path=resolved_catalog_path)


def load_workspace_inputs(
    workspace_root: Path,
    catalog_path: Path | None = None,
    *,
    profile: ExecutionProfile = ExecutionProfile.LOCAL,
) -> LoadedWorkspaceInputs:
    """Load default catalog, provider snapshot, and component metadata inputs."""

    resolved_workspace_root = workspace_root.resolve(strict=False)
    loaded_catalog = load_catalog_input(
        resolved_workspace_root,
        catalog_path,
    )
    site_root = loaded_catalog.catalog_path.parent

    try:
        provider_snapshot, provider_snapshot_path, aggregate_bytes = (
            _load_provider_snapshot(site_root, resolved_workspace_root)
        )
        component_documents = _load_component_documents(
            resolved_workspace_root, loaded_catalog.catalog
        )
        provider_snapshot, snapshot_inputs, snapshot_paths = _load_component_snapshots(
            catalog=loaded_catalog.catalog,
            workspace_root=resolved_workspace_root,
            aggregate=provider_snapshot,
            aggregate_path=provider_snapshot_path,
            aggregate_bytes=aggregate_bytes,
            profile=profile,
            component_documents=component_documents,
        )
    except LoadingError as exc:
        raise _input_error_from_loading(exc) from exc
    except ValueError as exc:
        raise InputDiagnosticError(
            str(exc),
            code="input-configuration-invalid",
            source=_display_input_path(
                loaded_catalog.catalog_path, resolved_workspace_root
            ),
        ) from exc
    return LoadedWorkspaceInputs(
        catalog=loaded_catalog.catalog,
        provider_snapshot=provider_snapshot,
        component_documents=component_documents,
        catalog_path=loaded_catalog.catalog_path,
        provider_snapshot_path=provider_snapshot_path,
        snapshot_inputs=snapshot_inputs,
        provider_snapshot_paths=snapshot_paths,
    )


def _load_provider_snapshot(
    site_root: Path, workspace_root: Path
) -> tuple[ProviderSnapshotDocumentV1, Path | None, int]:
    found_paths = [
        (site_root / candidate_name).resolve(strict=False)
        for candidate_name in _PROVIDER_SNAPSHOT_CANDIDATE_NAMES
        if (site_root / candidate_name).exists()
    ]
    if len(found_paths) > 1:
        raise InputDiagnosticError(
            "Found multiple default provider snapshot files; keep only one of "
            f"{', '.join(path.name for path in found_paths)}",
            code="input-ambiguous",
            source=_display_input_path(site_root, workspace_root),
        )
    if not found_paths:
        return (
            ProviderSnapshotDocumentV1(schema_version=1, providers=[], records=[]),
            None,
            0,
        )
    provider_snapshot_path = found_paths[0]
    source_name = _display_input_path(provider_snapshot_path, workspace_root)
    raw = _read_document_bytes(
        provider_snapshot_path,
        source_name=source_name,
        max_bytes=DEFAULT_PROVIDER_SNAPSHOT_BYTES,
    )
    return (
        load_provider_snapshot_document(
            raw,
            document_format=_infer_document_format(provider_snapshot_path),
            source_name=source_name,
        ),
        provider_snapshot_path,
        len(raw),
    )


def _load_component_documents(
    repo_root: Path,
    catalog: SiteCatalogDocumentV1,
) -> dict[str, ComponentMetadataDocumentV1]:
    component_documents: dict[str, ComponentMetadataDocumentV1] = {}
    default_metadata_file = (
        catalog.defaults.metadata_file if catalog.defaults is not None else None
    )
    source_bindings = resolve_catalog_source_bindings(
        catalog=catalog, workspace_root=repo_root
    )
    for component in catalog.components:
        content_source = resolve_component_content_source_binding(
            component=component,
            source_bindings=source_bindings,
            workspace_root=repo_root,
            default_metadata_file=default_metadata_file,
        )
        if content_source is None:
            continue
        repository_root = content_source.local_dir
        metadata_path = content_source.metadata_file
        if metadata_path is None:
            continue
        if not metadata_path.is_relative_to(repository_root):
            raise InputDiagnosticError(
                "Component metadata path escapes its repository root",
                code="input-path-invalid",
                source=_display_input_path(metadata_path, repo_root),
            )
        if not metadata_path.exists():
            continue
        source_name = _display_input_path(metadata_path, repo_root)
        component_documents[component.slug] = load_component_metadata_document(
            _read_document_bytes(metadata_path, source_name=source_name),
            document_format=_infer_document_format(metadata_path),
            source_name=source_name,
        )
    return component_documents


def _infer_document_format(path: Path) -> DocumentFormat:
    suffix = path.suffix.lower()
    if suffix == ".json":
        return DocumentFormat.JSON
    if suffix in {".yaml", ".yml"}:
        return DocumentFormat.YAML
    raise InputDiagnosticError(
        "Input document must use a .json, .yaml, or .yml suffix",
        code="input-format-unsupported",
        source=path.name,
    )


def _read_document_bytes(
    path: Path,
    *,
    source_name: str,
    max_bytes: int | None = None,
) -> bytes:
    """Read one input, optionally stopping after enough bytes to prove overflow."""

    try:
        with path.open("rb") as input_file:
            document = input_file.read() if max_bytes is None else input_file.read(max_bytes + 1)
    except OSError as exc:
        message = (
            "Input document is not a regular readable file"
            if isinstance(exc, IsADirectoryError)
            else "Could not read input document"
        )
        code = "input-not-file" if isinstance(exc, IsADirectoryError) else "input-read-failed"
        raise InputDiagnosticError(
            message,
            code=code,
            source=source_name,
        ) from exc

    if max_bytes is not None and len(document) > max_bytes:
        raise InputDiagnosticError(
            f"Provider snapshot exceeds the {max_bytes}-byte raw input limit",
            code="input-size-limit-exceeded",
            source=source_name,
            issues=(
                CliDiagnosticIssue(
                    location="$",
                    code="size-limit-exceeded",
                    message=f"read at least {len(document)} bytes; limit is {max_bytes} bytes",
                    actual_bytes=len(document),
                    limit_bytes=max_bytes,
                ),
            ),
        )
    return document


def _input_error_from_loading(exc: LoadingError) -> InputDiagnosticError:
    """Map loader exceptions into the stable CLI input taxonomy."""

    source_name = exc.source_name
    if isinstance(exc, DocumentValidationFailure):
        issues, omitted_issue_count = _validation_issues(exc)
        return InputDiagnosticError(
            "Document does not satisfy its schema",
            code="input-validation-failed",
            source=source_name,
            issues=issues,
            omitted_issue_count=omitted_issue_count,
        )
    if isinstance(exc, DocumentDecodingError):
        return InputDiagnosticError(
            "Document is not valid UTF-8",
            code="input-encoding-invalid",
            source=source_name,
        )
    if isinstance(exc, DuplicateKeyError):
        code = "input-duplicate-key"
        message = "Document contains a duplicate mapping key"
    elif isinstance(exc, DocumentSyntaxError):
        code = "input-syntax-invalid"
        message = "Document syntax is invalid"
    elif isinstance(exc, DocumentRootTypeError):
        code = "input-root-type-invalid"
        message = "Document root must be a mapping/object"
    elif isinstance(exc, MissingSchemaVersionError):
        code = "input-schema-version-missing"
        message = "Document is missing the required schemaVersion"
    elif isinstance(exc, UnsupportedSchemaVersionError):
        code = "input-schema-version-unsupported"
        message = "Document uses an unsupported schemaVersion"
    else:
        code = "input-invalid"
        message = str(exc)
    return InputDiagnosticError(message, code=code, source=source_name)


def _validation_issues(
    exc: DocumentValidationFailure,
) -> tuple[tuple[CliDiagnosticIssue, ...], int]:
    raw_issues = exc.validation_error.errors(
        include_url=False,
        include_context=False,
        include_input=False,
    )
    visible_issues = raw_issues[:_MAX_VALIDATION_ISSUES]
    issues = tuple(
        CliDiagnosticIssue(
            location=_format_validation_location(issue.get("loc", ())),
            code=_stable_validation_issue_code(str(issue.get("type", "value_error"))),
            message=_bounded_issue_message(str(issue.get("msg", "Invalid value"))),
        )
        for issue in visible_issues
    )
    return issues, len(raw_issues) - len(visible_issues)


def _format_validation_location(location: object) -> str:
    if not isinstance(location, tuple) or not location:
        return "$"
    rendered = ""
    for segment in location:
        if isinstance(segment, int):
            rendered += f"[{segment}]"
        else:
            rendered += ("." if rendered else "") + str(segment)
    if len(rendered) <= _MAX_ISSUE_LOCATION_CHARACTERS:
        return rendered
    return f"{rendered[: _MAX_ISSUE_LOCATION_CHARACTERS - 1]}…"


def _stable_validation_issue_code(pydantic_code: str) -> str:
    if pydantic_code == "missing":
        return "required"
    if pydantic_code == "extra_forbidden":
        return "unknown-field"
    if pydantic_code.endswith("_type"):
        return "type-invalid"
    return "value-invalid"


def _bounded_issue_message(message: str) -> str:
    if len(message) <= _MAX_ISSUE_MESSAGE_CHARACTERS:
        return message
    return f"{message[: _MAX_ISSUE_MESSAGE_CHARACTERS - 1]}…"


def _display_input_path(path: Path, workspace_root: Path) -> str:
    resolved_path = path.resolve(strict=False)
    resolved_workspace_root = workspace_root.resolve(strict=False)
    if resolved_path == resolved_workspace_root:
        return "."
    if resolved_path.is_relative_to(resolved_workspace_root):
        return resolved_path.relative_to(resolved_workspace_root).as_posix()
    return f"<external-input>/{resolved_path.name or 'input'}"


def _load_component_snapshots(
    *,
    catalog: SiteCatalogDocumentV1,
    workspace_root: Path,
    aggregate: ProviderSnapshotDocumentV1,
    aggregate_path: Path | None,
    profile: ExecutionProfile,
    aggregate_bytes: int,
    component_documents: dict[str, ComponentMetadataDocumentV1],
) -> tuple[ProviderSnapshotDocumentV1, tuple[SnapshotInput, ...], tuple[Path, ...]]:
    """Compose validated component inventory files with aggregate inventory."""
    sources = resolve_catalog_source_bindings(
        catalog=catalog, workspace_root=workspace_root
    )
    providers = {item.key: item for item in aggregate.providers}
    records = list(aggregate.records)
    snapshot_artifacts = list(aggregate.artifacts)
    aggregate_name = str(aggregate_path) if aggregate_path else "aggregate inventory"
    origins = {
        (item.provider, item.external_id): aggregate_name
        for item in records
        if item.external_id is not None
    }
    descriptor_origins = {item.key: aggregate_name for item in aggregate.providers}
    paths = [aggregate_path] if aggregate_path is not None else []
    inputs = []
    consumed_bytes = aggregate_bytes
    for component in catalog.components:
        binding = component.provider_snapshot
        if binding is None:
            continue
        path = resolve_repo_path(sources[binding.source].local_dir, binding.path)
        claims = [
            item
            for item in chain[SnapshotArtifact | ProviderRecord](
                aggregate.artifacts, aggregate.records
            )
            if item.component_slug == component.slug
        ]
        if claims:
            raise InputDiagnosticError(
                f"Component {component.slug!r} version facts are owned by {path}; aggregate input {aggregate_name} must not claim this component",
                code="input-configuration-invalid",
                source=aggregate_name,
            )
        paths.append(path)
        required = binding.requirement is SnapshotRequirement.REQUIRED or (
            binding.requirement is SnapshotRequirement.PUBLICATION
            and profile is ExecutionProfile.PUBLICATION
        )
        source_name = _display_input_path(path, workspace_root)
        try:
            mode = path.stat().st_mode
        except FileNotFoundError:
            inputs.append(
                SnapshotInput(
                    component_slug=component.slug,
                    source_key=binding.source,
                    expected_local_path=str(path),
                    requirement=binding.requirement,
                    required=required,
                    status=MaterializationStatus.MISSING,
                )
            )
            continue
        except OSError as exc:
            raise InputDiagnosticError(
                "Could not inspect component snapshot",
                code="input-read-failed",
                source=source_name,
            ) from exc
        if not stat.S_ISREG(mode):
            raise InputDiagnosticError(
                "Component snapshot must be a regular file",
                code="input-not-file",
                source=source_name,
            )
        raw = _read_document_bytes(
            path, source_name=source_name, max_bytes=DEFAULT_PROVIDER_SNAPSHOT_BYTES
        )
        consumed_bytes += len(raw)
        if consumed_bytes > DEFAULT_PROVIDER_SNAPSHOT_BYTES:
            raise InputDiagnosticError(
                "Combined provider inputs exceed the 16 MiB ceiling",
                code="input-too-large",
                source=source_name,
            )
        document = load_provider_snapshot_document(
            raw, document_format=_infer_document_format(path), source_name=source_name
        )
        metadata = component_documents.get(component.slug)
        artifacts = (
            {item.key: item for item in metadata.artifacts or ()} if metadata else {}
        )
        bindings = {item.key: item for item in component.artifacts or ()}
        content = resolve_component_content_source_binding(
            component=component,
            source_bindings=sources,
            workspace_root=workspace_root,
            default_metadata_file=catalog.defaults.metadata_file
            if catalog.defaults
            else None,
        )
        for record in chain[SnapshotArtifact | ProviderRecord](
            document.artifacts, document.records
        ):
            if (
                record.component_slug != component.slug
                or record.artifact_key not in artifacts
            ):
                raise InputDiagnosticError(
                    f"Snapshot owned by {component.slug!r} references invalid artifact {record.component_slug}:{record.artifact_key}",
                    code="input-configuration-invalid",
                    source=source_name,
                )
        for record in document.records:
            artifact_binding = bindings.get(record.artifact_key)
            expected_source = (
                artifact_binding.source
                if artifact_binding and artifact_binding.source
                else content.key
                if content
                else None
            )
            if record.source_key is not None and record.source_key != expected_source:
                raise InputDiagnosticError(
                    f"Record sourceKey {record.source_key!r} does not match artifact source",
                    code="input-configuration-invalid",
                    source=source_name,
                )
            if record.external_id is not None:
                identity = (record.provider, record.external_id)
                if identity in origins:
                    raise InputDiagnosticError(
                        f"Duplicate provider record {identity!r} in {origins[identity]} and {source_name}",
                        code="input-configuration-invalid",
                        source=source_name,
                    )
                origins[identity] = source_name
        for descriptor in document.providers:
            previous = providers.get(descriptor.key)
            if previous is not None:
                if previous.model_dump(exclude={"fetched_at"}) != descriptor.model_dump(
                    exclude={"fetched_at"}
                ):
                    raise InputDiagnosticError(
                        f"Conflicting provider {descriptor.key!r} in {descriptor_origins[descriptor.key]} and {source_name}",
                        code="input-configuration-invalid",
                        source=source_name,
                    )
                if previous.fetched_at >= descriptor.fetched_at:
                    continue
            providers[descriptor.key] = descriptor
            descriptor_origins[descriptor.key] = source_name
        records.extend(document.records)
        snapshot_artifacts.extend(document.artifacts)
        if len(records) > 50_000:
            raise InputDiagnosticError(
                "Combined provider inputs exceed the 50,000 record ceiling",
                code="input-too-large",
                source=source_name,
            )
        inputs.append(
            SnapshotInput(
                component_slug=component.slug,
                source_key=binding.source,
                expected_local_path=str(path),
                requirement=binding.requirement,
                required=required,
                status=MaterializationStatus.PRESENT,
                fetched_at={item.key: item.fetched_at for item in document.providers},
            )
        )
    if aggregate_path is not None:
        inputs.append(
            SnapshotInput(
                expected_local_path=str(aggregate_path),
                requirement=SnapshotRequirement.OPTIONAL,
                required=False,
                status=MaterializationStatus.PRESENT,
                fetched_at={item.key: item.fetched_at for item in aggregate.providers},
            )
        )
    return (
        ProviderSnapshotDocumentV1(
            schema_version=1,
            providers=list(providers.values()),
            records=records,
            artifacts=snapshot_artifacts,
        ),
        tuple(inputs),
        tuple(paths),
    )
