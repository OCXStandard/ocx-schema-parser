# CI/CD Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Full CI/CD for ocx-schema-parser: local lint-on-commit + test-on-push hooks, a reusable GitHub Actions test workflow gating both CI and the tag-triggered PyPI publish, and a GitHub Release with CHANGELOG notes after publish.

**Architecture:** A reusable `tests.yml` workflow (lint + pytest) is called by a new `ci.yml` (PRs and pushes to main) and by the existing `python-publish.yml` as a gate before build/publish. The publish workflow gains a final job that extracts the tagged version's CHANGELOG section and creates a GitHub Release. Locally, pre-commit gains a `pre-push` pytest hook. The docs workflow is untouched.

**Tech Stack:** uv, pre-commit, ruff, pytest, GitHub Actions (`astral-sh/setup-uv`, `pypa/gh-action-pypi-publish`, `gh` CLI).

**Spec:** `docs/superpowers/specs/2026-08-24-ci-cd-pipeline-design.md`

---

## File map

- Modify: `.pre-commit-config.yaml` — add pre-push pytest hook
- Create: `.github/workflows/tests.yml` — reusable lint+test workflow
- Create: `.github/workflows/ci.yml` — PR/main trigger, calls tests.yml
- Modify: `.github/workflows/python-publish.yml` — test gate + GitHub Release job
- Create: `scripts/extract_changelog.py` — release-notes extraction (testable locally)
- Create: `tests/test_extract_changelog.py` — tests for the extraction script
- Modify: `README.md` — Development section
- Untouched: `.github/workflows/documentation.yaml`

Notes for the engineer:

- This repo uses **uv** for everything: `uv sync`, `uv run <cmd>`. Never call `pip` or bare `pytest`.
- CHANGELOG version headings look exactly like `## [3.0.0] - 2026-08-20`; the unreleased section is `## [Unreleased]`.
- The repo's pytest config (pyproject `addopts`) always runs coverage; a plain `uv run pytest` prints a coverage table — that is expected.
- All commits: include the trailer `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`.

---

### Task 1: CHANGELOG extraction script (TDD)

The GitHub Release job needs release notes for the tagged version. Put the logic in a real script so it can be tested, instead of inline shell in YAML.

**Files:**
- Create: `scripts/extract_changelog.py`
- Test: `tests/test_extract_changelog.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_extract_changelog.py`:

```python
from pathlib import Path

import pytest

from scripts.extract_changelog import extract_section

CHANGELOG = """\
# ocx-schema-parser: Changelog

## [Unreleased]

### Added

* Something pending.

## [3.1.0] - 2026-09-01

### Added

* New feature A.

### Fixed

* Bug B.

## [3.0.0] - 2026-08-20

### Changed

* Old stuff.
"""


def test_extracts_single_version_section(tmp_path: Path):
    path = tmp_path / "CHANGELOG.md"
    path.write_text(CHANGELOG, encoding="utf-8")
    notes = extract_section(path, "3.1.0")
    assert "New feature A." in notes
    assert "Bug B." in notes
    assert "Old stuff." not in notes
    assert "Something pending." not in notes
    assert "## [3.1.0]" not in notes  # heading itself excluded


def test_missing_version_raises(tmp_path: Path):
    path = tmp_path / "CHANGELOG.md"
    path.write_text(CHANGELOG, encoding="utf-8")
    with pytest.raises(SystemExit):
        extract_section(path, "9.9.9")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_extract_changelog.py -v`
Expected: FAIL/ERROR with `ModuleNotFoundError: No module named 'scripts'` (pyproject sets `pythonpath = ["."]`, so imports resolve once the file exists).

- [ ] **Step 3: Write the script**

Create `scripts/extract_changelog.py`:

```python
"""Extract one version's section from CHANGELOG.md.

Usage: python scripts/extract_changelog.py <version> [changelog-path]

Prints the body of the ``## [<version>] - <date>`` section (heading
excluded) to stdout. Exits non-zero if the section is missing, which
fails the GitHub Release job loudly.
"""

import re
import sys
from pathlib import Path


def extract_section(path: Path, version: str) -> str:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if match is None:
        sys.exit(f"No CHANGELOG section found for version {version}")
    return match.group(1).strip() + "\n"


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: extract_changelog.py <version> [changelog-path]")
    version = sys.argv[1].lstrip("v")
    path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("CHANGELOG.md")
    sys.stdout.write(extract_section(path, version))


if __name__ == "__main__":
    main()
```

