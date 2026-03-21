---
name: infrastructure
description: Infrastructure operations guidance for git workflow, Docker hardening, Linux administration, database migrations, and security controls.
---

# Git Workflow

- Use feature branches.
- Do not commit directly to protected branches.
- Use rebase workflows only on private/unshared branches.
- Keep commits scoped to one logical change.
- Write commit messages that explain intent.
- Never commit secrets.
- Preferred flow: inspect with status/diff -> stage intentionally -> sync with pull before push -> resolve conflicts locally.

# Docker

- Prefer slim, pinned base images.
- Use multi-stage builds to reduce runtime attack surface.
- Never bake secrets into images.
- Run as non-root where possible.
- At runtime, set explicit environment variables and volume mappings.
- Prefer read-only mounts where feasible.
- Define health checks for service containers.

# Linux Operations

- Apply least privilege by default.
- Keep operational changes reversible.
- Validate state before and after changes.
- For config changes: check current state, apply targeted updates, and back up configuration first.
- After service restarts, verify process health and inspect logs.

# Database

- Schema: consistent naming, explicit primary keys, explicit indexes, documented relationships.
- Querying: index frequent access paths, avoid full table scans when possible, inspect query plans.
- Migrations: additive-first rollout, backfill in batches, remove deprecated columns/tables only after all consumers migrate.

# Security

- Secrets: never hardcode, use a secret manager, rotate immediately if exposed.
- Input/output: validate and sanitize all inputs; encode outputs in target context.
- Dependencies: track third-party packages, update regularly, and avoid unmaintained dependencies.
