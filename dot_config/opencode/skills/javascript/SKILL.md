---
name: javascript
description: JavaScript & TypeScript conventions
---

# JavaScript

Aim:
Language-specific guidelines for reliable JS/TS codebases.

Core:
1. Clarity > terseness
2. Modern features, avoid deprecated patterns
3. Explicit, predictable async code

Do:

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

Refs: See doc/refs.md
