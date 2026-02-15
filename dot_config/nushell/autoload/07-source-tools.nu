# Integrations cache consumer (source-only)
# Cache generation happens in modules/integrations.nu via integrations-cache-update.

const starship_file = ($nu.home-dir | path join ".cache" "nushell-init" "starship.nu")
const zoxide_file = ($nu.home-dir | path join ".cache" "nushell-init" "zoxide.nu")
const carapace_file = ($nu.home-dir | path join ".cache" "nushell-init" "carapace.nu")
const atuin_file = ($nu.home-dir | path join ".cache" "nushell-init" "atuin.nu")

# Refresh cached init scripts first
if (scope commands | where name == "integrations-cache-update" | is-not-empty) {
    integrations-cache-update
}

# STARSHIP PROMPT
if (has-cmd starship) {
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
    if ($atuin_file | path exists) {
        source $atuin_file
    }
}

# Taskwarrior preview (wraps right prompt after prompt tools load)
if (scope commands | where name == "task_preview_enable" | is-not-empty) {
    task_preview_enable
}
