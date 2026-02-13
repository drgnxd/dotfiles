# Makefile for local development (using uv)

.PHONY: help venv install run test pytest validate validate-strict \
        test-thinking preset check-uv clean

help:
	@echo "Make targets:"
	@echo "  venv            - create Python virtualenv (.venv) using uv"
	@echo "  install         - create venv and install dependencies using uv"
	@echo "  run             - run skills_loader.py demo output"
	@echo "  test            - run quick smoke test"
	@echo "  pytest          - run full pytest test suite"
	@echo "  validate        - validate YAML syntax and structure"
	@echo "  validate-strict - validate with duplicate keyword warnings"
	@echo "  test-thinking   - test thinking mode detection"
	@echo "  preset          - load a preset (usage: make preset P=py_dev)"
	@echo "  check-uv        - check for forbidden pip/venv commands"
	@echo "  clean           - remove .venv and caches"

venv:
	@test -d .venv || uv venv .venv
	@echo ".venv ready"

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

pytest: install
	@uv run pytest tests/ -v

validate: install
	@uv run python skills_loader.py --validate

validate-strict: install
	@uv run python skills_loader.py --validate-strict

test-thinking: install
	@echo "=== Testing Thinking Mode Detection ==="
	@uv run python -c "from skills_loader import SkillsLoader, ThinkingMode; loader = SkillsLoader(); assert loader._detect_thinking_mode('ls -la') == ThinkingMode.SIMPLE, 'FAIL: simple'; assert loader._detect_thinking_mode('Create a Python script') == ThinkingMode.MEDIUM, 'FAIL: medium'; assert loader._detect_thinking_mode('Design a microservices architecture') == ThinkingMode.COMPLEX, 'FAIL: complex'; print('OK: Simple mode detection'); print('OK: Medium mode detection'); print('OK: Complex mode detection')"

preset: install
	@if [ -z "$(P)" ]; then echo "Usage: make preset P=py_dev"; echo "Available presets: py_dev, devops, research, full"; exit 1; fi
	@uv run python skills_loader.py --preset=$(P)

check-uv:
	@echo "=== Checking for forbidden pip/venv commands ==="
	@bash skills/tools/check_uv_usage.sh .

clean:
	@rm -rf .venv .pytest_cache
	@echo "Removed .venv and caches"
