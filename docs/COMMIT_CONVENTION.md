# Commit Message Convention

This repository follows the [Conventional Commits](https://www.conventionalcommits.org/) specification. All messages must be concise, imperative, and in English.

## Format

```text
<type>[optional scope][!]: <description>

[optional body]

[optional footer(s)]
```

- Scope is optional; when used keep it a short, lowercase noun (e.g., `auth`, `api`, `deps`).
- Description starts with a lowercase letter and uses the imperative mood.
- Keep the header concise (preferably **50 characters** or fewer).
- Wrap the body at **72 characters**.
- Leave a blank line between header and body.
- Do not end the header with a period (`.`).

## Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code (white-space, formatting, etc)
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `build`: Changes that affect the build system or external dependencies (npm, make, etc)
- `ci`: Changes to our CI configuration files and scripts (GitHub Actions, Travis, etc)
- `chore`: Other changes that don't modify src or test files

## Rules

1. Write commit messages in English.
2. Use imperative, present tense ("add", "fix", "refactor").
3. Start descriptions with lowercase and avoid trailing periods.
4. Keep scope meaningful; omit it if it adds no clarity.
5. Separate the header from the body with a blank line when a body is present.

## Breaking Changes

- Mark the header with `!` after the type or scope (e.g., `feat!:`, `fix(api)!:`).
- Include a `BREAKING CHANGE:` footer explaining what changed and why.

## Examples

### Standard Feature

```text
feat(auth): add user authentication module
```

### Bug Fix with Body

```text
fix(api): handle null pointer in /users endpoint

The previous implementation caused a crash when the user ID was missing.
This change adds a nil check before accessing the database.
```

### Breaking Change

```text
feat(api)!: remove deprecated v1 endpoints

BREAKING CHANGE: The v1 endpoints under /api/v1 have been removed.
Please migrate to /api/v2 structure.
```

### Documentation

```text
docs: update installation guide in README
```
