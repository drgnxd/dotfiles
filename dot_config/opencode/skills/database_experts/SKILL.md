---
name: database_experts
description: DB design & query optimization
---

# Database Experts

Aim:
Standards for schema, query perf, safe migrations.

Core:
1. Model clearly, normalize appropriately
2. Optimize for common access patterns
3. Safe migrations w/ backward compatibility

Do:

### Schema
- Consistent naming for tables/columns
- Explicit PKs & indexes
- Doc relationships & constraints

### Query Optimization
- Index frequent filters/joins
- Avoid full table scans in latency-sensitive paths
- Review query plans for hotspots

### Migrations
- Additive changes first (new cols/tables)
- Backfill in batches
- Remove deprecated only after consumers updated

## Examples

✅ "Add col, backfill batches, switch reads"
❌ "Drop col immediately w/o coordinating consumers"

## Edge Cases
- Large tables: online migration strategies
- Multi-tenant: verify isolation & indexing

Refs: See doc/refs.md
