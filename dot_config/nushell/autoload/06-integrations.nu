
# Integrations wrapper (eager-loaded via config.nu → modules/integrations.nu)

export def integrations-cache-update [] {
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
