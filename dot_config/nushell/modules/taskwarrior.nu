# Taskwarrior integration (lazy-loaded)

def taskwarrior_has_cmd [cmd: string] {
    (which $cmd | is-not-empty)
}

def taskwarrior_cache_dir [] {
    let cache_home = ($env | get -o XDG_CACHE_HOME | default ($env.HOME | path join ".cache"))
    $cache_home | path join "taskwarrior"
}

def taskwarrior_cache_update [] {
    let update_script = ($env.XDG_CONFIG_HOME | path join "taskwarrior" "hooks" "update_cache.py")
    if not ($update_script | path exists) {
        return
    }
    if not (taskwarrior_has_cmd "uv") {
        return
    }
    do { uv run --quiet --script $update_script --update-only } | ignore
}

def taskwarrior_preview_ids [words: list<string>] {
    mut selected_ids = []
    for w in ($words | skip 1) {
        if ($w =~ '^[0-9]+$') {
            $selected_ids = ($selected_ids | append $w)
        } else if ($w =~ '^[0-9]+-[0-9]+$') {
            let range_parts = ($w | split row "-")
            let start = ($range_parts | first | into int)
            let end = ($range_parts | last | into int)
            let range_start = if ($start > $end) { $end } else { $start }
            let range_end = if ($start > $end) { $start } else { $end }
            for i in $range_start..$range_end {
                $selected_ids = ($selected_ids | append ($i | into string))
            }
        }
    }
    $selected_ids
}

def taskwarrior_preview_message_from_buffer [buffer: string] {
    if ($buffer | is-empty) {
        return ""
    }

    let words = ($buffer | split row " " | where $it != "")
    if ($words | is-empty) {
        return ""
    }

    let cmd = ($words | first)
    if ($cmd != "task" and $cmd != "t") {
        return ""
    }

    let ids = (taskwarrior_preview_ids $words)
    if ($ids | is-empty) {
        return ""
    }

    let desc_file = (taskwarrior_cache_dir | path join "desc.list")
    if not ($desc_file | path exists) {
        return ""
    }

    let uniq_ids = ($ids | uniq)
    let id_set = ($uniq_ids | reduce -f {} { |id, acc| $acc | insert $id true })

    let found = (open $desc_file
        | lines
        | reduce -f {} { |line, acc|
            let parts = ($line | split row ":" -n 2)
            if ($parts | length) == 2 {
                let id = ($parts | get 0)
                if ($id_set | get -o $id | default false) {
                    let desc = ($parts | get 1)
                    $acc | insert $id $desc
                } else {
                    $acc
                }
            } else {
                $acc
            }
        })

    if ($found | is-empty) {
        return ""
    }

    let ordered = ($uniq_ids | sort-by { |id| $id | into int })
    let messages = ($ordered | each { |id|
        let desc = ($found | get -o $id | default "")
        if ($desc | is-empty) { null } else { $"($id):($desc)" }
    } | where $it != null)

    if ($messages | is-empty) {
        return ""
    }

    $messages | str join " | "
}

export def --env taskwarrior_preview_update [buffer?: string] {
    let current = if ($buffer | is-not-empty) { $buffer } else { (try { commandline } catch { "" }) }
    let msg = (taskwarrior_preview_message_from_buffer $current)
    $env.TASK_PREVIEW_MESSAGE = $msg
}

export def --env taskwarrior_preview_clear [] {
    $env.TASK_PREVIEW_MESSAGE = ""
}

export def --env taskwarrior_preview_insert_char [ch: string] {
    let buffer = (try { commandline } catch { "" })
    let cursor = (try { commandline get-cursor } catch { ($buffer | str length) })
    let head = if $cursor <= 0 { "" } else { $buffer | str substring 0..($cursor - 1) }
    let tail = ($buffer | str substring $cursor..)
    let new_buffer = $"($head)($ch)($tail)"

    commandline edit --replace $new_buffer
    commandline set-cursor ($cursor + 1)
    taskwarrior_preview_update $new_buffer
}

export def --env taskwarrior_preview_backspace [] {
    let buffer = (try { commandline } catch { "" })
    let cursor = (try { commandline get-cursor } catch { 0 })
    if $cursor <= 0 {
        return
    }

    let head = ($buffer | str substring 0..($cursor - 1))
    let tail = ($buffer | str substring $cursor..)
    let new_buffer = $"($head)($tail)"

    commandline edit --replace $new_buffer
    commandline set-cursor ($cursor - 1)
    taskwarrior_preview_update $new_buffer
}

export def --env taskwarrior_run [...args] {
    if not (taskwarrior_has_cmd "task") {
        error make { msg: "task not found" }
    }
    ^task ...$args
    let code = $env.LAST_EXIT_CODE
    taskwarrior_cache_update
    taskwarrior_preview_clear
    $env.LAST_EXIT_CODE = $code
}
