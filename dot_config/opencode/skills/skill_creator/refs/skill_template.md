# Reference: Skill Blueprint (Compliant with V5 Protocol)

## 1. Top-Level Design
- **Identity**: Task-focused. Avoid personality bloat to prevent performance degradation.
- **Rules**: Must be a subset of the GLOBAL OPERATIONAL PROTOCOL.

## 2. SKILL.md Components
- **Constraints**: Define what the AI *cannot* do (e.g., skip tests, use conversational fillers).
- **Interaction**: Define `@command` aliases for common workflows.
- **Thinking Checklist**: Specific questions the AI must ask itself in the `<thinking>` block.

## 3. Scripting Standards (bin/)
- **Robustness**: Include try/catch and explicit error messages.
- **Hermeticity**: Use relative paths or verify via `pwd`/`ls` before execution.
