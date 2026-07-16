# Nushell Configuration

Nushell is a modern shell that treats everything as data. This configuration provides a modular, maintainable setup with XDG compliance and conditional command loading.

## Architecture

The configuration follows a modular structure using the `autoload/` directory pattern:

```
dot_config/nushell/
├── env.nu                  # ~/.config/nushell/env.nu
├── config.nu               # ~/.config/nushell/config.nu
├── autoload/
│   ├── 00-helpers.nu       # Shared helper functions
│   ├── 01-env.nu           # Environment variables & XDG paths
│   ├── 02-path.nu          # PATH configuration with path-add helper
│   ├── 03-aliases.nu       # Command aliases with fallbacks
│   ├── 04-functions.nu     # Custom functions & wrappers
│   ├── 05-completions.nu   # Command completions
│   ├── 07-abbreviations.nu # Fish-style abbreviation expansion (Space/Enter)
│   ├── 09-lima.nu          # Lazy wrapper for Lima/Docker helpers
│   ├── 10-source-tools.nu  # Sources Nix-built init scripts
│   └── 99-local.nu         # Loads unmanaged local overrides last
└── modules/
    └── lima.nu             # Lima/Docker commands
```

## Module Loading

Nushell includes `~/.config/nushell/autoload` in `$nu.user-autoload-dirs` and automatically sources its `.nu` files in filename order after `config.nu`:

```nushell
$nu.user-autoload-dirs
# => [..., ~/.config/nushell/autoload]
```

`env.nu` and `config.nu` do not manually source these files. Using the native autoload path prevents hooks and keybindings from being registered twice. Numeric prefixes make dependencies deterministic, and `99-local.nu` loads machine-specific overrides last.

Paths inside startup files remain anchored to `$nu.home-dir`, so Home Manager's `/nix/store` symlinks and different usernames do not require path rewrites.

Reusable tool logic lives under `modules/` and is exposed by lightweight wrappers in `autoload/`. `config.nu` loads the Lima module before automatic autoload reaches `09-lima.nu`; `10-source-tools.nu` then loads the Nix-generated integrations.

Carapace completion is configured directly in `config.nu`. It does not source runtime-generated files, so deleting `~/.cache` cannot break Nushell parsing.

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

## Third-Party Integrations

### Prompt and Tool Integrations
- **Starship** - Safety-focused cross-shell prompt
- **Zoxide** - Smart directory jumping
- **Carapace** - Command completions
- **Atuin** - Shell history sync
- **Direnv** - Environment management and state detection via a PWD change hook (no cache or per-prompt subprocess)

Nix generates Starship, Zoxide, and Atuin init scripts during the build and deploys them under `~/.config/nushell/generated/`. `autoload/10-source-tools.nu` sources those deterministic files after activation. Carapace uses the external completer defined directly in `config.nu` and does not require an init cache.

Direnv integration is attached to `$env.config.hooks.env_change.PWD` in `autoload/10-source-tools.nu`, so `direnv export json` runs whenever you `cd` and environment updates are applied automatically. A thin `direnv` wrapper reruns the same sync after a successful `direnv allow`, making the indicator update without another `cd`. The hook exposes loaded state through `DIRENV_DIR` and blocked state through `DIRENV_BLOCKED`; Starship renders both with `env_var` modules, so no direnv subprocess runs per prompt.

### Starship Prompt Safety Model

The Solarized Dark prompt uses a quiet `base02` Neutral Rail with rounded caps: blue location, green VCS, and cyan environment foregrounds share the carrier, while orange dirty-state and red anomaly chips appear only when active. It stays intentionally quiet during normal operation. The left prompt contains only context whose absence can cause an operational mistake: operating system, SSH/root identity, directory, Git branch and working-tree state, Nix shell, Direnv state, virtual environment, and the SSH-agent anomaly indicator. Language and tool version modules are omitted because the flake pins toolchains. Exit status, command duration, and background jobs appear in `right_format`, away from the typing path.

Virtual environment display uses Starship's `env_var.VIRTUAL_ENV_PROMPT` module and spawns no process per prompt. `uv` and modern activation scripts normally set `VIRTUAL_ENV_PROMPT`; if a tool sets only `VIRTUAL_ENV`, the segment stays hidden. The documented fallback is to configure the module for `VIRTUAL_ENV`, which displays the full environment path.

Before each prompt, a Nushell hook checks whether `SSH_AUTH_SOCK` is set and whether its socket path exists. It sets `PASS_AGENT_DOWN=✗` only for the anomalous state, which produces a red Starship warning, and removes the variable when the socket returns. This is a zero-subprocess stat check, not an agent health check: a stale socket left by a dead agent is a known blind spot.

The Plan B Starship init also sets Nushell's transient prompt commands. Nushell replaces a completed prompt with the Starship character, reducing scrollback to the character plus the command. `starship module character` receives no previous `--status` value through this path, so the transient character may always render with the success color.

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

Use `~/.config/nushell/local.nu` for machine-specific settings.
Home Manager activation auto-creates this file as empty if missing.
Add overrides as needed:

```nushell
# ~/.config/nushell/local.nu
$env.MY_LOCAL_VAR = "value"
alias mylocal = echo "local alias"
```

Security-sensitive values should live here. In particular, `OLLAMA_ORIGINS` is intentionally not set in `autoload/01-env.nu`; set a specific browser extension UUID in `local.nu` when needed.

`autoload/99-local.nu` automatically sources this file after all managed startup files.

## References

- [Nushell Book](https://www.nushell.sh/book/)
- [Nushell Cookbook](https://www.nushell.sh/cookbook/)
