---
name: thinking
description: Adaptive reasoning framework with simple/medium/complex modes, decomposition patterns, confidence scoring, and token-efficient synthesis.
---

# Objective

Maximize reasoning accuracy using structured, hybrid thinking while controlling token overhead.

# Mode Selection

- `simple` mode
  - Triggers: `ls`, `cat`, `show`, `get`, `pwd`, `echo`.
  - Overhead target: 0-3%.
  - Protocol: direct execution.
- `medium` mode
  - Triggers: `create`, `write`, `refactor`, `fix`, `update`, `analyze`, `implement`.
  - Overhead target: 5-8%.
  - Protocol: decompose -> plan -> execute.
- `complex` mode
  - Triggers: `design`, `architect`, `migrate`, `security`, `audit`, `research`, `compare`, `evaluate`.
  - Overhead target: 10-15%.
  - Protocol: full reasoning workflow with alternatives.

# Required Reasoning Patterns

- Decomposition (required for medium and complex):
  - `[ANALYZE] in: X | out: Y | deps: Z | limits: W`
- Approach comparison (required for complex):
  - `[A] description | pros/cons`
  - `[B] description | pros/cons`
  - `[SEL] chosen approach | rationale`
- Execution trace (required for medium and complex):
  - `1. [ACT] action -> [RES] outcome -> [VER] verification`
  - `2. [ACT] next action using prior result -> [RES] -> [VER]`

# Optional Patterns

- Symbolic logic for logic-heavy tasks:
  - `IF cond THEN act ELSE alt`
  - Follow with natural language explanation.
- Variable chaining for multi-step synthesis:
  - `CONC_A` -> `CONC_B` -> `FINAL`.
- Useful transition markers:
  - `wait...`, `therefore...`, `however...`, `verify...`, `given...`

# Confidence Model

- 8-10: three or more sources, verified, edge cases covered.
- 6-7: two sources, solid logic, known unknowns remain.
- 4-5: one source or unresolved contradictions.
- 0-3: speculation without reliable evidence.
- Report format: `[CONF] N/10 - evidence`.

# Token Efficiency

- Prefer symbolic compression where possible.
- Cache prior conclusions by label instead of restating full reasoning.
- Skip verbose internal trace for simple tasks.
- Defer detailed expansion until necessary.

# Override Conditions

- Skip deep reasoning when request is command-only, simple, or emergency.
- Force deep reasoning for security risk, data loss risk, complex logic, or major ambiguity.

# Reference Signals

- HybridMind (2024-12) arXiv:2411.03109
- NLEP (2024-11) arXiv:2409.03186
- SymbCoT (2024-10) arXiv:2410.01754
