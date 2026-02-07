# Integrations Module - Source Cache Files
# IMPORTANT: This file contains literal paths for 'source' commands
# 
# FIRST TIME SETUP:
#   1. Generate cache files: nu ~/.config/nushell/autoload/06-integrations.nu
#   2. New Nushell sessions will automatically source the caches
#
# NOTE: Cache files are sourced if present; 06-integrations generates them.

# Refresh cached init scripts if available
const cache_dir = "/Users/drgnxd/.cache/nushell-init"
const starship_file = "/Users/drgnxd/.cache/nushell-init/starship.nu"
const zoxide_file = "/Users/drgnxd/.cache/nushell-init/zoxide.nu"
const carapace_file = "/Users/drgnxd/.cache/nushell-init/carapace.nu"
const atuin_file = "/Users/drgnxd/.cache/nushell-init/atuin.nu"
const starship_bin = "/etc/profiles/per-user/drgnxd/bin/starship"
const brew_starship_bin = "/opt/homebrew/bin/starship"
if (scope commands | where name == "integrations-cache-update" | is-not-empty) {
    integrations-cache-update
}

# STARSHIP PROMPT
if (has-cmd starship) {
    let needs_regen = if ($starship_file | path exists) {
        let content = (open $starship_file | str trim)
        ($content | is-empty) or ($content | str contains $brew_starship_bin)
    } else {
        true
    }
    if $needs_regen and ($starship_bin | path exists) {
        let starship_init = (do { ^$starship_bin init nu } | complete)
        if ($starship_init.exit_code == 0) {
            $starship_init.stdout | save -f $starship_file
        }
    }
    if ($starship_file | path exists) {
        source $starship_file
    }
}

# ZOXIDE
if ((has-cmd zoxide) and ($zoxide_file | path exists)) {
    source $zoxide_file
}

# CARAPACE
if ((has-cmd carapace) and ($carapace_file | path exists)) {
    source $carapace_file
}

# ATUIN
if (has-cmd atuin) {
    if (not ($atuin_file | path exists)) {
        let atuin_init = (do { atuin init nu } | complete)
        if ($atuin_init.exit_code == 0) {
            $atuin_init.stdout | save -f $atuin_file
        }
    }
    if ($atuin_file | path exists) {
        source $atuin_file
    }
}

# Taskwarrior preview (wraps right prompt after prompt tools load)
if (scope commands | where name == "task_preview_enable" | is-not-empty) {
    task_preview_enable
}
