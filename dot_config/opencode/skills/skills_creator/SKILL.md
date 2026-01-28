---
name: skills_creator
description: Meta-skill for creating Agent Skills per agentskills.io spec
---

# Skills Creator

Ensures consistency, quality, compliance when creating skills for `.config/opencode/skills/`.

## Purpose
Consistent skill creation following agentskills.io standards & Anthropic best practices.

## Core Principles
1. **Progressive Disclosure**: Discovered by name/description, loaded when needed
2. **Self-Contained**: Independent, single responsibility
3. **Practical**: Concrete examples & actionable guidance
4. **Maintainable**: SKILL.md < 500 lines; use `doc/` for details
5. **Standards-Compliant**: Follow agentskills.io spec

## Creation Process

### Phase 1: Requirements
Clarify:
1. Purpose: What problem does this solve?
2. Scope: Single responsibility?
3. Uniqueness: Overlaps w/ existing skills?
4. Structure: Needs `bin/doc/share`?

### Phase 2: Structure

**Pattern A: Minimal (Guidelines Only)**
```
skill_name/
└── SKILL.md
```
Use when: Simple rules, standards, processes

**Pattern B: With Doc**
```
skill_name/
├── SKILL.md
└── doc/
    ├── ex.md
    └── tpl.md
```
Use when: Detailed examples or templates needed

**Pattern C: With Scripts**
```
skill_name/
├── SKILL.md
├── bin/
│   └── helper.py
├── doc/
│   └── usage.md
└── share/
    └── templates/
```
Use when: Executable code or automation required

### Phase 3: Content
Use template from `doc/tpl.md`.

## SKILL.md Structure

### Mandatory YAML Front Matter
```yaml
---
name: skill_name              # snake_case, max 64 chars
description: Brief when-to-use  # 1-2 lines
---
```

### Recommended Sections
1. **Purpose** (必須): Problem this solves
2. **Core Principles** (推奨): 3-5 fundamental rules
3. **Rules/Standards** (必須): Specific, actionable guidelines
4. **Examples** (推奨): Concrete ✅/❌ patterns
5. **Edge Cases** (optional): Exceptions & special situations
6. **References** (optional): Official docs or related skills

### Language
Write all new skills in English. Apply to `SKILL.md`, `doc/`, examples, inline text.

### Reference Format
Append `Last accessed: YYYY-MM-DD` to each URL (not shared date line).

## Naming

### Directory Names
- **Format:** lowercase, snake_case
- **Length:** Max 64 chars
- **Chars:** ASCII only, no spaces/special chars except underscores

✅ `naming_conventions`, `api_design_patterns`, `error_handling_guide`
❌ `NamingConventions`, `naming-conventions`, `nc`, `命名規則`

### File Names
- **Format:** lowercase, snake_case
- **Length:** Short & clear (ex, pat, tpl)
- **Exception:** `SKILL.md` fixed by spec

✅ `doc/ex.md`, `doc/tpl.md`, `doc/pat.md`
❌ `doc/examples.md`, `doc/template-basic.md`, `doc/Template.md`

### Optional Category Prefixes
For large skill sets:
```
coding_naming_conventions
coding_error_handling
writing_style_guide
finance_valuation_methods
```

## Size & Content

### SKILL.md Limits
- **Target:** < 500 lines
- **Max:** ~5000 tokens for main instructions
- **Strategy:** Move detailed content to `doc/`

### When to Split
If SKILL.md > 500 lines:
```
BEFORE:
skill_name/
└── SKILL.md (800 lines)

AFTER:
skill_name/
├── SKILL.md (300 lines - core)
└── doc/
    ├── detailed_ex.md (300 lines)
    └── adv_patterns.md (200 lines)
```

Reference: `For detailed examples, see [doc/detailed_ex.md](doc/detailed_ex.md)`

## File References

### Relative Paths
Always use skill-root relative:

✅ `See [template](doc/tpl.md)`, `Run: bin/validator.py`
❌ `See [template](/absolute/path/tpl.md)`, `See [template](../other-skill/file.md)`

### Nesting Depth
Keep doc refs 1 level from SKILL.md:

✅ `doc/ex.md`, `bin/helper.py`
❌ `doc/sub_dir/deep/file.md`

## Bin Directory

When including `bin/`:
1. **Self-Contained:** Each script works independently
2. **Documented:** Usage in SKILL.md or script docstring
3. **Error Handling:** Handle edge cases gracefully
4. **Dependencies:** Doc required libs/tools

Example:
```markdown
## Usage
Run: `python bin/validator.py --input data.csv`

Dependencies: Python 3.8+, pandas
```

## Quality Checklist

### Structure
- [ ] YAML front matter complete & valid
- [ ] `name` follows snake_case (legacy kebab-case allowed)
- [ ] `description` clearly states when to use
- [ ] SKILL.md < 500 lines

### Content
- [ ] Purpose explains problem solved
- [ ] Rules specific & actionable
- [ ] Examples include ✅ good & ❌ bad
- [ ] File references use relative paths
- [ ] No redundancy w/ existing skills

### Consistency
- [ ] Follows AGENTS.md principles
- [ ] Compatible w/ existing skills
- [ ] Uses progressive disclosure

### Usability
- [ ] Understandable by first-time users
- [ ] Practical examples included
- [ ] Edge cases addressed

## Self-Verification

After creation:
```
Q1: Single, clear responsibility? → YES/NO + reason
Q2: Content specific enough? → YES/NO + areas to improve
Q3: Conflicts w/ other skills/AGENTS.md? → YES/NO + resolve
Q4: What if user misinterprets? → Sections needing clarification
Q5: What if edge case X occurs? → Missing handling
```

## Common Skill Types

### Type 1: Standards & Conventions
Examples: naming_conventions, code_structure, documentation_standards
- Clear rules w/ examples
- ✅/❌ pattern demos
- Minimal `bin/` needs

### Type 2: Workflow & Processes
Examples: code_review_process, deployment_checklist, git_workflow
- Step-by-step procedures
- Decision trees
- Checklists

### Type 3: Templates & Generators
Examples: readme_template, api_documentation, test_template
- Reusable templates in `doc/`
- Customization points marked
- May include generation `bin/` utilities

### Type 4: Analysis & Decision Frameworks
Examples: architecture_decision, performance_optimization, risk_assessment
- Evaluation criteria
- Scenario comparison tables
- Weighted decision matrices

See `COMMON.md`.

Related: `thinking_framework`, `documentation`, `security_experts`

See `doc/ex.md`, `doc/pat.md`, `doc/tpl.md` for details.

Refs: [agentskills.io](https://agentskills.io/specification), [repo](https://github.com/agentskills/agentskills) (2026-01-26)
