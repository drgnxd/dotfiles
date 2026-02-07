# PATH Configuration Module
# Uses Nushell standard library for path management

use std "path add"
let XDG_DIRS = (try { xdg-dirs } catch {
    {
        config: ($env.HOME | path join ".config")
        cache: ($env.HOME | path join ".cache")
        data: ($env.HOME | path join ".local" "share")
        state: ($env.HOME | path join ".local" "state")
    }
})

# =============================================================================
# DETECT NIX PROFILES
# =============================================================================
def detect-nix-paths [] {
    let user = ($env | get -o USER | default "")
    let per_user = if ($user | is-not-empty) { $"/etc/profiles/per-user/($user)/bin" } else { "" }
    let candidates = [
        ($env.HOME | path join ".nix-profile" "bin")
        ($env.HOME | path join ".local" "share" "nix" "profile" "bin")
        "/nix/var/nix/profiles/default/bin"
        "/run/current-system/sw/bin"
        $per_user
    ]
    
    $candidates | where { |it| ($it | is-not-empty) and ($it | path exists) }
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

# Homebrew (macOS, optional)
if ("/opt/homebrew/bin" | path exists) {
    path add "/opt/homebrew/bin"
}
if ("/opt/homebrew/sbin" | path exists) {
    path add "/opt/homebrew/sbin"
}

# Nix profiles (highest priority)
for p in (detect-nix-paths) {
    path add $p
}

# =============================================================================
# FZF WITH FD
# =============================================================================
if (has-cmd fd) {
    $env.FZF_DEFAULT_COMMAND = 'fd --type f --hidden --follow --exclude .git'
    $env.FZF_CTRL_T_COMMAND = $env.FZF_DEFAULT_COMMAND
    $env.FZF_ALT_C_COMMAND = 'fd --type d --hidden --follow --exclude .git'
}
