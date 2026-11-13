# Configuration Management Policy

## Core Policy

**Nix-first, native-when-needed.**

Home Manager is the center of configuration management.
Anything Nix expresses naturally is managed in `.nix`.
Where Nix would reduce readability, maintainability, editing efficiency, or functionality, keep the application's native format.

Pursue consistency, brevity, and elegance only where they cost nothing in practicality.

## Decision Flow

Apply the first matching rule.

1. The application has a `programs.*` or `services.*` module with structured options: use it.
2. The content is structured data (TOML, JSON, YAML, KDL values): declare it in Nix and render it with `pkgs.formats.*` or the module's `settings`, never a hand-written string.
3. The content is code (Nushell, Lua, shell, Python) or a format whose tooling matters (completion, LSP, formatter): keep it native under `xdg/` and reference it from the module.
4. The application rewrites the file at run time: deploy it as a writable file (see Writable and Mutable Files).
5. When two options are equally practical, choose the more consistent and shorter one.

The six criteria below break ties inside rules 2 and 3.
Read them in this order: compatibility, editing efficiency, readability, maintainability, reusability, complexity.

1. **Compatibility**: does Nix keep every application-specific feature available?
2. **Editing efficiency**: are completion, LSP, and formatter support kept?
3. **Readability**: does Nix make the intent clearer?
4. **Maintainability**: are changes and dependencies easier to trace?
5. **Reusability**: are shared and per-OS settings simpler to express?
6. **Complexity**: does it avoid abstraction added only for management's sake?

Changing the extension to `.nix` without improving any of these is not a migration.

## Design Principles

### 1. Home Manager Is the Center

- Install and enable applications through Home Manager.
- Express dependencies, environment variables, and per-OS branches in Nix.
- Prefer `programs.*` and `services.*`; use `xdg.configFile` where Home Manager has no module.
- Placement and reproducibility are owned by Home Manager.

### 2. Static Settings Live in Nix

- Themes, fonts, and window settings.
- Simple key bindings and behavior options.
- External commands and tool dependencies.
- Per-OS and per-host differences.

### 3. Programs Keep Their Native Format

- Nushell functions and scripts (`.nu`), Neovim Lua, and Yazi Lua plugins.
- Complex application-specific configuration.
- Anything that benefits from native completion, LSP, or formatters.

Do not embed large native code in `extraConfig` or string literals.
Keep it as a file under `xdg/` and reference it with `source` or `builtins.readFile`.

### 4. One Source of Truth

- Never define the same setting in both Nix and a native file.
- Every application enters through `home/modules/*.nix`.
- Native files are referenced from their module.
- Never edit generated files under `~/.config/`; change the tracked source.

### 5. Declarative Settings and Runtime State Are Separate

Home Manager output can be a read-only symlink into the Nix store.

| Kind | Management |
|---|---|
| Static configuration | Declared in Nix |
| Cache, history, sessions | Owned by the application |
| Settings the application rewrites | Writable file (see below) |
| Secrets | Outside the Git-tracked configuration (see Secrets) |

### 6. Cross-Platform

Share configuration between macOS and Linux and branch per OS in Nix.

```nix
lib.optionalAttrs pkgs.stdenv.isLinux {
  copy_command = "${pkgs.wl-clipboard}/bin/wl-copy";
}
```

- Avoid duplicating shared settings.
- State OS-specific dependencies explicitly.
- Do not hardcode environment-dependent paths, usernames, or hostnames.

## Writable and Mutable Files

Choose the least mutable option that works.

| Need | Mechanism | Reproducibility |
|---|---|---|
| Application writes occasionally and the file can be seeded | Activation-synced real file | Seeded at activation; local edits survive |
| Frequent hand edits where a rebuild per change is too slow | `config.lib.file.mkOutOfStoreSymlink` to a path in the working tree | Edits apply immediately; the file is not in the store |
| Fully application-owned | Not managed; keep in a state or data directory | None, by design |

A runtime-resolved path (Bun resolving imports from realpaths is one example) also requires a real file or an out-of-store symlink rather than a store symlink.

## Secrets

- Secrets are managed with agenix; encrypted files live under `secrets/` and are keyed in `secrets/secrets.nix`.
- Never commit plaintext secrets or private values; private values stay in `local/` or a state directory and are read at run time.
- A public module may declare where a secret is deployed, not what it contains.

## Application Guidance

| Application | Management | Reason |
|---|---|---|
| Zellij | Nix | Static settings dominate; keep layouts native KDL if they grow beyond simple settings |
| Alacritty | Nix settings, native helpers | TOML settings render through Nix; helper scripts stay native |
| Git | Nix | Strong Home Manager support |
| Nushell | Hybrid | Functions and scripts are best as `.nu` |
| Neovim | Hybrid | Lua configuration and plugin management |
| Yazi | Hybrid | Static settings and Lua plugins are separated |
| OpenCode | Hybrid | Static settings and runtime state are separated |

## Directory Layout

```text
dotfiles/
├── flake.nix
├── hosts/
│   └── darwin/
├── home/
│   ├── default.nix
│   ├── packages.nix
│   └── modules/
├── nix/
├── secrets/
└── xdg/
    └── config/
```

- `home/modules/` is the single entrance for application configuration.
- `hosts/` holds machine-level (nix-darwin) configuration; per-host differences belong there, not in modules.
- `xdg/config/` holds only files that are worth keeping in native format.

## Operating Rules

- Check first whether Home Manager can manage a new setting.
- Migrate existing settings step by step, only where maintainability measurably improves.
- Do not rewrite working configuration for aesthetics alone.
- Keep sources and generated output clearly distinct.
- Do not mix mechanisms for the same purpose across applications without reason.
- Justify every new dependency or abstraction.

## Verification

Scope the gates to what changed, following the repository rules.

| Change | Gate |
|---|---|
| Any `.nix` file | `just fmt-check`, `just lint`, `just dead` |
| Module output changes | Evaluate the full target and build the changed artifact |
| Pure refactor | Assert byte-equal `.drvPath` before and after |
| Native files | The language's own check (for example `nu --ide-check 1000 <file>` for Nushell) |

Format, lint, and dead-code checks do not evaluate the configuration, so evaluation is a separate step.

## Final Criteria

Beautiful dotfiles are not those written in one format.
Each setting sits in the right place, the management method is consistent, and changes and rebuilds are easy.

Priority order:

1. Correctness and functionality
2. Maintainability and ease of change
3. Reproducibility and portability
4. Structural consistency
5. Brevity and elegance

When practicality is equal, choose the more consistent, shorter, and more elegant structure.
