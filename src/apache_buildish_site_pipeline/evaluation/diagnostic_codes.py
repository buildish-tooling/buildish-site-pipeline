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

"""Central diagnostic code registry for the evaluation package."""

INPUT_MISSING = "input-missing"
INPUT_STALE = "input-stale"
INPUT_UNRESOLVED = "input-unresolved"
PUBLICATION_ROUTE_COLLISION = "publication-route-collision"
PUBLICATION_CANONICAL_COLLISION = "publication-canonical-collision"
PUBLICATION_CANONICAL_INVALID = "publication-canonical-invalid"
REDIRECT_TARGET_UNKNOWN = "redirect-target-unknown"
REDIRECT_LOOP = "redirect-loop"
PROVIDER_CONTEXT_AMBIGUOUS = "provider-context-ambiguous"
BUILD_PLAN_UNAVAILABLE = "build-plan-unavailable"
PAGE_READ_FAILED = "page-read-failed"
PAGE_FRONT_MATTER_INVALID = "page-front-matter-invalid"
PAGE_RESERVED_NAMESPACE = "page-reserved-namespace"
PAGE_PATH_OUTSIDE_ROOT = "page-path-outside-root"
LOCALIZATION_POLICY_INVALID = "localization-policy-invalid"
TRANSLATION_LOCALE_UNRESOLVED = "translation-locale-unresolved"
TRANSLATION_LOCALE_DUPLICATE = "translation-locale-duplicate"
TRANSLATION_LINKAGE_CONFLICT = "translation-linkage-conflict"
TRANSLATION_ROUTE_INCONSISTENT = "translation-route-inconsistent"
OPERATIONAL_LIMIT_EXCEEDED = "operational-limit-exceeded"
REFERENCE_CONFIGURATION_INVALID = "reference-configuration-invalid"
COMPATIBILITY_REFERENCE_UNKNOWN = "compatibility-reference-unknown"