# Integrations Module - Cache Generation
# This file generates cache files for third-party tools
# The actual sourcing happens in 07-source-tools.nu with literal paths
#
# FIRST TIME SETUP:
#   1. Run this file once: nu ~/.config/nushell/autoload/06-integrations.nu
#   2. New Nushell sessions will automatically source the caches

let XDG_DIRS = (xdg-dirs)

let cache_dir = ($XDG_DIRS.cache | path join "nushell-init")
let force_regen = (($env | get NU_INIT_REGEN? | default "0") == "1")

def cache-is-stale [tool: string, cache_file: path] -> bool {
    let tool_path = (which $tool | get path.0?)
    if $tool_path == null {
        return false
    }

    let hash_result = (do { ^shasum -a 256 $tool_path } | complete)
    if ($hash_result.exit_code != 0) {
        return false
    }

    let tool_hash = ($hash_result.stdout | str trim | split row " " | get 0?)
    if $tool_hash == null {
        return false
    }

    let cache_hash_file = ($cache_file | path dirname | path join $"($tool).hash")
    if not ($cache_hash_file | path exists) {
        return true
    }

    (open $cache_hash_file | str trim) != $tool_hash
}

def write-cache-hash [tool: string, cache_file: path] {
    let tool_path = (which $tool | get path.0?)
    if $tool_path == null {
        return
    }

    let hash_result = (do { ^shasum -a 256 $tool_path } | complete)
    if ($hash_result.exit_code != 0) {
        return
    }

    let tool_hash = ($hash_result.stdout | str trim | split row " " | get 0?)
    if $tool_hash == null {
        return
    }

    let cache_hash_file = ($cache_file | path dirname | path join $"($tool).hash")
    $tool_hash | save -f $cache_hash_file
}

# Ensure cache directory exists
if not ($cache_dir | path exists) {
    mkdir $cache_dir
}

# STARSHIP PROMPT
if (has-cmd starship) {
    let starship_file = ($cache_dir | path join "starship.nu")
    let starship_regen = ($force_regen or (not ($starship_file | path exists)) or (cache-is-stale "starship" $starship_file))
    if $starship_regen {
        let starship_init = (do { starship init nu } | complete)
        if ($starship_init.exit_code == 0) {
            $starship_init.stdout | save -f $starship_file
            write-cache-hash "starship" $starship_file
        }
    }
}

# ZOXIDE
if (has-cmd zoxide) {
    let zoxide_file = ($cache_dir | path join "zoxide.nu")
    let zoxide_regen = ($force_regen or (not ($zoxide_file | path exists)) or (cache-is-stale "zoxide" $zoxide_file))
    if $zoxide_regen {
        let zoxide_init = (do { zoxide init nushell } | complete)
        if ($zoxide_init.exit_code == 0) {
            $zoxide_init.stdout | save -f $zoxide_file
            write-cache-hash "zoxide" $zoxide_file
        }
    }
}

# CARAPACE
if (has-cmd carapace) {
    let carapace_file = ($cache_dir | path join "carapace.nu")
    let carapace_regen = ($force_regen or (not ($carapace_file | path exists)) or (cache-is-stale "carapace" $carapace_file))
    if $carapace_regen {
        let carapace_init = (do { carapace _carapace nushell } | complete)
        if ($carapace_init.exit_code == 0) {
            $carapace_init.stdout | save -f $carapace_file
            write-cache-hash "carapace" $carapace_file
        }
    }
}

# ATUIN
if (has-cmd atuin) {
    let atuin_file = ($cache_dir | path join "atuin.nu")
    let atuin_regen = ($force_regen or (not ($atuin_file | path exists)) or (cache-is-stale "atuin" $atuin_file))
    if $atuin_regen {
        let atuin_init = (do { atuin init nu } | complete)
        if ($atuin_init.exit_code == 0) {
            $atuin_init.stdout | save -f $atuin_file
            write-cache-hash "atuin" $atuin_file
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
