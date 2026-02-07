# Integrations wrappers (lazy-loaded cache generation)

const integrations_module = ($nu.config-path | path dirname | path join "modules" "integrations.nu")

export def integrations-cache-update [] {
    overlay use $integrations_module
    integrations_cache_update
}

if (which direnv | is-not-empty) {
    let direnv_init = (do { direnv export json } | complete)
    if ($direnv_init.exit_code == 0) {
        let direnv_json = ($direnv_init.stdout | from json)
        if ($direnv_json | is-not-empty) {
            $direnv_json | load-env
        }
    }
}
