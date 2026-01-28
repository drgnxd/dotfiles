---
name: javascript
description: JavaScript & TypeScript conventions
---

# JavaScript

## Purpose
Language-specific guidelines for reliable JS/TS codebases.

## Core Principles
1. Clarity > terseness
2. Modern features, avoid deprecated patterns
3. Explicit, predictable async code

## Rules

### Syntax & Style
- Prefer `const` & `let` over `var`
- Strict equality: `===`, `!==`
- Small, descriptive functions

### Types & Safety
- Use TS types for public APIs when available
- Avoid `any` unless absolutely necessary
- Validate external data before use

### Async Code
- Prefer `async/await` over nested callbacks
- Handle rejected promises explicitly

## Examples

✅ "`async/await` w/ explicit error handling"
❌ "Chain promises w/o handling rejections"

## Edge Cases
- Legacy code: match existing patterns, migrate gradually
- Runtime constraints: doc any polyfills required

See `COMMON.md`.

Refs: [Strict equality](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Strict_equality), [const](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/const), [let](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/let), [TS handbook](https://www.typescriptlang.org/docs/handbook/intro.html) (2026-01-26)
