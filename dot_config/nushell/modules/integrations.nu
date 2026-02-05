# Integrations cache generator (lazy-loaded)

def cache_is_stale [tool: string, cache_file: path] {
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

def write_cache_hash [tool: string, cache_file: path] {
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

export def integrations_cache_update [] {
    let xdg_dirs = (try { xdg-dirs } catch {
        {
            config: ($env.HOME | path join ".config")
            cache: ($env.HOME | path join ".cache")
            data: ($env.HOME | path join ".local" "share")
            state: ($env.HOME | path join ".local" "state")
        }
    })

    let cache_dir = ($xdg_dirs.cache | path join "nushell-init")
    let force_regen = (($env | get NU_INIT_REGEN? | default "0") == "1")

    if not ($cache_dir | path exists) {
        mkdir $cache_dir
    }

    if (which starship | is-not-empty) {
        let starship_file = ($cache_dir | path join "starship.nu")
        let starship_regen = ($force_regen or (not ($starship_file | path exists)) or (cache_is_stale "starship" $starship_file))
        if $starship_regen {
            let starship_init = (do { starship init nu } | complete)
            if ($starship_init.exit_code == 0) {
                $starship_init.stdout | save -f $starship_file
                write_cache_hash "starship" $starship_file
            }
        }
    }

    if (which zoxide | is-not-empty) {
        let zoxide_file = ($cache_dir | path join "zoxide.nu")
        let zoxide_regen = ($force_regen or (not ($zoxide_file | path exists)) or (cache_is_stale "zoxide" $zoxide_file))
        if $zoxide_regen {
            let zoxide_init = (do { zoxide init nushell } | complete)
            if ($zoxide_init.exit_code == 0) {
                $zoxide_init.stdout | save -f $zoxide_file
                write_cache_hash "zoxide" $zoxide_file
            }
        }
    }

    if (which carapace | is-not-empty) {
        let carapace_file = ($cache_dir | path join "carapace.nu")
        let carapace_regen = ($force_regen or (not ($carapace_file | path exists)) or (cache_is_stale "carapace" $carapace_file))
        if $carapace_regen {
            let carapace_init = (do { carapace _carapace nushell } | complete)
            if ($carapace_init.exit_code == 0) {
                $carapace_init.stdout | save -f $carapace_file
                write_cache_hash "carapace" $carapace_file
            }
        }
    }

    if (which atuin | is-not-empty) {
        let atuin_file = ($cache_dir | path join "atuin.nu")
        let atuin_regen = ($force_regen or (not ($atuin_file | path exists)) or (cache_is_stale "atuin" $atuin_file))
        if $atuin_regen {
            let atuin_init = (do { atuin init nu } | complete)
            if ($atuin_init.exit_code == 0) {
                $atuin_init.stdout | save -f $atuin_file
                write_cache_hash "atuin" $atuin_file
            }
        }
    }
}
