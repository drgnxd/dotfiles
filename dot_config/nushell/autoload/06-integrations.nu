# Integrations Module - Cache Generation
# This file generates cache files for third-party tools
# The actual sourcing happens in 07-source-tools.nu with literal paths
#
# FIRST TIME SETUP:
#   1. Run this file once: nu ~/.config/nushell/autoload/06-integrations.nu
#   2. New Nushell sessions will automatically source the caches

let cache_dir = ($env.HOME | path join ".cache" "nushell-init")
let force_regen = (($env | get NU_INIT_REGEN? | default "0") == "1")

# Ensure cache directory exists
if not ($cache_dir | path exists) {
    mkdir $cache_dir
}

# STARSHIP PROMPT
if (has-cmd starship) {
    let starship_file = ($cache_dir | path join "starship.nu")
    if $force_regen or (not ($starship_file | path exists)) {
        let starship_init = (do { starship init nu } | complete)
        if ($starship_init.exit_code == 0) {
            $starship_init.stdout | save -f $starship_file
        }
    }
}

# ZOXIDE
if (has-cmd zoxide) {
    let zoxide_file = ($cache_dir | path join "zoxide.nu")
    if $force_regen or (not ($zoxide_file | path exists)) {
        let zoxide_init = (do { zoxide init nushell } | complete)
        if ($zoxide_init.exit_code == 0) {
            $zoxide_init.stdout | save -f $zoxide_file
        }
    }
}

# CARAPACE
if (has-cmd carapace) {
    let carapace_file = ($cache_dir | path join "carapace.nu")
    if $force_regen or (not ($carapace_file | path exists)) {
        let carapace_init = (do { carapace _carapace nushell } | complete)
        if ($carapace_init.exit_code == 0) {
            $carapace_init.stdout | save -f $carapace_file
        }
    }
}

# ATUIN
if (has-cmd atuin) {
    let atuin_file = ($cache_dir | path join "atuin.nu")
    if $force_regen or (not ($atuin_file | path exists)) {
        let atuin_init = (do { atuin init nu } | complete)
        if ($atuin_init.exit_code == 0) {
            $atuin_init.stdout | save -f $atuin_file
        }
    }
}

# DIRENV - uses load-env instead of source, no cache needed
if (has-cmd direnv) {
    let direnv_init = (do { direnv export json } | complete)
    if ($direnv_init.exit_code == 0) {
        let direnv_json = ($direnv_init.stdout | from json)
        if ($direnv_json | is-not-empty) {
            $direnv_json | load-env
        }
    }
}
