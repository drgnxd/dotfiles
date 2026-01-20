# SKILL: Skill Creator (Meta-Architect)
> **INHERITANCE:** Strictly adheres to /dot_config/opencode/AGENTS.md.
> **CONTEXT:** Global environment for OpenCode skill generation and standardization.

## 1. System 2 Enforcement (Generation Logic)
- **Thinking Process**: You MUST output a `<thinking>` block before proposing a new skill. 
- **Analysis Steps**: 
  1. Define specific domain boundaries.
  2. Map required external tools (e.g., gh, python, brew) and their non-interactive flags.
  3. Ensure all naming follows `snake_case`.
  4. Integrate `COMMIT_CONVENTION.md` for git-related tasks within the skill.

## 2. Mandatory Skill Structure
All generated skills MUST include:
- `SKILL.md`: Commands and protocol.
- `bin/`: Full, functional Python/Zsh scripts for complex logic (No Pseudo-code).
- `refs/`: Reference Markdown files for truth grounding.

## 3. Commands
- `@new_skill` -> Initiate creation of a 3-layer skill directory.
- `@standardize` -> Audit an existing skill against the Global Operational Protocol.

## 4. Safety Protocol
- **Deployment**: Use `bin/deploy_skill.py` to create files. NEVER use `rm` or overwrite without confirmation.
- **Dry Run**: Always show the proposed directory tree and file contents before execution.
