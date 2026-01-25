---
name: database_experts
description: Database design and query optimization guidance
license: Apache-2.0
metadata:
  author: opencode
  version: "1.0.0"
  category: coding
---

# Database Experts

## Purpose

Provide standards for schema design, query performance, and safe database changes.

## Core Principles

1. Model data clearly and normalize where appropriate.
2. Optimize for the most common access patterns.
3. Apply migrations safely with backward compatibility in mind.

## Rules/Standards

### Schema Design

- Use consistent naming for tables and columns.
- Define primary keys and indexes explicitly.
- Document relationships and constraints.

### Query Optimization

- Use indexes for frequent filters and joins.
- Avoid full table scans in latency-sensitive paths.
- Review query plans for hotspots.

### Migrations

- Make additive changes first (new columns, new tables).
- Backfill data in controlled batches.
- Remove deprecated fields only after consumers are updated.

## Examples

Good:
- "Add a new column, backfill in batches, then switch reads."

Bad:
- "Drop a column immediately without coordinating consumers."

## Edge Cases

- For large tables, use online migration strategies.
- For multi-tenant data, verify isolation and indexing.


Naming follows `default_naming_conventions/doc/naming_protocol.md` (language/framework conventions take precedence).

## References


- https://www.postgresql.org/docs/current/indexes.html (Last accessed: 2026-01-26)
- https://www.postgresql.org/docs/current/using-explain.html (Last accessed: 2026-01-26)
- https://www.postgresql.org/docs/current/performance-tips.html (Last accessed: 2026-01-26)
