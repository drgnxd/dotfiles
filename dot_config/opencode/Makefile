# Makefile for local development: venv, deps, run, clean

.PHONY: help venv install run test clean

help:
	@echo "Make targets:"
	@echo "  venv     - create Python virtualenv (.venv)"
	@echo "  install  - create venv (if needed) and install dependencies"
	@echo "  run      - run skills_loader.py"
	@echo "  test     - run quick smoke test"
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
	@echo "=== Smoke Test Output ==="
	@.venv/bin/python skills_loader.py | head -n 30

clean:
	@rm -rf .venv
	@echo "Removed .venv"
