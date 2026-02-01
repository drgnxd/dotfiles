# Agent Skills System

## 📖 Read This First
This file is your entry point. Always read in this order:
1. This file (AGENTS.md) - System overview
2. skills_core.yaml - Core principles (always loaded)
3. Task-specific skills (auto-loaded by skills_loader.py)

---

## 🐍 Python MANDATORY Rule

**ALWAYS use `uv` for Python package management. NEVER use pip/venv/virtualenv directly.**

```bash
# ✅ Correct
uv venv
uv pip install pandas
uv run script.py

# ❌ WRONG - Do not do this
pip install pandas
python -m venv .venv
virtualenv venv
```

See: uv_usage_guide.md for details

---

## 🏗️ System Structure
```
.opencode/
├── AGENTS.md           ← You are here (start point)
├── skills_core.yaml    ← Core rules (always load)
├── skills_catalog.yaml ← Skill index (metadata)
├── skills_loader.py    ← Auto-loader
└── skills/             ← Task-specific skills
    ├── essential/      ← High-frequency skills
    └── specialized/    ← Domain-specific skills
```

---

## ⚙️ How It Works

### Auto-Loading by Task
When you receive a task:
1. Analyze keywords in task description
2. Load relevant skills from `skills/`
3. Apply rules following priority hierarchy

**Example:**
```
Task: "Create a Python script to parse CSV"
→ Loads: skills_core.yaml (always)
       + essential/languages.yaml (python detected)
       + essential/practices.yaml (code/test implied)
→ Python commands MUST use uv: "uv pip install pandas"
```

---

## 📐 Rules Hierarchy

Apply in this order (higher priority wins):

1. `.opencode/skills/` - Project-specific overrides
2. `CODING_STANDARDS.md` or `STYLE_GUIDE.md` - Project docs
3. `.editorconfig` - Editor configuration
4. Language configs (`pyproject.toml`, `.eslintrc`, etc.)
5. Global skills (fallback defaults)

**When in doubt**: Project rules > Global rules

**Python special rule**: ALWAYS use uv (non-negotiable)

---

## ⚠️ Safety Protocol (CRITICAL)

For destructive commands (`rm`, `dd`, `mkfs`, `chmod -R`, `>`):

**Mandatory steps:**
1. ⚠️ **Warn**: "This is a destructive operation"
2. 📝 **Explain**: What changes, where, and why
3. ❓ **Confirm**: Get explicit user confirmation
4. 💾 **Alternatives**: Offer backup or safer approach

**Never execute without confirmation.**

---

## 🗣️ Language & Mode

### Default Language
Japanese (polite, professional tone)

### Execution Modes
- **Simple**: Direct execution (e.g., "list files")
- **Complex**: Think → Plan → Execute (e.g., "refactor module")
- **Ambiguous**: Ask for clarification

---

## 📤 Output Standards

Every response should include:
- Clear diagnostics/reasoning
- Commands with inline comments
- Reference to applied skill(s)

**Example:**
```bash
# Applied: bash skill (quote vars, validate inputs)
readonly INPUT="${1}"
[[ -n "${INPUT}" ]] || { echo "Error: input required" >&2; exit 1; }
```

**Python Example:**
```bash
# Applied: python skill (uv required)
uv venv
uv pip install -r requirements.txt
uv run pytest
```

---

## 📚 Common References

### Naming Conventions
See `skills_core.yaml` → naming section
- Files: `lowercase_snake_case` (except README.md, SKILL.md)
- Code vars/funcs: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Classes: `PascalCase`

### Python Package Management
See `skills_core.yaml` → python_requirements
- Package manager: `uv` (mandatory)
- Install: `uv pip install <package>`
- Venv: `uv venv`
- Run: `uv run <script>`

### Skill Documentation Format
Each SKILL.md should follow:
- **Aim**: 1-3 line purpose
- **Core**: 3-5 key principles
- **Do**: Concrete rules with examples
- **Examples**: ✅ Good / ✗ Bad pairs
- **Edge**: When to deviate
- **Refs**: External references (URL + access date)

### Reference Format
`[Source] (YYYY-MM-DD) - URL`

Example: `PEP 8 (2025-01-30) - https://peps.python.org/pep-0008/`

---

## 🎯 Quick Task Examples

### Python Development
```
Task: "Write a Python function to read JSON"
Skills loaded: languages.yaml + practices.yaml
Commands: uv pip install <deps>, uv run script.py
Token usage: ~1,800
```

### Infrastructure Work
```
Task: "Set up Docker container with PostgreSQL"
Skills loaded: infrastructure.yaml + languages.yaml
Token usage: ~1,700
```

### Research Task
```
Task: "Compare GraphQL vs REST for our API"
Skills loaded: research.yaml + practices.yaml
Token usage: ~2,000
```
