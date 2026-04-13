# Makefile for local development (using uv)

.PHONY: help venv install run test validate validate-skills check-uv clean

help:
	@echo "Make targets:"
	@echo "  venv     - create Python virtualenv (.venv) using uv"
	@echo "  install  - create venv and install dependencies using uv"
	@echo "  run      - show native SKILL.md usage guidance"
	@echo "  test     - run OpenCode setup validation"
	@echo "  validate - validate OpenCode setup"
	@echo "  validate-skills - validate OpenCode native skill setup"
	@echo "  check-uv - check for forbidden pip/venv commands"
	@echo "  clean    - remove .venv"

venv:
	@uv venv .venv
	@echo "Created .venv with uv"

install: venv
	@uv pip install -r requirements.txt
	@echo "Dependencies installed"

run: install
	@echo "Native skills are loaded by OpenCode from skills/*/SKILL.md"

test: install
	@uv run python validate_opencode_setup.py

validate: install
	@uv run python validate_opencode_setup.py

validate-skills: install
	@uv run python validate_opencode_setup.py

check-uv:
	@echo "=== Checking for forbidden pip/venv commands ==="
	@bash skills/tools/check_uv_usage.sh .

clean:
	@rm -rf .venv
	@echo "Removed .venv"
