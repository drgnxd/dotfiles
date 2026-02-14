
# Nushell Configuration

# Use ~/.config/nushell unconditionally (see env.nu for rationale).
const config_dir = ($nu.home-dir | path join '.config' 'nushell')

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

# Task preview keybindings
let task_preview_repaint_keys = (
    # Generate digit keybindings (0-9) data-driven
    (0..9 | each { |n|
        {
            name: $"task_preview_digit_($n)"
            modifier: none
            keycode: $"char_($n)"
            mode: [emacs vi_insert]
            event: [
                { edit: insertchar value: ($n | into string) }
                { send: executehostcommand cmd: 'task_preview_update' }
                { send: repaint }
            ]
        }
    })
    | append [
        {
            name: task_preview_backspace
            modifier: none
            keycode: backspace
            mode: [emacs vi_insert]
            event: [
                { edit: backspace }
                { send: executehostcommand cmd: 'task_preview_update' }
                { send: repaint }
            ]
        }
        {
            name: task_preview_delete
            modifier: none
            keycode: delete
            mode: [emacs vi_insert]
            event: [
                { edit: delete }
                { send: executehostcommand cmd: 'task_preview_update' }
                { send: repaint }
            ]
        }
        {
            name: task_preview_cancel
            modifier: control
            keycode: char_c
            mode: [emacs vi_insert vi_normal]
            event: [
                { send: executehostcommand cmd: 'task_preview_clear' }
                { send: ctrlc }
            ]
        }
    ]
)

$env.config.keybindings = (
    ($env.config.keybindings | default [])
    | append $task_preview_repaint_keys
)

# =============================================================================
# AUTOLOAD MODULES
# =============================================================================

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
