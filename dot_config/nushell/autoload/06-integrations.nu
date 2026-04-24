
# requires: modules/integrations

# Integrations wrapper (eager-loaded via config.nu → modules/integrations.nu)

export def integrations-cache-update [] {
    integrations_cache_update
}

# Direnv is initialized lazily in 10-source-tools.nu
