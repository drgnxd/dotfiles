---
name: skills-creator
description: Meta-skill for creating new Agent Skills following agentskills.io specification. Use when user requests creation of a new skill or asks how to structure skills.
license: Apache-2.0
metadata:
  author: drgnxd
  version: "1.0.0"
  category: meta
---

# Skills Creator

A meta-skill that guides the creation of new Agent Skills according to the official agentskills.io specification and Anthropic best practices.

## Purpose

This skill ensures consistency, quality, and compliance with Agent Skills standards when creating new skills for `.config/opencode/skills/`.

---

## Core Principles

1. **Progressive Disclosure**: Skills are discovered by name/description first, then loaded fully only when needed
2. **Self-Contained**: Each skill should be independent and focused on a single responsibility
3. **Practical**: Include concrete examples and actionable guidance
4. **Maintainable**: Keep SKILL.md under 500 lines; use doc/ for detailed content
5. **Standards-Compliant**: Follow agentskills.io specification strictly

---

## Creation Process

### Phase 1: Requirements Analysis (Chain-of-Thought)

Before creating a skill, clarify:

1. **Purpose**: What problem does this skill solve?
2. **Scope**: Is it focused on a single responsibility?
3. **Uniqueness**: Does it overlap with existing skills?
4. **Structure**: Does it need bin/doc/share?

### Phase 2: Structure Design (Tree-of-Thoughts)

Evaluate structure patterns:

**Pattern A: Minimal (Guidelines Only)**
```
skill_name/
└── SKILL.md
```
*Use when*: Simple rules, standards, or processes

**Pattern B: With Doc**
```
skill_name/
├── SKILL.md
└── doc/
    ├── ex.md
    └── tpl.md
```
*Use when*: Detailed examples or templates needed

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
*Use when*: Executable code or automation required

### Phase 3: Content Creation

Use the template from `doc/tpl.md` to create SKILL.md.

---

## SKILL.md Structure Requirements

### Mandatory YAML Front Matter

```yaml
---
name: skill_name                    # snake_case, max 64 chars
description: Brief description      # When to use this skill (1-2 lines)
license: Apache-2.0                 # Or appropriate license
metadata:
  author: organization-name
  version: "1.0.0"                  # Semantic versioning
  category: coding|writing|meta     # Optional but recommended
---
```

### Recommended Markdown Sections

1. **Purpose** (必須): What problem this skill solves
2. **Core Principles** (推奨): 3-5 fundamental rules
3. **Rules/Standards** (必須): Specific, actionable guidelines
4. **Examples** (推奨): Concrete use cases with ✅/❌ patterns
5. **Edge Cases** (optional): Exceptions and special situations
6. **References** (optional): Links to official docs or related skills

### Language Requirements

- Write all newly created skills in English.
- Apply this to `SKILL.md`, `doc/`, and any examples or inline text.


## Naming Conventions

### Directory Names
- **Format**: lowercase, underscore-separated (snake_case)
- **Length**: Maximum 64 characters
- **Characters**: ASCII only, no spaces or special chars except underscores

```
✅ Good:
naming_conventions
api_design_patterns
error_handling_guide

❌ Bad:
NamingConventions      (PascalCase)
naming-conventions     (kebab-case discouraged)
nc                     (too short/ambiguous)
命名規則               (non-ASCII)
```

### File Names
- **Format**: lowercase, snake_case
- **Length**: Short and clear (ex, pat, tpl)
- **Exception**: `SKILL.md` is fixed by spec

```
✅ Good:
doc/ex.md
doc/tpl.md
doc/pat.md

❌ Bad:
doc/examples.md
doc/template-basic.md
doc/Template.md
```

### Optional Category Prefixes

For large skill sets, use prefixes:

```
coding_naming_conventions
coding_error_handling
writing_style_guide
finance_valuation_methods
```

---

## Size and Content Guidelines

### SKILL.md Limits

- **Target**: < 500 lines
- **Maximum**: ~5000 tokens for main instructions
- **Strategy**: Move detailed content to `doc/`

