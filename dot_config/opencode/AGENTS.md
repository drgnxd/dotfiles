# Agent Skills System

## Read This First
This file is your entry point. Always read in this order:
1. This file (AGENTS.md) - System overview
2. skills_core.yaml - Core principles (always loaded)
3. Task-specific skills (auto-loaded by skills_loader.py)

---

## Python MANDATORY Rule

**ALWAYS use `uv` for Python package management. NEVER use pip/venv/virtualenv directly.**

```bash
# Correct
uv venv
uv pip install pandas
uv run script.py

# WRONG - Do not do this
pip install pandas
python -m venv .venv
virtualenv venv
```

See: uv_usage_guide.md for details

---

## Thinking Process Protocol

All tasks go through a thinking mode selection before execution.
Mode is auto-detected from the task description.

### Thinking Mode Selection

| Mode | Overhead | When | Protocol |
|---|---|---|---|
| **Simple** | 0-3% | list, show, get, basic commands | Direct execution |
| **Medium** | 5-8% | create, refactor, fix, implement | Decompose -> Plan -> Execute |
| **Complex** | 10-15% | design, migrate, security, research | Full structured reasoning |

### Core Thinking Templates

#### 1. Problem Decomposition (Medium + Complex: mandatory)
```
[ANALYZE]
- Input: <state clearly>
- Output: <expected outcome>
- Constraints: <limitations>
- Dependencies: <prerequisites>
```

#### 2. Approach Evaluation (Complex: mandatory)
```
[APPROACH_A] <description>
Pros: / Cons:

[APPROACH_B] <description>
Pros: / Cons:

[SELECTED] <choice> - <rationale>
```

#### 3. Step-by-Step Execution (Medium + Complex)
```
1. [ACTION] <what>
   [RESULT] <intermediate outcome>
   [VERIFY] <validation>

2. [ACTION] <next step, referencing previous RESULT>
   [RESULT] <new outcome>
   [VERIFY] <validation>
```

#### 4. Symbolic-Natural Hybrid (Complex, logic-heavy)
```
// Symbolic
IF condition THEN action ELSE alternative

-> Explanation:
"Natural language reasoning..."
```

#### 5. Intermediate Variables
```
CONCLUSION_A: <first finding>
-> Using A, derive CONCLUSION_B: <next finding>
-> A + B -> FINAL_RESULT: <synthesis>
```

#### 6. Metacognitive Markers
- **"Wait..."** - reconsidering an assumption
- **"Therefore..."** - drawing a logical conclusion
- **"However..."** - contradiction or edge case found
- **"Let me verify..."** - validation checkpoint
- **"Given that..."** - using an established fact

### Token Efficiency

- **High-precision** (security, migration): Full protocol. 10-15% overhead acceptable.
- **Exploratory** (prototyping, research): Streamlined. Verify at milestones only.
- **Simple** (routine): Skip thinking trace entirely.

### Example

```
Task: "Refactor auth module to use JWT"

[ANALYZE]
- Input: Session-based auth module
- Output: JWT auth with refresh tokens
- Constraints: Zero downtime, backward compat
- Dependencies: PyJWT, Redis

[APPROACH_EVALUATION]
APPROACH_A: In-place replacement - Pros: simple / Cons: risky
APPROACH_B: Feature flag parallel run - Pros: safe rollout / Cons: temporary duplication
[SELECTED] B - safety over simplicity

[EXECUTION]
1. [ACTION] Add JWT dependencies
   [RESULT] PyJWT added
   [VERIFY] OK: no conflicts with `uv pip install`

2. [ACTION] Create jwt_service.py
   [RESULT] encode/decode/refresh functions
   [VERIFY] OK: all tests pass with `uv run pytest`

3. [ACTION] Add feature flag
   [RESULT] USE_JWT_AUTH (default: False)
   [VERIFY] OK: existing behavior preserved

[CONFIDENCE] 8/10 - Systematic approach, verified at each step
```

---

## System Structure
```
.opencode/
├── AGENTS.md           <- You are here (start point)
├── skills_core.yaml    <- Core rules (always load)
├── skills_catalog.yaml <- Skill index (metadata)
├── skills_loader.py    <- Auto-loader (with thinking mode detection)
├── uv_usage_guide.md   <- Python package management guide
└── skills/             <- Task-specific skills
    ├── essential/      <- High-frequency skills
    │   ├── languages.yaml
    │   ├── practices.yaml
    │   └── thinking_framework.yaml   <- Thinking skill definitions
    └── specialized/    <- Domain-specific skills
```

---

## How It Works

### Auto-Loading by Task
When you receive a task:
1. **Detect thinking mode** (Simple / Medium / Complex)
2. Analyze keywords in task description
3. Prepend always-load skills (japanese, thinking)
4. Load task-matched skills within token budget
5. Apply rules following priority hierarchy

