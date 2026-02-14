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

    # Tool definitions: [tool_name, cache_filename, init_command_args]
    let tools = [
        ["starship",  "starship.nu",  ["starship", "init", "nu"]]
        ["zoxide",    "zoxide.nu",    ["zoxide", "init", "nushell"]]
        ["carapace",  "carapace.nu",  ["carapace", "_carapace", "nushell"]]
        ["atuin",     "atuin.nu",     ["atuin", "init", "nu"]]
    ]

    for tool_entry in $tools {
        let tool_name = ($tool_entry | get 0)
        let cache_filename = ($tool_entry | get 1)
        let init_args = ($tool_entry | get 2)

        if (which $tool_name | is-not-empty) {
            let cache_file = ($cache_dir | path join $cache_filename)
            let needs_regen = ($force_regen or (not ($cache_file | path exists)) or (cache_is_stale $tool_name $cache_file))
            if $needs_regen {
                let init_result = (do { ^($init_args | get 0) ...($init_args | skip 1) } | complete)
                if ($init_result.exit_code == 0) {
                    $init_result.stdout | save -f $cache_file
                    write_cache_hash $tool_name $cache_file
                }
            }
        }
    }
}
