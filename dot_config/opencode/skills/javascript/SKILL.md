---
name: javascript
description: JavaScript and TypeScript conventions for consistent code
license: Apache-2.0
metadata:
  author: opencode
  version: "1.0.0"
  category: coding
---

# JavaScript

## Purpose

Provide language-specific guidelines for reliable JavaScript and TypeScript codebases.

## Core Principles

1. Prefer clarity over terseness.
2. Use modern language features and avoid deprecated patterns.
3. Keep asynchronous code explicit and predictable.

## Rules/Standards

### Syntax and Style

- Prefer `const` and `let` over `var`.
- Use strict equality (`===`, `!==`).
- Keep functions small and descriptive.

### Types and Safety

- Use TypeScript types for public APIs when available.
- Avoid `any` unless absolutely necessary.
- Validate external data before use.

### Async Code

- Prefer `async/await` over nested callbacks.
- Handle rejected promises explicitly.

## Examples

Good:
- "Use `async/await` with explicit error handling."

Bad:
- "Chain promises without handling rejections."

## Edge Cases

- For legacy code, match existing patterns and migrate gradually.
- For runtime constraints, document any polyfills required.


Naming follows `default_naming_conventions/doc/naming_protocol.md` (language/framework conventions take precedence).

## References

Last accessed: 2026-01-25

- https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Strict_equality
- https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/const
- https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/let
- https://www.typescriptlang.org/docs/handbook/intro.html
