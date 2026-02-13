
# Nushell Configuration

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
let task_preview_repaint_keys = [
    {
        name: task_preview_digit_0
        modifier: none
        keycode: char_0
        mode: [emacs vi_insert]
        event: [
            { edit: insertchar value: '0' }
            { send: executehostcommand cmd: 'task_preview_update' }
            { send: repaint }
        ]
    }
    {
        name: task_preview_digit_1
        modifier: none
        keycode: char_1
        mode: [emacs vi_insert]
        event: [
            { edit: insertchar value: '1' }
            { send: executehostcommand cmd: 'task_preview_update' }
            { send: repaint }
        ]
    }
    {
        name: task_preview_digit_2
        modifier: none
        keycode: char_2
        mode: [emacs vi_insert]
        event: [
            { edit: insertchar value: '2' }
            { send: executehostcommand cmd: 'task_preview_update' }
            { send: repaint }
        ]
    }
    {
        name: task_preview_digit_3
        modifier: none
        keycode: char_3
        mode: [emacs vi_insert]
        event: [
            { edit: insertchar value: '3' }
            { send: executehostcommand cmd: 'task_preview_update' }
            { send: repaint }
        ]
    }
    {
        name: task_preview_digit_4
        modifier: none
        keycode: char_4
        mode: [emacs vi_insert]
        event: [
            { edit: insertchar value: '4' }
            { send: executehostcommand cmd: 'task_preview_update' }
            { send: repaint }
        ]
    }
    {
        name: task_preview_digit_5
        modifier: none
        keycode: char_5
        mode: [emacs vi_insert]
        event: [
            { edit: insertchar value: '5' }
            { send: executehostcommand cmd: 'task_preview_update' }
            { send: repaint }
        ]
    }
    {
        name: task_preview_digit_6
        modifier: none
        keycode: char_6
        mode: [emacs vi_insert]
        event: [
            { edit: insertchar value: '6' }
            { send: executehostcommand cmd: 'task_preview_update' }
            { send: repaint }
        ]
    }
    {
        name: task_preview_digit_7
        modifier: none
        keycode: char_7
        mode: [emacs vi_insert]
        event: [
            { edit: insertchar value: '7' }
            { send: executehostcommand cmd: 'task_preview_update' }
            { send: repaint }
        ]
    }
    {
        name: task_preview_digit_8
        modifier: none
        keycode: char_8
        mode: [emacs vi_insert]
        event: [
            { edit: insertchar value: '8' }
            { send: executehostcommand cmd: 'task_preview_update' }
            { send: repaint }
        ]
    }
    {
        name: task_preview_digit_9
        modifier: none
        keycode: char_9
        mode: [emacs vi_insert]
        event: [
            { edit: insertchar value: '9' }
            { send: executehostcommand cmd: 'task_preview_update' }
            { send: repaint }
        ]
    }
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
