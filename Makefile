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

UV_RUN = uv run --frozen
SNAPSHOT_OUT_DIR ?= dist/snapshots
CONTAINER_IMAGE ?= localhost/buildish-site-pipeline:local
CONTAINER_IMAGE_PLATFORMS ?= linux/amd64,linux/arm64
LOCAL_REGISTRY_TEST_PLATFORMS ?= linux/amd64,linux/arm64
LOCAL_REGISTRY_TEST_TAG ?= integration-test
LOCAL_REGISTRY_TEST_ARGS ?=
HELP_TARGETS = $(MAKEFILE_LIST)
HELP_PUBLIC_CHECK_TARGETS := lint typecheck test rat check
HELP_PUBLIC_RELEASE_TARGETS := publish-snapshot-local
HELP_PUBLIC_CONTAINER_TARGETS := container-image container-image-local-registry-test

.PHONY: help lint typecheck test rat check container-image container-image-local-registry-test publish-snapshot-local

help: ## Show the curated Make targets for the site-pipeline repository.
	@desc_for() { awk -v target="$$1" 'BEGIN {FS = ":.*## "} $$1 == target {print $$2; exit}' $(HELP_TARGETS); }; \
	print_section() { title="$$1"; shift; printf "\n%s\n" "$$title"; for target in "$$@"; do printf "  %-30s %s\n" "$$target" "$$(desc_for "$$target")"; done; }; \
	printf "Available targets:\n"; \
	print_section "Checks:" $(HELP_PUBLIC_CHECK_TARGETS); \
	print_section "Release helpers:" $(HELP_PUBLIC_RELEASE_TARGETS); \
	print_section "Container image workflows:" $(HELP_PUBLIC_CONTAINER_TARGETS)

lint: ## Run Ruff checks for the Python sources and tests.
	$(UV_RUN) ruff check main.py src/apache_buildish_site_pipeline tests

typecheck: ## Run Mypy across the repository.
	$(UV_RUN) mypy

test: ## Run the Python unit test suite.
	$(UV_RUN) python -m unittest discover -s tests -p 'test_*.py' -v

rat: ## Run Apache RAT license checks.
	tools/rat/rat-check.sh

check: lint typecheck test rat ## Run lint, type checks, tests, and RAT.

publish-snapshot-local: ## Build and publish a local wheel snapshot under dist/snapshots.
	$(UV_RUN) python -m apache_buildish_site_pipeline.snapshot_publish --out-dir $(SNAPSHOT_OUT_DIR)

container-image: ## Build the generic Site Pipeline container image locally.
	tools/site-pipeline-image/build-image.sh --image $(CONTAINER_IMAGE) --platforms $(CONTAINER_IMAGE_PLATFORMS)

container-image-local-registry-test: ## Run the localhost-registry integration test for the container image.
	tools/site-pipeline-image/test-local-registry.sh --platforms '$(LOCAL_REGISTRY_TEST_PLATFORMS)' --tag '$(LOCAL_REGISTRY_TEST_TAG)' $(LOCAL_REGISTRY_TEST_ARGS)
