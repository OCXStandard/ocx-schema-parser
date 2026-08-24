# CI/CD Pipeline Design — ocx-schema-parser

**Date:** 2026-08-24
**Status:** Approved

## Goal

A full CI/CD pipeline for ocx-schema-parser: local pre-commit linting and
pre-push tests with uv, GitHub Actions workflows for build/test, PyPI
deployment gated on tests, GitHub Releases with CHANGELOG notes, and API
documentation published to GitHub Pages. Transfer PyPI project ownership to
the 3Docx.org organization (manual step).

## Current State

- `.pre-commit-config.yaml`: check-yaml, end-of-file-fixer,
  trailing-whitespace, typos, ruff (lint + format). No local test hook.
- `.github/workflows/documentation.yaml`: Sphinx build (`-W --keep-going`)
  on PRs and pushes to main; deploys to `gh-pages` on main push. Kept as-is.
- `.github/workflows/python-publish.yml`: on `v*` tag push — uv build →
  PyPI trusted publishing (OIDC, `pypi` environment). No test gate, no
  GitHub Release.
- No CI workflow running tests on PRs/pushes.
- Release tooling: tbump bumps version in `pyproject.toml` and
  `ocx_schema_parser/__init__.py`, requires a CHANGELOG entry, commits and
  pushes a `v{version}` tag.

## Design

### 1. Local hooks (pre-commit + pre-push)

Extend `.pre-commit-config.yaml`:

- Existing hooks stay on the default `pre-commit` stage.
- New local hook running the full test suite on the `pre-push` stage:
  - `id: pytest`, `entry: uv run pytest`, `language: system`,
    `pass_filenames: false`, `always_run: true`, `stages: [pre-push]`.
- Install both hook types:
  `uv run pre-commit install --hook-type pre-commit --hook-type pre-push`.
- Rationale: linting stays fast on every commit; the full suite (with
  coverage, per pyproject `addopts`) runs only on push.

### 2. CI workflows

Two new workflow files:

**`.github/workflows/tests.yml`** — reusable, `on: workflow_call`.
Single job `test` on `ubuntu-latest`, Python 3.12:

1. `actions/checkout@v4`
2. `astral-sh/setup-uv@v5` with cache enabled
3. `actions/setup-python@v5` (3.12)
4. `uv sync`
5. `uv run ruff check .`
6. `uv run ruff format --check .`
7. `uv run pytest` — coverage is reported in logs only; no minimum
   threshold is enforced.

**`.github/workflows/ci.yml`** — triggers on `pull_request` and `push`
to `main`. One job that `uses: ./.github/workflows/tests.yml`. Includes a
`concurrency` group keyed on workflow + ref with `cancel-in-progress: true`.

No test matrix: the package is pure Python, `requires-python >= 3.10`;
a single 3.12/ubuntu job is sufficient.

### 3. Release & PyPI publish

`python-publish.yml` keeps its `push: tags: ['v*']` trigger and gains a
test gate and a GitHub Release job. Job graph:

```
test (uses tests.yml)
  └─> build (uv build, upload dist/ artifact)
        └─> publish-to-pypi (pypi environment, OIDC trusted publishing)
              └─> github-release (CHANGELOG notes + dist assets)
```

- **test**: `uses: ./.github/workflows/tests.yml`.
- **build**: unchanged except `needs: test`.
- **publish-to-pypi**: unchanged — `environment: pypi`,
  `permissions: id-token: write`, `pypa/gh-action-pypi-publish@release/v1`.
- **github-release**: `needs: publish-to-pypi`,
  `permissions: contents: write`. Extracts the tagged version's section
  from `CHANGELOG.md` (small script step) and runs
  `gh release create "$TAG" dist/* --notes-file <extracted>`. The
  extraction step fails if the version section is missing.

Release procedure (unchanged for the developer):

1. Add a CHANGELOG entry for the new version.
2. `uv run tbump X.Y.Z` — bumps files, commits, pushes tag.
3. Tag push triggers test → build → publish → release.

### 4. Documentation

The existing `documentation.yaml` already satisfies the requirement:
Sphinx API docs build as a required check on PRs and deploy to GitHub
Pages (`gh-pages` branch) on push to main. No changes.

### 5. PyPI organization (3Docx.org) — manual step

Yes, the project can be moved to the org. PyPI Organizations own projects;
an owner of both the project and the 3Docx.org organization transfers it
via the PyPI web UI: project → Settings → "Transfer project to an
organization" (or accept an org invitation). The trusted-publisher
configuration is per-project and carries over — no workflow changes
required. This is a one-time manual action outside the repository.

### 6. README update

Add a short "Development" section: `uv sync`, pre-commit/pre-push hook
installation, running tests, and the release procedure above.

## Error handling

- Publish never runs if tests fail (job `needs` chain).
- GitHub Release is created only after a successful PyPI upload, so a
  failed upload leaves no dangling release.
- tbump refuses to tag without a CHANGELOG entry; the release-notes
  extraction fails loudly as a second guard.
- Docs deployment is independent of releases and tracks `main`.

## Verification

- Workflow YAML validated by the `check-yaml` pre-commit hook.
- The reusable workflow is exercised by CI on the PR/push that introduces
  it.
- Pre-push hook verified locally by running
  `uv run pre-commit run --hook-stage pre-push --all-files`.
- Full publish path verified on the next real `v*` tag.

## Out of scope

- Test matrix across Python versions or operating systems.
- Coverage thresholds or Codecov integration.
- Changes to Sphinx configuration or docs content.
- Automating the PyPI organization transfer.
