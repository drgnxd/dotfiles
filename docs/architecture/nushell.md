# Nushell Configuration

Nushell is a modern shell that treats everything as data. This configuration provides a modular, maintainable setup with XDG compliance and conditional command loading.

## Architecture

The configuration follows a modular structure using the `autoload/` directory pattern:

```
dot_config/nushell/
├── env.nu                  # ~/.config/nushell/env.nu
├── config.nu               # ~/.config/nushell/config.nu
├── autoload/
    ├── 00-helpers.nu       # Shared helper functions
    ├── 01-env.nu           # Environment variables & XDG paths
    ├── 02-path.nu          # PATH configuration using std/util
    ├── 03-aliases.nu       # Command aliases with fallbacks
    ├── 04-functions.nu     # Custom functions & wrappers
    ├── 05-completions.nu   # Command completions
    ├── 06-integrations.nu  # Lazy wrapper for integration cache updates
    ├── 07-source-tools.nu  # Sources cached init scripts
    ├── 08-taskwarrior.nu   # Lazy wrapper for task preview and task command
    └── 09-lima.nu          # Lazy wrapper for Lima/Docker helpers
└── modules/
    ├── integrations.nu    # Cache generation (on demand)
    ├── taskwarrior.nu     # Task preview + cache refresh
    └── lima.nu            # Lima/Docker commands
```

## Module Loading

`config.nu` sources modules with explicit paths derived from `$nu.default-config-dir` and loads cached init scripts if present:

```nushell
# AUTOLOAD MODULES
source ($nu.default-config-dir | path join "autoload" "01-env.nu")
source ($nu.default-config-dir | path join "autoload" "02-path.nu")
...
```

This approach avoids the parse-time evaluation issues that occur with dynamic `ls | each { source }` patterns.

Lazy-loaded integrations live under `modules/` and are pulled in by lightweight wrappers in `autoload/` via `overlay use` with literal paths. This keeps startup fast while avoiding parse-time evaluation errors.

## Key Features

### 1. XDG Base Directory Compliance

All application data is stored in XDG-compliant locations:
- Config: `~/.config/`
- Cache: `~/.cache/`
- Data: `~/.local/share/`
- State: `~/.local/state/`

See `01-env.nu` for the complete XDG path configuration.

### 2. Conditional Command Loading

Commands are defined with automatic fallback to standard tools:

```nushell
export def g [...args] {
    if (has-cmd rg) {
        rg ...$args
    } else {
        ^grep ...$args
    }
}
```

This ensures the configuration works across different systems, even when modern tools (bat, fd, ripgrep) aren't installed.

### 3. Standard Library Integration

Uses Nushell's `std/util` for PATH management:

```nushell
use std "path add"
path add ($env.HOME | path join ".local" "bin")
```

### 4. ENV_CONVERSIONS

Colon-separated environment variables (PATH, TERMINFO_DIRS, etc.) are properly handled with converters:

```nushell
$env.ENV_CONVERSIONS = ($env.ENV_CONVERSIONS | default {}) | merge {
    "PATH": {
        from_string: {|s| $s | split row (char esep) | path expand --no-symlink }
        to_string: {|v| $v | path expand --no-symlink | str join (char esep) }
    }
}
```

## Available Aliases & Commands

### File Operations
- `la`, `ld`, `lf`, `lsize` - List variants (all/dirs/files/size)
- `cat` - Display files (uses bat if available)
- `f` - Find files (uses fd if available)

### Search
- `g` - Search with ripgrep (fallback to grep)

### Application Shortcuts
- `t` - Taskwarrior
- `lg` - LazyGit
- `oc`, `ocd` - opencode
- `pload` - Proton Pass CLI

### Lima/Docker
- `lls` - List Lima VMs
- `dctx` - Docker context switch
- `dctx-reset` - Reset to default context

### Functions
- `y` - Yazi file manager with cwd tracking
- `zk` - Zettelkasten notebook with git sync
- `ppget` - Proton Pass password retrieval
- `upgrade-all` / `update` - Unified system upgrade
- `save-stats` - Export Stats.app configuration
- `bundle-id` - Get macOS app bundle ID
- `integrations-cache-update` - Regenerate cached init scripts (Starship/Zoxide/Carapace/Atuin)

## Third-Party Integrations

### Cached Integrations
- **Starship** - Cross-shell prompt
- **Zoxide** - Smart directory jumping
- **Carapace** - Command completions
- **Atuin** - Shell history sync
- **Direnv** - Environment management (loaded at startup; no cache)

Cache generation runs on demand via `integrations-cache-update`. Generated init scripts are cached in `~/.cache/nushell-init` and sourced by `autoload/07-source-tools.nu`.

## Configuration Settings

### History
- Format: SQLite
- Max size: 1,000,000 entries
- Sync on enter: Enabled
- Isolation: Disabled

### UI
- Banner: Disabled
- Error style: Fancy
- Edit mode: Emacs
- Kitty protocol: Enabled
- Bracketed paste: Enabled

### Completions
- Case sensitive: No
- Algorithm: Prefix
- External completer: Carapace (if available)

## Migration from Zsh

This configuration replaces the previous Zsh setup. Key changes:

1. **No .zshenv/.zshrc** - Nushell uses `env.nu` and `config.nu`
2. **No .aliases** - Aliases are `export def` commands in `03-aliases.nu`
3. **No .functions** - Functions are `export def` in `04-functions.nu`
4. **Module system** - Uses Nushell's module system instead of shell sourcing

## Local Overrides

Create `~/.config/nushell/local.nu` for machine-specific settings:

```nushell
# ~/.config/nushell/local.nu
$env.MY_LOCAL_VAR = "value"
alias mylocal = echo "local alias"
```

This file is automatically sourced at the end of `config.nu`.

## References

- [Nushell Book](https://www.nushell.sh/book/)
- [Nushell Cookbook](https://www.nushell.sh/cookbook/)
