
let has_carapace = (which carapace | is-not-empty)

$env.config.history = {
    file_format: 'sqlite'
    max_size: 1_000_000
    sync_on_enter: true
    isolation: false
}

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

# User startup files under autoload/ are loaded automatically in filename order
# after config.nu. Do not source them here or hooks and keybindings will duplicate.
