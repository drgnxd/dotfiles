---
name: memory
description: Use when maintaining, migrating, importing, exporting, or diagnosing the persistent local memory store.
---

# Persistent Memory

The persistent local memory store is accessed only through `memory-read`,
`memory-append`, `memory-maintain`, `memory-export`, `memory-import`, and
`memory-rescope-legacy`. Never hardcode storage paths, access its files
directly, or run git against it.

## Read And Append

- Use `memory-read --query "<short task description>"` when earlier context is
  needed. It includes global and current-project memory within a context budget.
- Use `--scope global` to exclude project memory. Use `--all` only for
  diagnosis or an explicit whole-store review.
- Append one concise, self-contained, durable, non-sensitive fact at a time.
- Run `memory-append` from the active project. Use `--scope global` only for
  cross-project preferences. Use `--pin` only for a tiny set of facts that must
  always enter context.

## Maintenance

When `memory-read` reports that maintenance is due:

1. Run `memory-read --maintenance`.
2. Review the active JSONL projection for the current global and project scope.
3. Preserve every record that should remain active, keeping its `memory_id` and
   `scopes`. Omit only records that should be retracted. Give new records
   explicit `scopes`. Omitting an existing record from the maintenance input
   retracts it.
4. Pass the edited JSONL projection through standard input and pass the
   generation token as the sole positional argument:

   ```sh
   memory-maintain "<generation>" < edited-projection.jsonl
   ```

5. If the generation changes, repeat the maintenance read.

Maintenance appends update and retraction events; it never rewrites history.

## Import And Export

- Use `memory-export --output <new-directory>` for a portable bundle.
- Before importing unfamiliar data, run `memory-import <jsonl-or-bundle> --dry-run`.
- Use `memory-rescope-legacy` only for explicit legacy project migration.
