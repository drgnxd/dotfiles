
# Integrations wrappers (lazy-loaded cache generation)

const integrations_module_path = ($nu.home-dir | path join ".config" "nushell" "modules" "integrations.nu")

export def integrations-cache-update [] {
    # overlay use must live in the same scope as the command call;
    # a helper def cannot propagate overlays back to its caller.
    # Calling overlay use when already active is a no-op, so no guard needed.
    overlay use $integrations_module_path
    integrations_cache_update
}

if (has-cmd direnv) {
    let direnv_init = (do { direnv export json } | complete)
    if ($direnv_init.exit_code == 0) {
        let direnv_json = ($direnv_init.stdout | from json)
        if ($direnv_json | is-not-empty) {
            $direnv_json | load-env
        }
    }
}
