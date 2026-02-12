
# Nushell Configuration

# History
$env.config.history = {
    file_format: 'sqlite'
    max_size: 1_000_000
    sync_on_enter: true
    isolation: false
}

# UI & Completions
$env.config.show_banner = false
$env.config.error_style = 'fancy'
$env.config.edit_mode = 'emacs'
$env.config.completions.external = {
    enable: true
    max_results: 100
    completer: {|spans|
        if (which carapace | is-not-empty) {
            carapace $spans.0 nushell ...$spans | from json
        } else {
            null
        }
    }
}

# =============================================================================
# AUTOLOAD MODULES
# =============================================================================

const config_dir = ($nu.config-path | path dirname)

source ($config_dir | path join 'autoload' '00-constants.nu')
source ($config_dir | path join 'autoload' '00-helpers.nu')

# Modules (Dependencies) - Load these FIRST
source ($config_dir | path join 'autoload' '03-aliases.nu')
source ($config_dir | path join 'autoload' '04-functions.nu')
source ($config_dir | path join 'autoload' '05-completions.nu')
source ($config_dir | path join 'autoload' '06-integrations.nu')
source ($config_dir | path join 'autoload' '08-taskwarrior.nu')
source ($config_dir | path join 'autoload' '09-lima.nu')

# Tools / Consumers - Load these LAST
source ($config_dir | path join 'autoload' '07-source-tools.nu')

# Local config (optional)
try { source ($config_dir | path join 'local.nu') }
