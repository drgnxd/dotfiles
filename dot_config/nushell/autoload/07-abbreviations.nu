# Fish-like abbreviation expansion for the line editor.
#
# Expands aliases typed at command position when Space or Enter is pressed.
# Space: expand in place, insert space, continue editing.
# Enter: expand in place, execute immediately.
#
# Key design decisions:
# - Uses a SINGLE executehostcommand per keybinding (Nushell #12045:
#   multiple executehostcommand events only execute the first one).
# - Enter uses `commandline edit --replace --accept` to atomically
#   replace the buffer and execute, avoiding the need for a separate
#   `{ send: enter }` event (which caused the "long-press Enter" bug).
# - Space handling inserts the space character inside the same function
#   to avoid the multi-event issue.

const nu_abbr_command_wrappers = [sudo doas command builtin env time noglob]
const nu_abbr_token_boundaries = ['|' ';' '&' '(' ')' '[' ']' '{' '}']
const nu_abbr_explicit_map = {
    lg: 'lazygit'
    oc: 'opencode'
    ocd: 'opencode --continue'
    t: 'task'
}

def nu_abbr_build_alias_map [] {
    let alias_map = (
        scope aliases
        | reduce -f {} { |row, acc|
            $acc | merge { ($row.name): $row.expansion }
        }
    )

    $alias_map | merge $nu_abbr_explicit_map
}

$env.NU_ABBR_ALIAS_MAP = (nu_abbr_build_alias_map)

def --env nu_abbr_refresh_alias_map [] {
    $env.NU_ABBR_ALIAS_MAP = (nu_abbr_build_alias_map)
}

def nu_abbr_alias_map [] {
    $env.NU_ABBR_ALIAS_MAP
}

def nu_abbr_is_word_boundary [char: string] {
    ($char =~ '\s') or ($nu_abbr_token_boundaries | any { |boundary| $boundary == $char })
}

def nu_abbr_current_token [buffer: string, cursor: int] {
    let before_cursor = if $cursor <= 0 {
        ''
    } else {
        $buffer | str substring 0..($cursor - 1)
    }
    let after_cursor = ($buffer | str substring $cursor..)

    if ($before_cursor | is-empty) {
        return null
    }

    let trimmed_before = ($before_cursor | str trim --right)
    if $trimmed_before != $before_cursor {
        return null
    }

    if ($after_cursor | is-not-empty) {
        let next_char = ($after_cursor | str substring 0..0)
        if not (nu_abbr_is_word_boundary $next_char) {
            return null
        }
    }

    let token = ($trimmed_before | split row -r '\s+' | last)
    if ($token | is-empty) {
        return null
    }

    let end = ($trimmed_before | str length)
    let start = ($end - ($token | str length))
    let context = if $start <= 0 {
        ''
    } else {
        $trimmed_before | str substring 0..($start - 1)
    }

    {
        token: $token
        start: $start
        end: $end
        context: $context
    }
}

def nu_abbr_can_expand [context: string] {
    let trimmed = ($context | str trim --right)
    if ($trimmed | is-empty) {
        return true
    }

    let segment = ($trimmed | split row -r '[|;&(]' | last | str trim)
    if ($segment | is-empty) {
        return true
    }

    let words = ($segment | split row -r '\s+' | where { |word| $word != '' })
    if ($words | is-empty) {
        return true
    }

    $words | all { |word|
        ($nu_abbr_command_wrappers | any { |cmd| $cmd == $word }) or ($word =~ '^[A-Za-z_][A-Za-z0-9_]*=')
    }
}

def nu_abbr_expand_buffer [buffer: string, cursor: int, --submit] {
    let before_cursor = if $cursor <= 0 {
        ''
    } else {
        $buffer | str substring 0..($cursor - 1)
    }
    let after_cursor = ($buffer | str substring $cursor..)
    let token_info = (nu_abbr_current_token $buffer $cursor)

    if $token_info != null and (nu_abbr_can_expand $token_info.context) {
        let expansion = (nu_abbr_alias_map | get -o $token_info.token)
        if $expansion != null {
            let head = if $token_info.start <= 0 {
                ''
            } else {
                $buffer | str substring 0..($token_info.start - 1)
            }
            let separator = if $submit { '' } else { ' ' }
            let new_buffer = $'($head)($expansion)($separator)($after_cursor)'

            return {
                buffer: $new_buffer
                cursor: (($head | str length) + ($expansion | str length) + ($separator | str length))
                expanded: true
                token: $token_info.token
                expansion: $expansion
            }
        }
    }

    if $submit {
        return {
            buffer: $buffer
            cursor: $cursor
            expanded: false
            token: null
            expansion: null
        }
    }

    {
        buffer: $'($before_cursor) ($after_cursor)'
        cursor: ($cursor + 1)
        expanded: false
        token: null
        expansion: null
    }
}

def --env nu_abbr_insert_space [] {
    let buffer = (try { commandline } catch { '' })
    let cursor = (try { commandline get-cursor } catch { ($buffer | str length) })
    let next = (nu_abbr_expand_buffer $buffer $cursor)

    commandline edit --replace $next.buffer
    commandline set-cursor $next.cursor
}

def --env nu_abbr_submit [] {
    let buffer = (try { commandline } catch { '' })
    let cursor = (try { commandline get-cursor } catch { ($buffer | str length) })
    let next = (nu_abbr_expand_buffer $buffer $cursor --submit)

    commandline edit --replace --accept $next.buffer
}

let nu_abbr_keybindings = [
    {
        name: nu_abbr_space
        modifier: none
        keycode: space
        mode: [emacs vi_insert]
        event: { send: executehostcommand cmd: 'nu_abbr_insert_space' }
    }
    {
        name: nu_abbr_enter
        modifier: none
        keycode: enter
        mode: [emacs vi_insert]
        event: { send: executehostcommand cmd: 'nu_abbr_submit' }
    }
]

$env.config.keybindings = (
    ($env.config.keybindings | default [])
    | append $nu_abbr_keybindings
)
