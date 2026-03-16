# uv Usage Guide

## Requirements
- This project mandates uv for Python package management.
- Do not use pip/venv/virtualenv directly.

## Common tasks
- Create a venv: `uv venv`
- Install dependencies: `uv pip install -r requirements.txt`
- Install a package: `uv pip install <package>`
- Add a dev dependency: `uv pip install --dev <package>`
- Run a script: `uv run python script.py`
- Run tests: `uv run pytest`
- Export requirements: `uv pip freeze > requirements.txt`

## Examples
```bash
uv venv
uv pip install -r requirements.txt
uv run python scripts/example.py
```

## Troubleshooting
- Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
