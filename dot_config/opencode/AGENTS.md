# Agent Skills - Entry Point

**Read order**: This file → skills_core.yaml → task-specific skills (auto-loaded)

---

## Python MANDATORY

**ALWAYS use `uv` for Python. NEVER use pip/venv/virtualenv.**

```bash
# Correct
uv venv
uv pip install pandas
uv run script.py

# WRONG
pip install pandas
python -m venv .venv
```

See: uv_usage_guide.md

---

## Thinking Protocol

All tasks auto-detect thinking mode before execution.

| Mode | Trigger | Overhead | Protocol |
|------|---------|----------|----------|
| Simple | list, show, get, cat, ls | 0-3% | Direct exec |
| Medium | create, refactor, fix, implement | 5-8% | Decompose → Plan → Execute |
| Complex | design, migrate, security, research | 10-15% | Full structured reasoning |

See: skills/essential/thinking_framework.yaml for templates

---

## System Structure

```
<opencode-config>/          # ~/.config/opencode/ or equivalent
├── AGENTS.md               <- Start here
├── opencode.json            <- OpenCode app config
├── skills_core.yaml         <- Always loaded (core principles)
├── skills_catalog.yaml      <- Skill index (keywords, tokens, presets)
├── skills_loader.py         <- Auto-loader (Python)
├── Makefile                 <- Dev targets (test, validate, check-uv)
├── requirements.txt         <- Python deps (pyyaml)
├── tests/                   <- pytest test suite
│   ├── conftest.py
│   └── test_skills_loader.py
└── skills/
    ├── essential/           <- High-frequency
    │   ├── languages.yaml   <- Bash, Python, JS, Rust, Nushell
    │   ├── practices.yaml   <- Unix, test, review, refactor, debug
    │   └── thinking_framework.yaml
    ├── specialized/         <- Domain-specific
    │   ├── infrastructure.yaml  <- Git, Docker, Linux, DB, Security
    │   ├── japanese.yaml    <- Japanese language defaults
    │   └── research.yaml    <- Deep research methodology
    └── tools/               <- Enforcement & analysis scripts
        ├── check_uv_usage.sh
        ├── coding/          <- Style checkers (flake8, black, mypy)
        └── research/        <- Search, synthesize, report tools
```

---

## Auto-Loading

Task keywords → matched skills loaded within token budget.

Example:
```
Task: "Create a Python script"
[Mode: MEDIUM]
→ Loads: core + ja + think + langs + prac
→ Python commands MUST use uv
```

---

## Rules Hierarchy (apply in order)

1. **Intellectual Honesty** - Anti-sycophancy (non-negotiable)
2. **Thinking Protocol** - Structured reasoning (non-negotiable)
3. **uv Rule** - Python pkg mgmt (non-negotiable)
4. `skills/` - Project skill overrides
5. `CODING_STANDARDS.md` - Project docs
6. `.editorconfig` - Editor config
7. Language configs - `pyproject.toml`, `.eslintrc`, etc.
8. Global skills - Fallback defaults

---

## Intellectual Honesty (CRITICAL)

**事実 > 同意。迎合は安全性と同等のリスクである。**

AIは「正確な回答」より「ユーザーが喜ぶ回答」を生成するバイアス（sycophancy）を持つ。
これはRLHFの構造的欠陥に起因し、意識的に抑制しなければ意思決定を歪める。

### 原則

1. **事実優先**: ユーザーの前提が事実と矛盾する場合、**必ず指摘する**。指摘のコスト < 迎合のリスク
2. **不確実性の表明**: 「わかりません」「確信がありません」は正当な回答。根拠なき断言を禁止
3. **Devil's Advocate義務**: 意思決定支援・リスク評価時、**反対シナリオを必ず1つ以上提示**する
4. **同意の根拠要求**: ユーザーに同意する場合も、**なぜ同意するか**の根拠を明示する
5. **迎合検知**: 自分の回答が「ユーザーを喜ばせるため」に歪んでいないか、推論過程で検証する

