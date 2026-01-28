---
name: deep_research
description: Systematic research workflow for evidence synthesis & reporting
---

# Deep Research

Repeatable workflow for complex questions requiring evidence synthesis & structured reporting.

## Purpose
- Scoped, multi-phase research
- Gather & evaluate diverse sources w/ quality checks
- Synthesize into themes, patterns, gaps, recommendations
- Traceable citations

## Core Principles
1. **Scope First**: Define questions, criteria, constraints before search
2. **Source Diversity**: Multiple independent sources, prefer primary
3. **Evidence Grading**: Record recency, authority, confidence
4. **Synthesis > Summary**: Themes, patterns, gaps
5. **Reproducibility**: Track inputs, queries, decisions

## Rules

### Scope Definition
Capture main question, subquestions, success criteria, constraints, deliverables before search.

See `doc/research_plan_template.md`.

### Source Collection
Collect 10-15+ sources across categories (official docs, academic, benchmarks, practitioner reports). Record author, date, link.

### Source Evaluation
Score each for currency, relevance, authority, accuracy, purpose. Summarize confidence.

See `doc/source_evaluation.md` (CRAAP framework).

### Deep Dive
Prioritize where importance & uncertainty high. Use citation chaining & triangulation.

### Synthesis
Group by theme, identify patterns, capture gaps w/ confidence levels.

See `doc/findings_template.md`.

### Reporting
Executive summary, methodology, findings, comparisons, recommendations, risks, references.

Use `doc/final_report_template.md`.

### Automation (Optional)
Scripts = helpers, not substitutes. Doc assumptions & inputs.

## Decision Framework

```
High impact, ambiguous, controversial:
  → Full deep research workflow

Well-known, low impact:
  → Lightweight scan, cite 2-3 sources

Time constrained:
  → Full workflow but reduced depth, doc limitations
```

## Examples

### Tech Evaluation
Compare Next.js vs Remix for SSR → structured report w/ scope, benchmarks, ecosystem, decision matrix, recommendations.

### Market Research
AI coding assistant market → report w/ market signals, vendor positioning, trend analysis, confidence levels, gaps.

## Edge Cases
- Limited sources: doc gap, lower confidence, avoid strong recs
- Conflicting evidence: present competing views, explain weighting
- Paywalled: use abstracts/secondary, note limitations
- Tight deadlines: reduce depth, keep methodology & limitations explicit

Related: `thinking_framework`, `documentation`, `security_experts`

See `COMMON.md`.

Tools: `bin/search_and_analyze.py`, `bin/synthesize.py`, `bin/report_generator.py`

Refs: [CRAAP](https://libguides.csuchico.edu/craap), [PRISMA](https://prisma-statement.org/) (2026-01-26)
