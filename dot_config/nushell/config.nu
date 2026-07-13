
# Nushell Configuration

# Use ~/.config/nushell unconditionally (see env.nu for rationale).
const config_dir = ($nu.home-dir | path join '.config' 'nushell')
let has_carapace = (which carapace | is-not-empty)

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
        if $has_carapace {
            carapace $spans.0 nushell ...$spans | from json
        } else {
            null
        }
    }
}

# =============================================================================
# AUTOLOAD MODULES
# =============================================================================

source ($config_dir | path join 'autoload' '00-constants.nu')
source ($config_dir | path join 'autoload' '00-helpers.nu')

# Tool modules (eager-loaded) — must precede autoload wrappers that call their exports
source ($config_dir | path join 'modules' 'integrations.nu')
source ($config_dir | path join 'modules' 'lima.nu')

# Modules (Dependencies) - Load these FIRST
source ($config_dir | path join 'autoload' '03-aliases.nu')
source ($config_dir | path join 'autoload' '04-functions.nu')
source ($config_dir | path join 'autoload' '05-completions.nu')

# Integrations wrapper — defines integrations-cache-update (calls module export directly)
source ($config_dir | path join 'autoload' '06-integrations.nu')
source ($config_dir | path join 'autoload' '07-abbreviations.nu')

# Lima wrapper — thin defs that delegate to eagerly-loaded module exports.
source ($config_dir | path join 'autoload' '09-lima.nu')

# Tools / Consumers - Load these LAST
source ($config_dir | path join 'autoload' '10-source-tools.nu')

# Local config (optional)
try { source ($config_dir | path join 'local.nu') }
