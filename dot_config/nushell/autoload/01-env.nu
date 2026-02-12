# Environment Variables Module
# XDG Base Directory and application-specific settings

export def xdg-dirs [] {
    {
        config: ($env | get --optional XDG_CONFIG_HOME | default ($env.HOME | path join ".config"))
        cache: ($env | get --optional XDG_CACHE_HOME | default ($env.HOME | path join ".cache"))
        data: ($env | get --optional XDG_DATA_HOME | default ($env.HOME | path join ".local" "share"))
        state: ($env | get --optional XDG_STATE_HOME | default ($env.HOME | path join ".local" "state"))
    }
}

# =============================================================================
# XDG DIRS
# =============================================================================
let XDG_DIRS = (xdg-dirs)

# =============================================================================
# LOCALE
# =============================================================================
$env.LANG = "en_US.UTF-8"
$env.LC_ALL = "en_US.UTF-8"

# =============================================================================
# ENV_CONVERSIONS (for colon-separated environment variables)
# =============================================================================
$env.ENV_CONVERSIONS = ($env.ENV_CONVERSIONS | default {}) | merge {
    "PATH": {
        from_string: {|s| $s | split row (char esep) | path expand --no-symlink }
        to_string: {|v| $v | path expand --no-symlink | str join (char esep) }
    }
    "XDG_DATA_DIRS": {
        from_string: {|s| $s | split row (char esep) }
        to_string: {|v| $v | str join (char esep) }
    }
    "TERMINFO_DIRS": {
        from_string: {|s| $s | split row (char esep) }
        to_string: {|v| $v | str join (char esep) }
    }
}

# =============================================================================
# XDG BASE DIRECTORY
# =============================================================================
$env.XDG_CONFIG_HOME = $XDG_DIRS.config
$env.XDG_CACHE_HOME = $XDG_DIRS.cache
$env.XDG_DATA_HOME = $XDG_DIRS.data
$env.XDG_STATE_HOME = $XDG_DIRS.state

# =============================================================================
# APPLICATION-SPECIFIC PATHS (XDG-compliant)
# =============================================================================

# GnuPG
$env.GNUPGHOME = ($env.XDG_CONFIG_HOME | path join "gnupg")

# Rust/Cargo
$env.CARGO_HOME = ($env.XDG_DATA_HOME | path join "cargo")

# Node.js/npm
$env.NPM_CONFIG_PREFIX = ($env.XDG_DATA_HOME | path join "npm")
$env.NPM_CONFIG_CACHE = ($env.XDG_CACHE_HOME | path join "npm")
$env.NPM_CONFIG_USERCONFIG = ($env.XDG_CONFIG_HOME | path join "npm" "npmrc")

# Taskwarrior
$env.TASKRC = ($env.XDG_CONFIG_HOME | path join "taskwarrior" "config")
$env.TASKDATA = ($env.XDG_DATA_HOME | path join "taskwarrior")

# ZK (Zettelkasten)
$env.ZK_NOTEBOOK_DIR = ($env.HOME | path join "dev" "zettel")
$env.ZK_EDITOR = "hx"

# Zoxide
$env._ZO_DATA_DIR = ($env.XDG_DATA_HOME | path join "zoxide")

# Bat
$env.BAT_CONFIG_DIR = ($env.XDG_CONFIG_HOME | path join "bat")
$env.BAT_CACHE_DIR = ($env.XDG_CACHE_HOME | path join "bat")

# Starship
$env.STARSHIP_CONFIG = ($env.XDG_CONFIG_HOME | path join "starship" "starship.toml")

# Terminfo
$env.TERMINFO_DIRS = [($env.XDG_DATA_HOME | path join "terminfo") "/usr/share/terminfo"]
$env.TERMINFO = ($env.XDG_DATA_HOME | path join "terminfo")

# Scilab
$env.SCIHOME = ($env.XDG_CONFIG_HOME | path join "scilab")

# ShellCheck
$env.SHELLCHECK_OPTS = "--rcfile=" + ($env.XDG_CONFIG_HOME | path join "shellcheck" "shellcheckrc" | path expand)

# Docker
$env.DOCKER_CONFIG = ($env.XDG_CONFIG_HOME | path join "docker")

# Lima
$env.LIMA_HOME = ($env.XDG_DATA_HOME | path join "lima")

# Ollama
$env.OLLAMA_MODELS = ($env.XDG_DATA_HOME | path join "ollama" "models")
$env.OLLAMA_FLASH_ATTENTION = "1"
$env.OLLAMA_KV_CACHE_TYPE = "q8_0"
$env.OLLAMA_KEEP_ALIVE = "5m"
$env.OLLAMA_ORIGINS = "moz-extension://*"

# History files
$env.LESSHISTFILE = ($env.XDG_STATE_HOME | path join "less" "history")

# Shell session state
$env.SHELL_SESSION_DIR = ($env.XDG_STATE_HOME | path join "nushell" "sessions")

# =============================================================================
# DEVELOPMENT ENVIRONMENT
# =============================================================================

# Dotfiles
if ($env | get -o DOTFILES_DIR | default "" | is-empty) {
    $env.DOTFILES_DIR = ($env.HOME | path join ".config" "nix-config")
}
if ($env | get -o DOTFILES_FLAKE_TARGET | default "" | is-empty) {
    $env.DOTFILES_FLAKE_TARGET = "macbook"
}

# Editor
$env.EDITOR = "hx"
$env.VISUAL = $env.EDITOR

# Shell
let nu_path = (which nu | get path.0?)
if $nu_path != null {
    $env.SHELL = $nu_path
}

# =============================================================================
# TERMINAL SETTINGS
# =============================================================================

# LS_COLORS for Solarized Dark
$env.LS_COLORS = "di=1;34:ln=1;36:so=32:pi=33:ex=31:bd=34;46:cd=34;43:su=30;41:sg=30;46:tw=30;42:ow=30;43"

# Color support
$env.CLICOLOR = "1"
$env.LSCOLORS = "Gxfxcxdxbxegedabagacad"

# Truecolor support
$env.COLORTERM = "truecolor"

# =============================================================================
# FZF CONFIGURATION
# =============================================================================
$env.FZF_DEFAULT_OPTS = "
  --color=bg+:#073642,bg:#002b36,spinner:#719e07,hl:#719e07
  --color=fg:#839496,header:#586e75,info:#cb4b16,pointer:#719e07
  --color=marker:#719e07,fg+:#839496,prompt:#719e07,hl+:#719e07
"
