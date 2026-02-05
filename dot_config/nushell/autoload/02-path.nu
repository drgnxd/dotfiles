# PATH Configuration Module
# Uses Nushell standard library for path management

use std "path add"
let XDG_DIRS = (xdg-dirs)

# =============================================================================
# DETECT HOMEBREW
# =============================================================================
def detect-homebrew [] {
    let brew_paths = [
        "/opt/homebrew/bin/brew"
        "/usr/local/bin/brew"
        "/home/linuxbrew/.linuxbrew/bin/brew"
    ]
    
    $brew_paths | where { |it| ($it | path exists) and ($it | path type) == "file" } | get 0?
}

let brew_path = (detect-homebrew)

# Initialize Homebrew environment if found
if ($brew_path | is-not-empty) {
    # Get Homebrew prefix
    let hb_prefix = (do { ^$brew_path --prefix } | complete)
    if ($hb_prefix.exit_code == 0) {
        $env.HOMEBREW_PREFIX = ($hb_prefix.stdout | str trim)
    }
}

# =============================================================================
# ADD CUSTOM PATHS (in priority order)
# =============================================================================

# User local binaries
let local_bin = ($XDG_DIRS.data | path dirname | path join "bin")
path add $local_bin

# Cargo (Rust)
if ($env | get CARGO_HOME? | is-not-empty) {
    path add ($env.CARGO_HOME | path join "bin")
}

# npm global packages
if ($env | get NPM_CONFIG_PREFIX? | is-not-empty) {
    path add ($env.NPM_CONFIG_PREFIX | path join "bin")
}

# Homebrew LLVM
if ($brew_path | is-not-empty) {
    path add "/opt/homebrew/opt/llvm/bin"
}

# Homebrew binaries (highest priority)
if ($brew_path | is-not-empty) {
    let brew_bin = ($brew_path | path dirname)
    path add $brew_bin
}

# =============================================================================
# FZF WITH FD
# =============================================================================
if (has-cmd fd) {
    $env.FZF_DEFAULT_COMMAND = 'fd --type f --hidden --follow --exclude .git'
    $env.FZF_CTRL_T_COMMAND = $env.FZF_DEFAULT_COMMAND
    $env.FZF_ALT_C_COMMAND = 'fd --type d --hidden --follow --exclude .git'
}