### When to Split Content

If SKILL.md exceeds 500 lines:

```
BEFORE:
skill_name/
└── SKILL.md (800 lines)

AFTER:
skill_name/
├── SKILL.md (300 lines - core guidelines)
└── doc/
    ├── detailed_ex.md (300 lines)
    └── adv_patterns.md (200 lines)
```

Reference from SKILL.md:
```markdown
For detailed examples, see [doc/detailed_ex.md](doc/detailed_ex.md)
```

---

## File Reference Rules

### Relative Paths

Always use skill-root relative paths:

```markdown
✅ Correct:
See [template](doc/tpl.md)
Run script: bin/validator.py

❌ Incorrect:
See [template](/absolute/path/tpl.md)
See [template](../other-skill/file.md)
```

### Nesting Depth

Keep doc references 1 level deep from SKILL.md:

```
✅ Good:
doc/ex.md
bin/helper.py

❌ Discouraged:
doc/sub_dir/deep/file.md
```

---

## Bin Directory Best Practices

When including `bin/`:

1. **Self-Contained**: Each script should work independently
2. **Documented**: Include usage instructions in SKILL.md or script docstring
3. **Error Handling**: Handle edge cases gracefully
4. **Dependencies**: Clearly document required libraries/tools

Example reference in SKILL.md:

```markdown
## Usage

Run the validation script:
```bash
python bin/validator.py --input data.csv
```

Dependencies:
- Python 3.8+
- pandas
```

---

## Quality Checklist

Before finalizing a skill:

### Structure
- [ ] YAML front matter is complete and valid
- [ ] name follows snake_case convention (legacy kebab-case allowed)
- [ ] description clearly states when to use this skill
- [ ] SKILL.md is under 500 lines

### Content
- [ ] Purpose section explains the problem solved
- [ ] Rules are specific and actionable
- [ ] Examples include both ✅ good and ❌ bad patterns
- [ ] File references use relative paths
- [ ] No redundancy with existing skills

### Consistency
- [ ] Follows AGENTS.md principles
- [ ] Compatible with existing skills
- [ ] Uses progressive disclosure (essential info first)

### Usability
- [ ] Understandable by first-time users
- [ ] Includes practical examples
- [ ] Edge cases are addressed

---

## Self-Verification (Self-Consistency Check)

After creation, verify:

```
Q1: Does this skill have a single, clear responsibility?
→ YES/NO + reason

Q2: Is the content specific enough to be actionable?
→ YES/NO + areas to improve

Q3: Does it conflict with other skills or AGENTS.md?
→ YES/NO + conflicts to resolve

Q4: (Counterfactual) What if user misinterprets this rule?
→ Sections needing clarification

Q5: (Counterfactual) What if an edge case X occurs?
→ Missing handling procedures
```

---

## Common Skill Types

### Type 1: Standards & Conventions
**Examples**: naming_conventions, code_structure, documentation_standards

**Characteristics**:
- Clear rules with examples
- ✅/❌ pattern demonstrations
- Minimal need for bin/

### Type 2: Workflow & Processes
**Examples**: code_review_process, deployment_checklist, git_workflow

**Characteristics**:
- Step-by-step procedures
- Decision trees
- Checklists

### Type 3: Templates & Generators
**Examples**: readme_template, api_documentation, test_template

**Characteristics**:
- Reusable templates in doc/
- Customization points clearly marked
- May include generation bin/ utilities

### Type 4: Analysis & Decision Frameworks
**Examples**: architecture_decision, performance_optimization, risk_assessment

**Characteristics**:
- Evaluation criteria
- Scenario comparison tables
- Weighted decision matrices

Naming follows `default_naming_conventions/doc/naming_protocol.md` (language/framework conventions take precedence).

## References

Last accessed: 2026-01-25

- https://agentskills.io/specification
- https://github.com/agentskills/agentskills
- https://agentskills.io/home
- https://raw.githubusercontent.com/agentskills/agentskills/main/README.md
