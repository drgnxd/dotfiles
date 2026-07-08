# Integrations cache generator — Plan A (runtime hash sync)
#
# Only carapace requires runtime caching because it embeds
# $XDG_CONFIG_HOME paths and panics without $HOME access,
# making it incompatible with the Nix sandbox.
#
# Plan B tools (starship, zoxide, atuin) are built at nix-build
# time via home/modules/nushell-integrations.nix.

def tool_path [tool: string] {
    which $tool | get path.0?
}

def hash_command [] {
    if (which shasum | is-not-empty) {
        "shasum"
    } else if (which sha256sum | is-not-empty) {
        "sha256sum"
    } else {
        null
    }
}

def tool_signature [tool: string] {
    let p = (tool_path $tool)
    if $p == null {
        return null
    }

    let real = ($p | path expand)
    if ($real | str starts-with "/nix/store/") {
        return $"path:($real)"
    }

    let hash_cmd = (hash_command)
    if $hash_cmd == null {
        return null
    }
    let hash_args = if $hash_cmd == "shasum" { ["-a" "256" $real] } else { [$real] }
    let hash_result = (do { ^$hash_cmd ...$hash_args } | complete)
    if ($hash_result.exit_code != 0) {
        return null
    }

    let tool_hash = ($hash_result.stdout | str trim | split row " " | get 0?)
    if $tool_hash == null {
        return null
    }

    $"sha256:($tool_hash)"
}

def cache_is_stale [tool: string, cache_file: path] {
    let signature = (tool_signature $tool)
    if $signature == null {
        return false
    }

    let cache_hash_file = ($cache_file | path dirname | path join $"($tool).hash")
    if not ($cache_hash_file | path exists) {
        return true
    }

    (open $cache_hash_file | str trim) != $signature
}

def write_cache_hash [tool: string, cache_file: path] {
    let signature = (tool_signature $tool)
    if $signature == null {
        return
    }

    let cache_hash_file = ($cache_file | path dirname | path join $"($tool).hash")
    $signature | save -f $cache_hash_file
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

    # Plan A: only carapace needs runtime caching
    let tools = [
        ["carapace", "carapace.nu", ["carapace", "_carapace", "nushell"]]
    ]

    for tool_entry in $tools {
        let tool_name = ($tool_entry | get 0)
        let cache_filename = ($tool_entry | get 1)
        let init_args = ($tool_entry | get 2)

        if (has-cmd $tool_name) {
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
