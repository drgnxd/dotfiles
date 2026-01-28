---
name: rust
description: Rust conventions for idiomatic, safe code
---

# Rust

## Purpose
Rust-specific guidelines for safe, idiomatic, maintainable code.

## Core Principles
1. Leverage ownership & borrowing for safety
2. Explicit error handling > panics
3. Use standard tooling for formatting & linting

## Rules

### Style & Tooling
- Format w/ `rustfmt`
- Run `clippy`, address correctness warnings
- Use modules for clear scope & visibility

### Error Handling
- Prefer `Result` & `Option` over `unwrap` in production
- Add context w/ `thiserror` or `anyhow` when appropriate

### Performance
- Avoid premature optimization; measure w/ benchmarks
- Use iterators & slices vs manual indexing when possible

## Examples

✅ "Return `Result`, propagate errors w/ `?`"
❌ "Call `unwrap()` in code paths that can fail"

## Edge Cases
- Tests or prototypes: `unwrap` acceptable w/ comment
- Unsafe code: doc invariants & required conditions

See `COMMON.md`.

Refs: [Rust book](https://doc.rust-lang.org/stable/book/), [dev tools](https://doc.rust-lang.org/book/appendix-04-useful-development-tools.html), [clippy](https://doc.rust-lang.org/clippy/) (2026-01-26)
