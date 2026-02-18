
# Taskwarrior preview wrapper (lazy-loaded)

def task_preview_message [] {
    let msg = ($env | get --optional TASK_PREVIEW_MESSAGE | default '')
    if ($msg | is-empty) {
        return ''
    }
    $'(ansi yellow)($msg)(ansi reset)'
}

def task_preview_base_left [] {
    let base_cmd = ($env | get --optional TASK_PREVIEW_BASE_PROMPT_LEFT | default null)
    if $base_cmd == null {
        return ''
    }
    try { do $base_cmd } catch { $base_cmd }
}

export def --env task_preview_enable [] {
    let current_left = ($env | get --optional PROMPT_COMMAND | default null)
    $env.TASK_PREVIEW_BASE_PROMPT_LEFT = $current_left
    $env.TASK_PREVIEW_MESSAGE = ''

    $env.PROMPT_COMMAND = {||
        let base = (task_preview_base_left)
        let preview = (task_preview_message)
        if ($preview | is-empty) {
            $base
        } else if ($base | is-empty) {
            $preview
        } else {
            $'($preview)
($base)'
        }
    }
}

export def --env task_preview_update [buffer?: string] {
    let current = if ($buffer | is-not-empty) { $buffer } else { (try { commandline } catch { '' }) }
    let trimmed = ($current | str trim --left)

    if ($trimmed | is-empty) {
        $env.TASK_PREVIEW_MESSAGE = ''
        return
    }

    if not ($trimmed | str starts-with 't') {
        $env.TASK_PREVIEW_MESSAGE = ''
        return
    }

    let words = ($trimmed | split row ' ' | where $it != '')
    if ($words | is-empty) {
        $env.TASK_PREVIEW_MESSAGE = ''
        return
    }

    let cmd = ($words | first)
    if ($cmd != 'task' and $cmd != 't') {
        $env.TASK_PREVIEW_MESSAGE = ''
        return
    }

    overlay use $taskwarrior_module
    taskwarrior_preview_update $trimmed
}

export def --env task_preview_clear [] {
    $env.TASK_PREVIEW_MESSAGE = ''
}

export def --env task_preview_insert_char [ch: string] {
    overlay use $taskwarrior_module
    taskwarrior_preview_insert_char $ch
}

export def --env task_preview_backspace [] {
    overlay use $taskwarrior_module
    taskwarrior_preview_backspace
}

export def --env task [...args] {
    overlay use $taskwarrior_module
    taskwarrior_run ...$args
}

export def --env t [...args] {
    overlay use $taskwarrior_module
    taskwarrior_run ...$args
}
