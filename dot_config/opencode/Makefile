# Makefile for local development (using uv)

.PHONY: help venv install run test validate test-thinking check-uv clean

help:
	@echo "Make targets:"
	@echo "  venv     - create Python virtualenv (.venv) using uv"
	@echo "  install  - create venv and install dependencies using uv"
	@echo "  run      - run skills_loader.py inside venv"
	@echo "  test     - run quick smoke test"
	@echo "  validate - validate YAML syntax and structure"
	@echo "  test-thinking - test thinking mode detection"
	@echo "  check-uv - check for forbidden pip/venv commands"
	@echo "  clean    - remove .venv"

venv:
	@uv venv .venv
	@echo "Created .venv with uv"

install: venv
	@uv pip install -r requirements.txt
	@echo "Dependencies installed"

run: install
	@uv run python skills_loader.py

test: install
	@echo "=== Testing Python task ==="
	@uv run python -c "from skills_loader import SkillsLoader; print(SkillsLoader().load_for_task('Create a Python script')[:500])"
	@echo ""
	@echo "=== Testing Docker task ==="
	@uv run python -c "from skills_loader import SkillsLoader; print(SkillsLoader().load_for_task('Set up Docker container')[:500])"

validate: install
	@echo "=== Validating YAML files ==="
	@uv run python -c "import yaml; from pathlib import Path; [yaml.safe_load(f.read_text()) for f in Path('skills').rglob('*.yaml')]; print('✓ All YAML files valid')"
	@echo "=== Checking file structure ==="
	@test -f AGENTS.md || echo "✗ AGENTS.md missing"
	@test -f skills_core.yaml || echo "✗ skills_core.yaml missing"
	@test -f skills_catalog.yaml || echo "✗ skills_catalog.yaml missing"
	@echo "✓ File structure valid"

test-thinking: install
	@echo "=== Testing Thinking Mode Detection ==="
	@uv run python -c "from skills_loader import SkillsLoader, ThinkingMode; loader = SkillsLoader(); assert loader._detect_thinking_mode('ls -la') == ThinkingMode.SIMPLE, 'FAIL: simple'; assert loader._detect_thinking_mode('Create a Python script') == ThinkingMode.MEDIUM, 'FAIL: medium'; assert loader._detect_thinking_mode('Design a microservices architecture') == ThinkingMode.COMPLEX, 'FAIL: complex'; print('OK: Simple mode detection'); print('OK: Medium mode detection'); print('OK: Complex mode detection')"

check-uv:
	@echo "=== Checking for forbidden pip/venv commands ==="
	@bash skills/tools/check_uv_usage.sh .

clean:
	@rm -rf .venv
	@echo "Removed .venv"