**Example:**
```
Task: "Create a Python script to parse CSV"

[Thinking Mode: MEDIUM]
-> Loads: skills_core.yaml (always)
       + japanese (always)
       + thinking (always)
       + essential/languages.yaml (python detected)
       + essential/practices.yaml (code implied)
-> Python commands MUST use uv
```

---

## Rules Hierarchy

Apply in this order (higher priority wins):

1. **Thinking Protocol** - Structured reasoning (this file)
2. **uv Mandatory Rule** - Python package management (non-negotiable)
3. `.opencode/skills/` - Project-specific overrides
4. `CODING_STANDARDS.md` or `STYLE_GUIDE.md` - Project docs
5. `.editorconfig` - Editor configuration
6. Language configs (`pyproject.toml`, `.eslintrc`, etc.)
7. Global skills (fallback defaults)

**Non-negotiable**: Thinking Protocol + uv Rule apply to all tasks.

---

## Safety Protocol (CRITICAL)

For destructive commands (`rm`, `dd`, `mkfs`, `chmod -R`, `>`):

**Mandatory steps:**
1. **Warn**: "This is a destructive operation"
2. **Explain**: What changes, where, and why
3. **Confirm**: Get explicit user confirmation
4. **Alternatives**: Offer backup or safer approach

**Thinking integration:**
```
[SAFETY_CHECK]
- Operation: <command>
- Risk: <CRITICAL / HIGH / MEDIUM>
- Verification: <what to confirm>
- Alternative: <safer option>
```

**Never execute without confirmation.**

---

## Language & Mode

### Default Language
Japanese (polite, professional tone)

### Agent Input Language
All agent-facing instructions, prompts, and skill files must be written in English for token efficiency.

### Execution Modes
- **Simple**: Direct execution (e.g., "list files")
- **Medium**: Decompose -> Plan -> Execute (e.g., "refactor module")
- **Complex**: Full structured reasoning (e.g., "design system")
- **Ambiguous**: Clarify requirements first, then select mode

---

## Output Standards

Every response should include:
- **Thinking trace** (Medium/Complex tasks only)
- Clear diagnostics/reasoning
- Commands with inline comments
- Reference to applied skill(s)
- **Confidence score** for Complex decisions

**Bash Example:**
```bash
# Applied: bash skill (quote vars, validate inputs)
readonly INPUT="${1}"
[[ -n "${INPUT}" ]] || { echo "Error: input required" >&2; exit 1; }
```

**Python Example:**
```bash
# Applied: python skill (uv required)
# Thinking Mode: MEDIUM
uv venv
uv pip install -r requirements.txt
uv run pytest
```

---

## Common References

### Thinking Patterns by Task Type

**Algorithmic**: Symbolic notation first -> natural language explanation -> edge case verification
**System Design**: Multi-approach evaluation -> trade-off matrix -> confidence scoring
**Refactoring**: Before/after state mapping -> invariant checks -> behavior equivalence
**Security**: Threat modeling (symbolic) -> mitigation per threat -> defense in depth

### Naming Conventions
See `skills_core.yaml` -> naming section
- Files: `lowercase_snake_case` (except README.md, SKILL.md)
- Code vars/funcs: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Classes: `PascalCase`

### Python Package Management
See `uv_usage_guide.md`
- Package manager: `uv` (mandatory)
- Install: `uv pip install <package>`
- Venv: `uv venv`
- Run: `uv run <script>`

### Skill Documentation Format
Each SKILL.md should follow:
- **Aim**: 1-3 line purpose
- **Core**: 3-5 key principles
- **Do**: Concrete rules with examples
- **Examples**: OK / Avoid pairs
- **Edge**: When to deviate
- **Refs**: External references (URL + access date)

### Reference Format
`[Source] (YYYY-MM-DD) - URL`

Example: `PEP 8 (2025-01-30) - https://peps.python.org/pep-0008/`

---

## Quick Task Examples

### Python Development
```
Task: "Write a Python function to read JSON"
[Thinking Mode: MEDIUM]
Skills loaded: thinking + languages.yaml + practices.yaml
Commands: uv pip install <deps>, uv run script.py
Token usage: ~2,100
```

### Infrastructure Work
```
Task: "Set up Docker container with PostgreSQL"
[Thinking Mode: MEDIUM -> COMPLEX (security implications)]
Skills loaded: thinking + infrastructure.yaml + languages.yaml
Token usage: ~2,400
```

### Research Task
```
Task: "Compare GraphQL vs REST for our API"
[Thinking Mode: COMPLEX]
Skills loaded: thinking + research.yaml + practices.yaml
Token usage: ~2,800
```
