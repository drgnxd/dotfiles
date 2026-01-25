# Common Skill Patterns

Reusable patterns for different types of Agent Skills.

Language note: Write all skill content in English, including any new templates and examples.

---

## Pattern 1: Standards & Conventions

**Use Case**: Enforce consistent practices across projects (naming, formatting, structure)

### Structure
```
skill_name/
└── SKILL.md
```

### Key Characteristics
- Clear rules with objective criteria
- ✅/❌ example pairs
- Language-specific sections if needed
- Minimal or no external files

### Template Outline
```markdown
## Core Principles
- List 3-5 fundamental rules

## Standards by Category
### Category 1
- Rule with examples
- ✅ Good example
- ❌ Bad example

### Category 2
(repeat)

## Decision Framework
When to use approach A vs B
```

### Example Skills
- `naming_conventions`
- `code_structure`
- `documentation_standards`
- `commit_message_format`

### Anti-Patterns to Avoid
- ❌ Subjective rules ("make it pretty")
- ❌ Tool-specific shortcuts
- ❌ Overly detailed (> 500 lines)

---

## Pattern 2: Workflow & Process

**Use Case**: Guide multi-step procedures or decision processes

### Structure
```
skill_name/
└── SKILL.md
```

### Key Characteristics
- Step-by-step instructions
- Decision trees or flowcharts (in Markdown)
- Checklists for verification
- Time estimates per step

### Template Outline
```markdown
## Process Steps

### Step 1: [Name]
Duration: X minutes
- [ ] Substep 1
- [ ] Substep 2

### Step 2: [Name]
(repeat)

## Decision Points

If condition A:
  → Take path X
Else if condition B:
  → Take path Y

## Verification Checklist
- [ ] Item 1
- [ ] Item 2
```

### Example Skills
- `code_review_process`
- `deployment_checklist`
- `incident_response`
- `onboarding_workflow`

### Anti-Patterns to Avoid
- ❌ Overly rigid (no room for judgment)
- ❌ Missing time estimates
- ❌ No verification step

---

## Pattern 3: Template Provider

**Use Case**: Provide reusable templates for documents, code, or configurations

### Structure
```
skill_name/
├── SKILL.md
└── doc/
    ├── tpl_basic.md
    ├── tpl_adv.md
    └── ex/
        └── filled_ex.md
```

### Key Characteristics
- Core template in doc/
- Customization instructions in SKILL.md
- Multiple template variants for different needs
- Filled examples showing usage

### Template Outline
```markdown
## Available Templates

### Basic Template
For: [use case]
See: [doc/tpl_basic.md](doc/tpl_basic.md)

### Advanced Template
For: [use case]
See: [doc/tpl_adv.md](doc/tpl_adv.md)

## Customization Guide

### Section [X]
- Replace [PLACEHOLDER] with your [value]
- Optional: Can be removed if [condition]

## Example Usage
See [doc/ex/filled_ex.md](doc/ex/filled_ex.md)
```

### Example Skills
- `readme_tpl`
- `api_doc_tpl`
- `pull_request_tpl`
- `test_plan_tpl`

### Anti-Patterns to Avoid
- ❌ Templates in SKILL.md body (use doc/)
- ❌ No placeholder explanations
- ❌ No filled examples

---

## Pattern 4: Analysis & Decision Framework

**Use Case**: Help make complex decisions with multiple factors

### Structure
```
skill_name/
├── SKILL.md
└── doc/
    └── eval_matrix.md
```

### Key Characteristics
- Weighted criteria for evaluation
- Comparison matrices
- Risk assessment frameworks
- Scenario analysis templates

### Template Outline
```markdown
## Evaluation Criteria

### Criterion 1: [Name]
Weight: [High/Medium/Low]
How to assess: [description]

### Criterion 2: [Name]
(repeat)

## Decision Matrix

| Option | Criterion 1 | Criterion 2 | Total Score |
|--------|-------------|-------------|-------------|
| A      | 8/10        | 6/10        | 70%         |
| B      | 6/10        | 9/10        | 75%         |

## Risk Assessment

For each option, evaluate:
- Likelihood: [Low/Medium/High]
- Impact: [Low/Medium/High]
- Mitigation: [strategy]

## Recommendation Framework

If score > 80%:
  → Proceed with confidence

If score 60-80%:
  → Proceed with caution, monitor risks

If score < 60%:
  → Reconsider or need more analysis
```

### Example Skills
- `architecture_decision`
- `technology_selection`
- `performance_optimization`
- `risk_assessment`

### Anti-Patterns to Avoid
- ❌ Purely subjective criteria
- ❌ No weighting of factors
- ❌ Missing risk analysis

---

## Pattern 5: Code Generation & Automation

**Use Case**: Provide scripts or tools to automate tasks

### Structure
```
skill_name/
├── SKILL.md
├── bin/
│   ├── generator.py
│   └── validator.sh
└── doc/
    ├── usage_ex.md
    └── config.md
```

### Key Characteristics
- Self-contained scripts
- Clear dependency documentation
- Error handling and logging
- Configuration via CLI args or config files