Also create an empty `scripts/__init__.py` so the test import works:

```python
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_extract_changelog.py -v`
Expected: 2 passed.

- [ ] **Step 5: Sanity-check against the real CHANGELOG**

Run: `uv run python scripts/extract_changelog.py 3.0.0`
Expected: prints the 3.0.0 section body (starts with `### Added` or similar), exit code 0.

Run: `uv run python scripts/extract_changelog.py 9.9.9; echo "exit: $?"` (PowerShell: `uv run python scripts/extract_changelog.py 9.9.9; echo "exit: $LASTEXITCODE"`)
Expected: error message, non-zero exit.

- [ ] **Step 6: Commit**

```bash
git add scripts/extract_changelog.py scripts/__init__.py tests/test_extract_changelog.py
git commit -m "feat: add CHANGELOG section extraction script for release notes"
```

---

### Task 2: Pre-push pytest hook

**Files:**
- Modify: `.pre-commit-config.yaml`

- [ ] **Step 1: Add the local pre-push hook**

Append this repo block at the end of `.pre-commit-config.yaml` (keep existing content unchanged):

```yaml
  - repo: local
    hooks:
      - id: pytest
        name: pytest (full suite)
        entry: uv run pytest
        language: system
        pass_filenames: false
        always_run: true
        stages: [pre-push]
```

- [ ] **Step 2: Install both hook stages**

Run: `uv run pre-commit install --hook-type pre-commit --hook-type pre-push`
Expected: `pre-commit installed at .git\hooks\pre-commit` and `... .git\hooks\pre-push`.

- [ ] **Step 3: Verify the pre-push stage runs the suite**

Run: `uv run pre-commit run --hook-stage pre-push --all-files`
Expected: `pytest (full suite).....Passed` (takes as long as the test suite; coverage table in output is normal).

- [ ] **Step 4: Verify normal commits do NOT run pytest**

Run: `uv run pre-commit run --all-files`
Expected: ruff/typos/etc. run; **no** `pytest` hook in the output.

- [ ] **Step 5: Commit**

```bash
git add .pre-commit-config.yaml
git commit -m "build: run full pytest suite on pre-push via pre-commit"
```

(The commit itself exercises the lint hooks — if a hook modifies files, `git add` and commit again.)

---

### Task 3: Reusable test workflow

**Files:**
- Create: `.github/workflows/tests.yml`

- [ ] **Step 1: Create the workflow**

Create `.github/workflows/tests.yml` with exactly:

```yaml
name: Tests

on:
  workflow_call:

permissions:
  contents: read

jobs:
  test:
    name: Lint and test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: uv sync

      - name: Ruff lint
        run: uv run ruff check .

      - name: Ruff format check
        run: uv run ruff format --check .

      - name: Run tests
        run: uv run pytest
```

- [ ] **Step 2: Validate YAML**

Run: `uv run pre-commit run check-yaml --files .github/workflows/tests.yml`
Expected: `check yaml.....Passed`.

