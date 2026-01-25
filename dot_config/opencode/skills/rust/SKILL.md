---
name: rust
description: Rust conventions for idiomatic and safe code
license: Apache-2.0
metadata:
  author: opencode
  version: "1.0.0"
  category: coding
---

# Rust

## Purpose

Define Rust-specific guidelines for writing safe, idiomatic, and maintainable code.

## Core Principles

1. Leverage ownership and borrowing to enforce safety.
2. Prefer explicit error handling over panics.
3. Use standard tooling for formatting and linting.

## Rules/Standards

### Style and Tooling

- Format code with `rustfmt`.
- Run `clippy` and address warnings that impact correctness.
- Use modules to keep scope and visibility clear.

### Error Handling

- Prefer `Result` and `Option` over `unwrap` in production code.
- Add context to errors using `thiserror` or `anyhow` when appropriate.

### Performance

- Avoid premature optimization; measure with benchmarks.
- Use iterators and slices instead of manual indexing when possible.

## Examples

Good:
- "Return `Result` and propagate errors with `?`."

Bad:
- "Call `unwrap()` in code paths that can fail."

## Edge Cases

- In tests or prototypes, `unwrap` can be acceptable with a comment.
- For unsafe code, document invariants and required conditions.


Naming follows `default_naming_conventions/doc/naming_protocol.md` (language/framework conventions take precedence).

## References

Last accessed: 2026-01-25

- https://doc.rust-lang.org/stable/book/
- https://doc.rust-lang.org/book/appendix-04-useful-development-tools.html
- https://doc.rust-lang.org/clippy/
