# Makefile for local development: venv, deps, run, clean

.PHONY: help venv install run test clean

help:
	@echo "Make targets:"
	@echo "  venv    - create Python virtualenv (.venv)"
	@echo "  install - create venv (if needed) and install dependencies from requirements.txt"
	@echo "  run     - run skills_loader.py inside the venv"
	@echo "  test    - run quick smoke test of loader"
	@echo "  clean   - remove .venv"

venv:
	@python3 -m venv .venv
	@echo "Created .venv"

install: venv
	@.venv/bin/python -m pip install --upgrade pip setuptools wheel
	@.venv/bin/python -m pip install -r requirements.txt
	@echo "Dependencies installed in .venv"

run: install
	@.venv/bin/python skills_loader.py

test: install
	@.venv/bin/python - <<PY
from skills_loader import SkillsLoader
print(SkillsLoader().load_for_task('Create a Python script to parse CSV files')[:800])
PY

clean:
	@rm -rf .venv
	@echo "Removed .venv"