### Template Outline
```markdown
## Overview
What the script does and when to use it

## Installation

Dependencies:
- Tool 1 (version)
- Tool 2 (version)

Installation:
```bash
pip install -r requirements.txt
```

## Usage

Basic usage:
```bash
python bin/generator.py --input data.csv --output result.json
```

Options:
- `--input`: [description]
- `--output`: [description]
- `--verbose`: Enable detailed logging

## Configuration

See [doc/config.md](doc/config.md)

## Examples

See [doc/usage_ex.md](doc/usage_ex.md)

## Troubleshooting

Common errors and solutions
```

### Example Skills
- `csv_validator`
- `api_client_generator`
- `test_data_generator`
- `documentation_builder`

### Anti-Patterns to Avoid
- ❌ Undocumented dependencies
- ❌ No error handling
- ❌ Missing usage examples
- ❌ Hardcoded paths/values

---

## Pattern 6: Language/Framework-Specific

**Use Case**: Best practices for specific programming languages or frameworks

### Structure
```
skill_name/
├── SKILL.md
└── doc/
    ├── pat.md
    └── anti_pat.md
```

### Key Characteristics
- Idiomatic usage for the technology
- Common pitfalls and solutions
- Performance considerations
- Security best practices

### Template Outline
```markdown
## Idioms & Best Practices

### Pattern 1: [Name]
When to use: [scenario]
Example:
```[language]
// Good example
```

### Pattern 2: [Name]
(repeat)

## Common Pitfalls

### Pitfall 1: [Name]
Problem: [description]
Solution: [how to avoid]

## Performance Tips

### Tip 1: [Name]
Impact: [high/medium/low]
When: [scenario]

## Security Considerations

- [ ] Item 1
- [ ] Item 2
```

### Example Skills
- `react_patterns`
- `python_idioms`
- `go_best_practices`
- `sql_optimization`

### Anti-Patterns to Avoid
- ❌ Too generic (not leveraging language features)
- ❌ Outdated patterns
- ❌ No version information

---

## Pattern 7: Domain-Specific Knowledge

**Use Case**: Capture specialized knowledge for a domain (finance, healthcare, etc.)

### Structure
```
skill_name/
├── SKILL.md
└── doc/
    ├── terms.md
    ├── regs.md
    └── formulas.md
```

### Key Characteristics
- Domain terminology definitions
- Industry standards and regulations
- Common calculations or formulas
- Real-world scenarios

### Template Outline
```markdown
## Domain Overview
Brief introduction to the domain

## Key Concepts

### Concept 1: [Name]
Definition: [...]
Example: [...]

### Concept 2: [Name]
(repeat)

## Standard Processes

### Process 1: [Name]
Steps: [...]
Regulations: [...]

## Calculations & Formulas

### Formula 1: [Name]
```
formula = (a + b) / c
```
When to use: [...]
Example: [...]

## Compliance Requirements

- [ ] Requirement 1
- [ ] Requirement 2

## References

Industry standards:
- [Standard name](URL)

Regulatory bodies:
- [Organization name](URL)
```

### Example Skills
- `financial_valuation`
- `medical_terminology`
- `legal_document_review`
- `manufacturing_quality`

### Anti-Patterns to Avoid
- ❌ Outdated regulations
- ❌ No source citations
- ❌ Overly technical without examples

---

## Choosing the Right Pattern

### Decision Tree

```
Is it about code/file organization?
  → Pattern 1: Standards & Conventions

Is it a multi-step procedure?
  → Pattern 2: Workflow & Process

Does it provide reusable boilerplate?
  → Pattern 3: Template Provider

Does it help make complex decisions?
  → Pattern 4: Analysis & Decision Framework

Does it automate a task?
  → Pattern 5: Code Generation & Automation

Is it specific to a language/framework?
  → Pattern 6: Language/Framework-Specific

Is it specialized domain knowledge?
  → Pattern 7: Domain-Specific Knowledge
```

---

## Hybrid Patterns

Skills can combine patterns. Examples:

### Standards + Templates
```
skill_name/
├── SKILL.md (standards)
└── doc/
    └── tpl.md (template)
```

### Workflow + Automation
```
skill_name/
├── SKILL.md (workflow)
├── bin/
│   └── automate.py (automation)
└── doc/
    └── ex.md
```

### Decision Framework + Domain Knowledge
```
skill_name/
├── SKILL.md (decision framework)
└── doc/
    ├── domain_concepts.md (domain knowledge)
    └── eval_criteria.md
```

---

## Pattern Evolution

As skills mature:

1. **Start Simple**: Begin with Pattern 1 (Standards)
2. **Add Examples**: Move to doc/ when > 500 lines
3. **Add Automation**: Introduce bin/ if repetitive tasks emerge
4. **Add Templates**: Create doc/tpls/ for boilerplate
5. **Refine Decision Logic**: Develop into Pattern 4 if needed

---

## Pattern Selection Checklist

Before choosing a pattern:

- [ ] What is the primary purpose?
- [ ] Who is the target user?
- [ ] How often will it be used?
- [ ] Does it need automation?
- [ ] Will it need frequent updates?
- [ ] Are there existing examples to reference?

---

**Last Updated**: 2024-01-25