- [ ] **Step 3: Verify the lint commands pass locally (so CI won't be red on arrival)**

Run: `uv run ruff check . ; uv run ruff format --check .`
Expected: both succeed. If `ruff format --check` reports files that would be reformatted, run `uv run ruff format .`, review the diff, and include those changes in this task's commit.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/tests.yml
git commit -m "ci: add reusable lint+test workflow"
```

---

### Task 4: CI workflow for PRs and main

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create the workflow**

Create `.github/workflows/ci.yml` with exactly:

```yaml
name: CI

on:
  push:
    branches:
      - main
  pull_request:

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

permissions:
  contents: read

jobs:
  tests:
    uses: ./.github/workflows/tests.yml
```

- [ ] **Step 2: Validate YAML**

Run: `uv run pre-commit run check-yaml --files .github/workflows/ci.yml`
Expected: `check yaml.....Passed`.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: run lint+tests on pull requests and pushes to main"
```

---

### Task 5: Gate publish on tests and add GitHub Release

**Files:**
- Modify: `.github/workflows/python-publish.yml`

- [ ] **Step 1: Replace the workflow content**

Replace the **entire** content of `.github/workflows/python-publish.yml` with:

```yaml
name: Publish Python 🐍 distribution 📦 to PyPI

on:
  push:
    tags:
      - 'v*'

permissions:
  contents: read

jobs:
  test:
    name: Lint and test
    uses: ./.github/workflows/tests.yml

  build:
    name: Build distribution 📦
    needs:
      - test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Build distribution
        run: uv build

      - name: Store the distribution packages
        uses: actions/upload-artifact@v4
        with:
          name: python-package-distributions
          path: dist/

  publish-to-pypi:
    name: Publish Python 🐍 distribution 📦 to PyPI
    needs:
      - build
    runs-on: ubuntu-latest
    environment:
      name: pypi
      url: https://pypi.org/p/ocx-schema-parser
    permissions:
      id-token: write  # IMPORTANT: mandatory for trusted publishing
    steps:
      - name: Download all the dists
        uses: actions/download-artifact@v4
        with:
          name: python-package-distributions
          path: dist/

      - name: Publish distribution 📦 to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1

  github-release:
    name: Create GitHub Release
    needs:
      - publish-to-pypi
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4

      - name: Download all the dists
        uses: actions/download-artifact@v4
        with:
          name: python-package-distributions
          path: dist/

      - name: Extract release notes from CHANGELOG
        run: python scripts/extract_changelog.py "${{ github.ref_name }}" > release-notes.md

      - name: Create GitHub Release
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: >-
          gh release create "${{ github.ref_name }}"
          dist/*
          --title "${{ github.ref_name }}"
          --notes-file release-notes.md
```

Notes on intentional changes from the old file:
- `build` no longer runs `uv sync` — `uv build` needs no installed environment.
- `test` job gates `build` via `needs`.
- `github-release` runs the extraction script (Task 1) with the tag name (`v3.1.0` — the script strips the leading `v`) and fails if the CHANGELOG section is missing.

- [ ] **Step 2: Validate YAML**

Run: `uv run pre-commit run check-yaml --files .github/workflows/python-publish.yml`
Expected: `check yaml.....Passed`.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/python-publish.yml
git commit -m "ci: gate PyPI publish on tests and create GitHub Release from CHANGELOG"
```

---

### Task 6: README Development section

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add the section**

Insert the following **before** the `## Changelog` heading in `README.md`:

```markdown
## Development

This project uses [uv](https://docs.astral.sh/uv/) for environment and
package management.

```bash
# Set up the environment
uv sync

# Install git hooks: linting on commit, full test suite on push
uv run pre-commit install --hook-type pre-commit --hook-type pre-push

# Run the tests (with coverage)
uv run pytest
```

### Releasing

1. Add a section for the new version to `CHANGELOG.md`
   (heading format: `## [X.Y.Z] - YYYY-MM-DD`).
2. Run `uv run tbump X.Y.Z` — this bumps the version, commits, and pushes
   a `vX.Y.Z` tag.
3. The tag triggers the publish workflow: tests → build → PyPI (trusted
   publishing) → GitHub Release with the CHANGELOG notes.
```

(Watch the nested code fence: use a wider outer fence or place the bash block as a normal fenced block within the section — the final README must render correctly.)

- [ ] **Step 2: Verify rendering**

Run: `uv run python -c "print(open('README.md', encoding='utf-8').read())"` and visually check the section, or preview in an editor.
Expected: fenced blocks balanced; `## Changelog` still the last section.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add Development section with hooks setup and release procedure"
```

---

### Task 7: Push and verify CI end-to-end

**Files:** none (verification only)

- [ ] **Step 1: Push main**

Run: `git push` (the pre-push hook runs the full test suite first — expected to pass).

- [ ] **Step 2: Watch the CI run**

Run: `gh run watch --exit-status` (or `gh run list --limit 3` and then `gh run watch <id> --exit-status`).
Expected: the **CI** workflow succeeds (lint + tests job green). The **Docs** workflow also runs and deploys — pre-existing behavior.

- [ ] **Step 3: Confirm workflow files are recognized**

Run: `gh workflow list`
Expected: lists `CI`, `Docs`, `Tests`, and `Publish Python 🐍 distribution 📦 to PyPI`.

---

## Manual follow-ups (outside this plan)

- **PyPI org transfer:** an owner of both the `ocx-schema-parser` project and the 3Docx.org organization transfers the project on pypi.org: project → Settings → "Transfer project to an organization". Trusted-publisher config carries over; no repo changes.
- **Full publish path** is verified on the next real `v*` tag release.