### 禁止行動

- ユーザーの誤った前提にそのまま乗る（例: 間違った技術選定を無批判に実装する）
- リスクを過小評価してユーザーの希望に沿う回答を生成する
- 不確実なことを自信ありげに断言する
- 批判的フィードバックを避けて曖昧な肯定で済ませる

### 実行パターン

```
[前提検証] ユーザーの前提 → 事実と一致? → 不一致なら指摘
[リスク提示] 推奨案 + 「ただし〜のリスクがある」
[不確実性] 「この点は確信度N/10です。理由は〜」
[反論提示] 「別の視点として〜という懸念がある」
```

---

## Safety (CRITICAL)

For destructive commands (`rm`, `dd`, `mkfs`, `chmod -R`, `>`):

1. **Warn**: "Destructive operation"
2. **Explain**: What/where/why
3. **Confirm**: Get explicit user OK
4. **Alternative**: Offer backup/safer approach

**Never execute without confirmation.**

---

## Output Standards

- **Thinking trace** (Medium/Complex only)
- Clear diagnostics
- Commands with inline comments
- Reference applied skill(s)
- **Confidence score** (Complex decisions)

Example:
```bash
# Applied: bash skill
readonly IN="${1}"
[[ -n "${IN}" ]] || { echo "Error: input required" >&2; exit 1; }
```

---

## Shell Selection

**Default**: Nushell (structured data processing, cross-platform)
**Alternative**: Bash (POSIX compatibility, system scripts)

### When to use Nushell
- Structured data operations (CSV, JSON, YAML parsing/transformation)
- Complex data pipelines with filtering and aggregation
- Cross-platform scripts (Windows, macOS, Linux)
- Type-safe shell scripting

### When to use Bash
- POSIX compliance required (strict sh compatibility)
- System service management (systemd, init scripts)
- Legacy environment support
- Maximum portability to minimal Unix systems

### Examples

**Nushell** (structured data):
```nushell
# Parse CSV, filter, and export to JSON
open data.csv 
| where age > 30 
| select name email department 
| to json 
| save filtered.json

# Pipeline with error handling
do { 
  http get https://api.example.com/data 
} | complete 
| if $in.exit_code != 0 { 
    error make {msg: "API request failed"} 
  } else { 
    $in.stdout | from json 
  }
```

**Bash** (system operations):
```bash
# Service management with validation
readonly SERVICE="nginx"
systemctl restart "${SERVICE}"
systemctl is-active --quiet "${SERVICE}" || {
  echo "ERROR: ${SERVICE} failed to start" >&2
  journalctl -u "${SERVICE}" -n 50
  exit 1
}
```

### Interoperability

Nushell can invoke Bash commands using `^` prefix or `bash -c`:
```nushell
# Call external POSIX command
^ls -la /var/log

# Execute bash script
bash -c 'source /etc/profile && echo $PATH'

# Pipe to/from bash
ls | where size > 1mb | each { |file| ^gzip $file.name }
```

---

## Language

- **Default**: Japanese (polite, professional)
- **Agent input**: English (for token efficiency)
- **Execution modes**: Simple | Medium | Complex | Ambiguous (clarify first)

---

## Quick Reference

### Naming
- Files: `lowercase_snake_case` (except README.md, SKILL.md)
- Code: `snake_case` (vars/funcs), `UPPER_SNAKE` (consts), `PascalCase` (classes)

### Python
- Manager: `uv` (mandatory)
- Install: `uv pip install <pkg>`
- Venv: `uv venv`
- Run: `uv run <script>`

### Skill Format
- **Aim**: 1-3 line purpose
- **Core**: 3-5 key principles
- **Do**: Concrete rules + examples
- **Edge**: When to deviate
- **Refs**: `[Source] (YYYY-MM-DD) - URL`

---

**Last updated**: 2025-02-13

<!-- Anti-sycophancy v1.0 - 3-layer defense integrated -->
