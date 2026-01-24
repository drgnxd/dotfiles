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
4. **Maintainable**: Keep SKILL.md under 500 lines; use refs/ for detailed content
5. **Standards-Compliant**: Follow agentskills.io specification strictly

---

## Creation Process

### Phase 1: Requirements Analysis (Chain-of-Thought)

Before creating a skill, clarify:

1. **Purpose**: What problem does this skill solve?
2. **Scope**: Is it focused on a single responsibility?
3. **Uniqueness**: Does it overlap with existing skills?
4. **Structure**: Does it need scripts/refs/assets?

### Phase 2: Structure Design (Tree-of-Thoughts)

Evaluate structure patterns:

**Pattern A: Minimal (Guidelines Only)**
```
skill_name/
└── SKILL.md
```
*Use when*: Simple rules, standards, or processes

**Pattern B: With Refs**
```
skill_name/
├── SKILL.md
└── refs/
    ├── ex.md
    └── tpl.md
```
*Use when*: Detailed examples or templates needed

**Pattern C: With Scripts**
```
skill_name/
├── SKILL.md
├── scripts/
│   └── helper.py
└── refs/
    └── usage.md
```
*Use when*: Executable code or automation required

### Phase 3: Content Creation

Use the template from `refs/tpl.md` to create SKILL.md.

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

---

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
refs/ex.md
refs/tpl.md
refs/pat.md

❌ Bad:
refs/examples.md
refs/template-basic.md
refs/Template.md
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
- **Strategy**: Move detailed content to `refs/`

### When to Split Content

If SKILL.md exceeds 500 lines:

```
BEFORE:
skill_name/
└── SKILL.md (800 lines)

AFTER:
skill_name/
├── SKILL.md (300 lines - core guidelines)
└── refs/
    ├── detailed_ex.md (300 lines)
    └── adv_patterns.md (200 lines)
```

Reference from SKILL.md:
```markdown
For detailed examples, see [refs/detailed_ex.md](refs/detailed_ex.md)
```

---

## File Reference Rules

### Relative Paths

Always use skill-root relative paths:

```markdown
✅ Correct:
See [template](refs/tpl.md)
Run script: scripts/validator.py

❌ Incorrect:
See [template](/absolute/path/tpl.md)
See [template](../other-skill/file.md)
```

### Nesting Depth

Keep references 1 level deep from SKILL.md:

```
✅ Good:
refs/ex.md
scripts/helper.py

❌ Discouraged:
refs/sub_dir/deep/file.md
```

---

## Scripts Directory Best Practices

When including `scripts/`:

1. **Self-Contained**: Each script should work independently
2. **Documented**: Include usage instructions in SKILL.md or script docstring
3. **Error Handling**: Handle edge cases gracefully
4. **Dependencies**: Clearly document required libraries/tools

Example reference in SKILL.md:

```markdown
## Usage

Run the validation script:
```bash
python scripts/validator.py --input data.csv
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
- Minimal need for scripts/

### Type 2: Workflow & Processes
**Examples**: code_review_process, deployment_checklist, git_workflow

**Characteristics**:
- Step-by-step procedures
- Decision trees
- Checklists

### Type 3: Templates & Generators
**Examples**: readme_template, api_documentation, test_template

**Characteristics**:
- Reusable templates in refs/
- Customization points clearly marked
- May include generation scripts/

### Type 4: Analysis & Decision Frameworks
**Examples**: architecture_decision, performance_optimization, risk_assessment

**Characteristics**:
- Evaluation criteria
- Scenario comparison tables
- Weighted decision matrices

---

## Version Management

Use Semantic Versioning (MAJOR.MINOR.PATCH):

```
1.0.0 → Initial release
1.1.0 → New rules/sections added (backward compatible)
1.0.1 → Typo fixes, clarifications (backward compatible)
2.0.0 → Breaking changes to existing rules
```

Update changelog in SKILL.md:

```markdown
## Changelog

### [1.1.0] - 2024-02-15
- Added section on error handling patterns
- Extended examples with TypeScript support

### [1.0.0] - 2024-01-25
- Initial release
```

---

## Integration with AGENTS.md

### Precedence Order

When conflicts occur:

1. **AGENTS.md - Safety Protocol** (highest priority)
2. **AGENTS.md - Fundamental Rules**
3. **Individual SKILL.md - Specific Rules**
4. **AGENTS.md - Thinking Architecture** (process guidance)

### Skill Composition

Skills can reference each other:

```markdown
## Related Skills

This skill builds upon:
- `naming_conventions`: For file naming standards
- `code_structure`: For organization principles

See also:
- `error_handling`: For exception handling patterns
```

---

## Deprecation Process

When a skill becomes obsolete:

1. **Add warning to SKILL.md**:
```markdown
> ⚠️ **DEPRECATED**: This skill is deprecated.  
> Use `new_skill_name` instead.  
> Removal date: 2024-12-31
```

2. **Migration period**: 3 months minimum
3. **Archive**: Move to `deprecated/` directory
4. **Remove**: After 6 months total

---

## Anti-Patterns to Avoid

### ❌ Don't:

1. **Overly Generic**: "Write good code" → Too vague
2. **Overly Specific**: Platform-specific shortcuts → Not reusable
3. **Duplicate Existing**: Check existing skills first
4. **Subjective Rules**: "Make it beautiful" → Need objective criteria
5. **Unmaintainable**: External dependencies without fallbacks

### ✅ Do:

1. **Specific & Measurable**: "Functions should have ≤ 3 parameters"
2. **Cross-Platform**: Works across languages/environments where applicable
3. **Unique Value**: Solves a problem not covered elsewhere
4. **Objective Criteria**: Clear pass/fail conditions
5. **Self-Contained**: Minimal external dependencies

---

## Example Creation Flow

**User Request**: "Create a skill for API design standards"

**Process**:

```
[Phase 1: Analysis]
- Purpose: Standardize REST API design
- Scope: Endpoint naming, HTTP methods, response formats
- Structure: SKILL.md + refs/ex.md

[Phase 2: Design]
- Pattern B (with refs) selected
- Need examples of good/bad API designs

[Phase 3: Creation]
- Use template from refs/tpl.md
- Add specific rules for REST conventions
- Include OpenAPI/Swagger references
- Add real-world examples

[Verification]
- Single responsibility? ✓
- Under 500 lines? ✓
- No conflicts? ✓
- Actionable rules? ✓
```

---

## Getting Started

To create a new skill:

1. **Request**: "Create a skill for [topic]"
2. Requirements analyzed using this skills-creator guide
3. **Structure is determined** (minimal/refs/scripts)
4. **Template is populated** from refs/tpl.md
5. **Quality check** is performed
6. **Result is presented** for review

For detailed template, see [refs/tpl.md](refs/tpl.md)  
For examples, see [refs/ex.md](refs/ex.md)  
For common patterns, see [refs/pat.md](refs/pat.md)

---

## Maintenance Schedule

- **Monthly**: Review usage frequency
- **Quarterly**: Update with new best practices
- **Annually**: Comprehensive audit and refactoring

---

**Last Updated**: 2024-01-25
