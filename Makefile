# A self-documenting Makefile
# You can set these variables from the command line, and also
# from the environment for the first two.

PACKAGE := ocx_schema_parser
SOURCE = ./ocx_schema_parser
# PS replacements for sh
RM = 'del -Confirmed False'

# PROJECT SETUP ##############################################################
install-tools: ## Install the uv toolbox
	@uv tool install ruff
	@uv tool install tbump
	@iv tool install pre-commit

it: install-tools
PHONY: it

init: ## Initiate the project using uv. Install all dependencies in the virtual environment and activate it
	@uv sync

ps-venv:  ## Activate the virtual environment for powershell terminal
	@powershell -NoProfile -ExecutionPolicy Bypass -Command "& { . .venv/Scripts/activate.ps1 }"
	@powershell -NoProfile -ExecutionPolicy Bypass -Command "Write-Host 'Activated virtual environment' -ForegroundColor Blue"
av: ps-venv

# Color output
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# DOCUMENTATION ##############################################################
SPHINXBUILD = sphinx-build -E -b html docs dist/docs
COVDIR = "htmlcov"

doc-serve: ## Open the the html docs built by Sphinx
	@cmd /c start "_build/index.html"

ds: doc-serve
.PHONY: ds


doc: ## Build the html docs using Sphinx. For other Sphinx options, run make in the docs folder
	@uv run sphinx-build docs _build

doc-links: ## Check the internal and external links after building the documentation
	@uv run sphinx-build docs -W -b linkcheck -d _build/doctrees _build/html
PHONY: doc-links

doc-export: ## Export the requirements to docs/requirements.txt
	@uv export --no-hashes --group docs -o docs/requirements.txt

# RUN ##################################################################

PHONY: run
run: ## Run the
	uv run main.py

# pre-commit ######################################################################
pre-commit:	## Run the pre-commit hooks
	@uv run pre-commit run --all-files

# TESTS #######################################################################

FAILURES := .pytest_cache/pytest/v/cache/lastfailed

test:  ## Run unit and integration tests
	@uv run pytest --log-disable=test --durations=5  --cov-report html --cov=$(SOURCE)

test-upd:  ## Run unit and integration tests
	@uv run pytest --force-regen --durations=5  --cov-report html --cov=$(SOURCE)


test-cov:  ## View the test coverage report
	cmd /c start $(CURDIR)/htmlcov/index.html

# HELP ########################################################################


.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help

#-----------------------------------------------------------------------------------------------
