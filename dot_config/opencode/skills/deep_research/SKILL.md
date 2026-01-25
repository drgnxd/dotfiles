---
name: deep_research
description: Systematic deep research workflow for scoping, gathering, evaluating, synthesizing, and reporting evidence.
---

# Deep Research

This skill defines a repeatable deep research workflow for complex questions that require evidence synthesis and structured reporting. It emphasizes source quality, transparent reasoning, and actionable recommendations.

## Purpose

- Establish a scoped, multi-phase research process.
- Gather and evaluate diverse sources with explicit quality checks.
- Synthesize findings into themes, patterns, gaps, and recommendations.
- Produce reports with traceable citations.

## Core Principles

1. **Scope First**: Define research questions, success criteria, and constraints before searching.
2. **Source Diversity**: Collect multiple independent sources and prefer primary materials.
3. **Evidence Grading**: Record recency, authority, and confidence for each source.
4. **Synthesis Over Summary**: Turn findings into themes, patterns, and gaps.
5. **Reproducibility**: Track inputs, queries, and decisions for reuse.

## Rules/Standards

### Scope Definition

**Rule**: Capture the main question, subquestions, success criteria, constraints, and deliverables before search.

**Examples**:
```
Good:
Research Question: "Which framework fits our SSR migration?"
Subquestions: performance, DX, ecosystem
Constraints: 2-week deadline, JavaScript team only

Bad:
"Compare frameworks quickly."
```

**Rationale**: Clear scope prevents research drift and supports reproducibility.
See [research plan template](doc/research_plan_template.md).

---

### Source Collection

**Rule**: Collect at least 10-15 sources across categories (official docs, academic, benchmarks, practitioner reports). Record author, date, and link.

**Examples**:
```
Good:
- 4 official docs, 3 benchmarks, 5 technical articles, 2 community discussions
- Each entry includes author and date

Bad:
- Only blogs from a single vendor
```

**Rationale**: Diverse sources reduce bias and reveal contradictions.

---

### Source Evaluation

**Rule**: Score each source for currency, relevance, authority, accuracy, and purpose. Summarize confidence.

**Examples**:
```
Good:
Source score: 8/10, confidence: High, notes: primary spec with recent update

Bad:
No evaluation or confidence notes
```

**Rationale**: Quality scoring makes evidence weighting explicit.
See [source evaluation](doc/source_evaluation.md).

---

### Deep Dive

**Rule**: Prioritize deep dives where importance and uncertainty are high. Use citation chaining and triangulation.

**Examples**:
```
Good:
- Follow citations for benchmark claims
- Confirm performance claims with 3 independent sources

Bad:
Accepting a single claim without validation
```

**Rationale**: Deep dives resolve critical uncertainty and prevent weak conclusions.

---

### Synthesis

**Rule**: Group findings by theme, identify patterns, and capture knowledge gaps with confidence levels.

**Examples**:
```
Good:
Theme: "Deployment complexity" with 4 supporting sources and medium confidence

Bad:
List findings without organizing or confidence notes
```

**Rationale**: Structured synthesis turns data into insight.
See [findings template](doc/findings_template.md).

---

### Reporting

**Rule**: Produce a report with executive summary, methodology, findings, comparisons, recommendations, risks, and references.

**Examples**:
```
Good:
Includes decision matrix, limitations, and explicit references

Bad:
No methodology section or citations
```

**Rationale**: Reports should be decision-ready and traceable.
Use [final report template](doc/final_report_template.md).

---

### Automation (Optional)

**Rule**: Scripts are helpers, not substitutes for evaluation and synthesis. Document assumptions and inputs.

**Examples**:
```
Good:
bin/search_and_analyze.py used to collect source details, manual review still performed

Bad:
Automation output copied without human review
```

**Rationale**: Human judgment is required for quality control.

## Decision Framework

```
If the question is high impact, ambiguous, or controversial:
  -> Use full deep research workflow
  Reason: requires evidence weighting and synthesis

If the question is well-known and low impact:
  -> Use a lightweight scan and cite 2-3 sources
  Reason: efficiency

If time is constrained:
  -> Use the full workflow but reduce depth and document limitations
  Reason: transparency preserves decision quality
```

## Examples

### Example 1: Technology Evaluation

**Context**: Choose between two web frameworks.

**Input**:
```
"Compare Next.js and Remix for an SSR migration."
```

**Output**:
```
A structured report with scope, benchmarks, ecosystem analysis, a decision matrix,
and recommendations for short- and medium-term adoption.
```

**Explanation**: Uses multi-source evidence and a comparative framework.

---

### Example 2: Market Research

**Context**: Assess AI coding assistant market direction.

**Input**:
```
"Research the AI coding assistant market and key players."
```

**Output**:
```
A report covering market size signals, vendor positioning, and trend analysis,
with explicit confidence levels and data gaps.
```

**Explanation**: Uses trend triangulation and gap analysis.

---

## Edge Cases and Exceptions

- **Limited sources**: Document the gap and lower confidence; avoid strong recommendations.
- **Conflicting evidence**: Present competing views and explain weighting.
- **Paywalled sources**: Use abstracts and secondary sources, noting limitations.
- **Tight deadlines**: Reduce depth but keep methodology and limitations explicit.

## Related Skills

- `thinking_framework`: Structured reasoning and verification steps.
- `documentation`: Clear reporting standards.
- `security_experts`: Security-focused research for risk analysis.

Naming follows `default_naming_conventions/doc/naming_protocol.md` (language/framework conventions take precedence).

## References

### Internal Resources

- See [research methodology](doc/research_methodology.md) for the full workflow.
- Use [citation guide](doc/citation_guide.md) for consistent references.
- Templates: [research plan](doc/research_plan_template.md), [findings](doc/findings_template.md), [final report](doc/final_report_template.md).
- Sample report: [sample research](doc/sample_research.md).

### External References

- https://libguides.csuchico.edu/craap (Last accessed: 2026-01-26)
- https://www.prisma-statement.org/ (Last accessed: 2026-01-26)
