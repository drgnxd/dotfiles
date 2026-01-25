# SKILL Template

Use this template when creating new Agent Skills.

Language note: Write all content in English, including headings, examples, and inline text.

---

```markdown
---
name: your_skill_name
description: Brief description of when and why to use this skill (1-2 lines)
license: Apache-2.0
metadata:
  author: your_organization
  version: "1.0.0"
  category: coding|writing|analysis|meta|finance|other
---

# [Skill Display Name]

Brief overview of what this skill provides (2-3 sentences).

## Purpose

Clearly state:
- What problem this skill solves
- When it should be used
- What value it provides

Example:
> This skill standardizes file naming conventions across projects, improving discoverability and reducing cognitive load when navigating codebases.

---

## Core Principles

List 3-5 fundamental principles this skill follows:

1. **[Principle 1]**: Brief explanation
2. **[Principle 2]**: Brief explanation
3. **[Principle 3]**: Brief explanation
4. **[Principle 4]**: Brief explanation (optional)
5. **[Principle 5]**: Brief explanation (optional)

---

## Rules and Standards

### [Section 1: Primary Topic]

#### [Subsection if needed]

**Rule**: State the rule clearly and concisely.

**Examples**:
```
✅ Good:
[Concrete example of correct usage]

❌ Bad:
[Concrete example of what to avoid]
```

**Rationale**: Explain why this rule matters (1-2 sentences).

---

### [Section 2: Secondary Topic]

(Repeat structure as needed)

---

## Decision Framework

When multiple approaches are valid, provide decision criteria:

```
Scenario A (specific condition):
  → Use Approach X
  Reason: [...]

Scenario B (different condition):
  → Use Approach Y
  Reason: [...]

Default:
  → Use Approach Z
  Reason: [...]
```

---

## Examples

### Example 1: [Common Use Case]

**Context**: Describe the situation

**Input/Request**:
```
[What user asks for or provides]
```

**Output/Result**:
```
[Expected output following this skill]
```

**Explanation**: Why this approach is correct

---

### Example 2: [Edge Case]

(Repeat structure for additional examples)

---

## Edge Cases and Exceptions

### Case 1: [Unusual Scenario]
- **Situation**: When X happens
- **Handling**: Apply Y approach instead
- **Reason**: Because Z

### Case 2: [Another Exception]
- **Situation**: When A condition is met
- **Handling**: Use B modification
- **Reason**: Due to C constraint

---

## Related Skills

- `related_skill_1`: How it relates to this skill
- `related_skill_2`: How it relates to this skill

---

## References

### Official Documentation
- [Name of Standard/Framework](https://example.com)

### Industry Best Practices
- [Authority/Organization](https://example.com)

### Internal Resources
- See [detailed_guide](doc/detailed_guide.md) for advanced usage
- Template available at [tpl_file](doc/tpl.txt)

---

## Notes on Template Usage

### Required Sections
- YAML front matter
- Purpose
- Core Principles (at least 3)
- Rules and Standards (at least 1 section)

### Optional but Recommended
- Decision Framework (if multiple approaches exist)
- Examples (2-3 practical examples)
- Edge Cases (if applicable)
- Related Skills (for discoverability)

### Optional Sections
- References (external links)

### Size Management

If content exceeds 500 lines:
1. Keep core rules in SKILL.md
2. Move detailed examples to `doc/ex.md`
3. Move templates to `doc/tpls/`
4. Reference them using relative paths

Example:
```markdown
For comprehensive examples, see [doc/detailed_ex.md](doc/detailed_ex.md)
```
