---
name: docker_experts
description: Docker builds & container ops best practices
---

# Docker Experts

## Purpose
Secure, efficient container images & safe ops.

## Core Principles
1. Minimal, reproducible images
2. Non-root execution when possible
3. Explicit, auditable runtime config

## Rules

### Dockerfile
- Slim base images, pin versions
- Multi-stage builds to reduce size
- Never copy secrets into images

### Runtime
- Explicit env vars & volumes
- Read-only mounts for immutable data
- Health checks for long-running services

### Compose & Orchestration
- Doc service dependencies clearly
- Separate dev settings from production

## Examples

✅ "Multi-stage build, drop build tools from final image"
❌ "Run as root, bake credentials into image"

## Edge Cases
- Root required: doc why, reduce capabilities
- Large images: explain tradeoff, monitor pull times

See `COMMON.md`.

Refs: [Best practices](https://docs.docker.com/build/building/best-practices/), [Dockerfile ref](https://docs.docker.com/reference/dockerfile/) (2026-01-26)
