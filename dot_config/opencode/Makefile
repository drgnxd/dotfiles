# Makefile for local development

.PHONY: help venv install run test validate clean

help:
	@echo "Make targets:"
	@echo "  venv     - create Python virtualenv (.venv)"
	@echo "  install  - create venv and install dependencies"
	@echo "  run      - run skills_loader.py inside venv"
	@echo "  test     - run quick smoke test"
	@echo "  validate - validate YAML syntax and structure"
	@echo "  clean    - remove .venv"

venv:
	@python3 -m venv .venv
	@echo "Created .venv"

install: venv
	@.venv/bin/python -m pip install --upgrade pip setuptools wheel
	@.venv/bin/python -m pip install -r requirements.txt
	@echo "Dependencies installed"

run: install
	@.venv/bin/python skills_loader.py

test: install
	@echo "=== Testing Python task ==="
	@.venv/bin/python -c "from skills_loader import SkillsLoader; print(SkillsLoader().load_for_task('Create a Python script')[:500])"
	@echo ""
	@echo "=== Testing Docker task ==="
	@.venv/bin/python -c "from skills_loader import SkillsLoader; print(SkillsLoader().load_for_task('Set up Docker container')[:500])"

validate: install
	@echo "=== Validating YAML files ==="
	@.venv/bin/python -c "import yaml; from pathlib import Path; [yaml.safe_load(f.read_text()) for f in Path('skills').rglob('*.yaml')]; print('✓ All YAML files valid')"
	@echo "=== Checking file structure ==="
	@test -f AGENTS.md || echo "✗ AGENTS.md missing"
	@test -f skills_core.yaml || echo "✗ skills_core.yaml missing"
	@test -f skills_catalog.yaml || echo "✗ skills_catalog.yaml missing"
	@echo "✓ File structure valid"

clean:
	@rm -rf .venv
	@echo "Removed .venv"
