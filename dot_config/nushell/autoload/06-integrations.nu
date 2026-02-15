
# Integrations wrappers (lazy-loaded cache generation)

export def integrations-cache-update [] {
    overlay use $integrations_module
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
