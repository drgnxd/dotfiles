# Benchmark Reports

This directory stores point-in-time benchmark reports for performance tracking.

## Naming Convention

- Use `YYYY-MM-DD.md` for a single report on that date.
- If multiple reports are needed on the same date, use `YYYY-MM-DD-<slug>.md`.
- Use lowercase ASCII for `<slug>` and separate words with hyphens.

Examples:

- `2026-02-27.md`
- `2026-02-27-nushell-startup.md`

## CI Scope

Benchmark reports are intentionally excluded from EN/JA document pair checks.
The doc-pair-check job validates benchmark filenames against the naming rules above.
