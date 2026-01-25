---
name: docker_experts
description: Best practices for Docker builds and container operations
---

# Docker Experts

## Purpose

Provide guidance for building secure, efficient container images and operating them safely.

## Core Principles

1. Keep images minimal and reproducible.
2. Prefer non-root execution where possible.
3. Make runtime configuration explicit and auditable.

## Rules/Standards

### Dockerfile

- Use slim base images and pin versions.
- Leverage multi-stage builds to reduce final size.
- Avoid copying secrets into images.

### Runtime

- Define environment variables and volumes explicitly.
- Prefer read-only mounts for immutable data.
- Use health checks for long-running services.

### Compose and Orchestration

- Document service dependencies clearly.
- Separate local development settings from production.

## Examples

Good:
- "Use a multi-stage build and drop build tools from the final image."

Bad:
- "Run everything as root and bake credentials into the image."

## Edge Cases

- If root is required, document why and reduce capabilities.
- If images must be large, explain the tradeoff and monitor pull times.


Naming follows `default_naming_conventions/doc/naming_protocol.md` (language/framework conventions take precedence).

## References


- https://docs.docker.com/build/building/best-practices/ (Last accessed: 2026-01-26)
- https://docs.docker.com/reference/dockerfile/ (Last accessed: 2026-01-26)
- https://docs.docker.com/build/concepts/dockerfile/ (Last accessed: 2026-01-26)
