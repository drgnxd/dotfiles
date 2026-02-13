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
    ├── 02-path.nu          # PATH configuration with path-add helper
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

`env.nu` and `config.nu` resolve a runtime `config_dir` from Nushell's active config paths, then source modules relative to that directory:

```nushell
# env.nu
const config_dir = ($nu.env-path | path dirname)
source ($config_dir | path join 'autoload' '01-env.nu')
source ($config_dir | path join 'autoload' '02-path.nu')

# config.nu
const config_dir = ($nu.config-path | path dirname)
source ($config_dir | path join 'autoload' '00-constants.nu')
source ($config_dir | path join 'autoload' '00-helpers.nu')
...
```

This keeps module lookups anchored to whichever config Nushell actually loaded and avoids parse-time failures caused by store-backed symlink paths in Home Manager.

No user-specific path rewrites are needed when moving between machines/users, as long as `env.nu` and `config.nu` are loaded from the target config directory.

Lazy-loaded integrations live under `modules/` and are pulled in by lightweight wrappers in `autoload/` via `overlay use` with module constants exported from `autoload/00-constants.nu`. This keeps startup fast while avoiding hardcoded path assumptions.

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

### 3. PATH Management Helper

PATH entries are added through a small helper that only prepends existing paths in a deterministic order:

```nushell
def --env path-add [new_path: string] {
    if ($new_path | path exists) {
        $env.PATH = ($env.PATH | prepend $new_path | uniq)
    }
}
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
- Edit mode: Readline-compatible (Nushell `emacs` mode)
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
