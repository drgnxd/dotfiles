# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for task/taskwarrior (feature-rich console based todo list manager)
# Provides syntax highlighting for task command options and subcommands

# Global array for cached task IDs (populated on first call per command line)
typeset -ga CHROMA_TASK_IDS

chroma/task() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style="" __start __end

    # First call: initialize state and load cache
    if (( __first_call )); then
        FAST_HIGHLIGHT[chroma-task-subcommand-seen]=0
        # Load IDs from cache file
        local cache_file="$HOME/.cache/taskwarrior/ids.list"
        if [[ -f "$cache_file" ]]; then
            CHROMA_TASK_IDS=( ${(f)"$(<"$cache_file")"} )
        else
            CHROMA_TASK_IDS=()
        fi
        # Return 1 to let chroma handle all tokens (including command name)
        return 1
    fi

    (( __start = __start_pos - ${#PREBUFFER}, __end = __end_pos - ${#PREBUFFER} ))

    # Subcommands (including shell reserved words like 'done')
    # Check this FIRST so 'done' gets highlighted before falling through
    if [[ "$__wrd" =~ ^(add|annotate|append|calendar|completed|config|context|count|delete|denotate|done|duplicate|edit|execute|export|help|ids|import|information|list|log|logo|ls|modify|next|prepend|purge|ready|redo|show|start|stats|stop|summary|sync|tags|timesheet|undo|uuids|version|mod|rm|del|info|calc)$ ]]; then
        if (( FAST_HIGHLIGHT[chroma-task-subcommand-seen] == 0 )); then
            __style=${FAST_THEME_NAME}subcommand
            FAST_HIGHLIGHT[chroma-task-subcommand-seen]=1
        else
            __style=${FAST_THEME_NAME}default
        fi
    # Task ID patterns (numeric)
    elif [[ "$__wrd" =~ ^[0-9]+$ ]]; then
        # Check if ID exists in cache
        if (( ${#CHROMA_TASK_IDS} > 0 )) && (( ${CHROMA_TASK_IDS[(Ie)$__wrd]} )); then
            __style=${FAST_THEME_NAME}mathnum
        else
            __style=${FAST_THEME_NAME}incorrect-subtle
        fi
    # UUID pattern
    elif [[ "$__wrd" =~ ^[0-9a-fA-F-]{8,}$ ]]; then
        __style=${FAST_THEME_NAME}mathnum
    # Attributes with trailing colon
    elif [[ "$__wrd" =~ ^(project|priority|due|wait|until|scheduled|recur|depends|tags|description|status|entry|end|modified|start|estimate|pro|pri|du|wa|sch|dep|desc|est):$ ]]; then
        __style=${FAST_THEME_NAME}assign
    # Attribute assignments (key:value)
    elif [[ "$__wrd" =~ ^(project|priority|due|wait|until|scheduled|recur|depends|tags|description|status|entry|end|modified|start|estimate|pro|pri|du|wa|sch|dep|desc|est):.+$ ]]; then
        __style=${FAST_THEME_NAME}assign
    # Status values
    elif [[ "$__wrd" =~ ^(pending|completed|deleted|waiting|recurring)$ ]]; then
        __style=${FAST_THEME_NAME}mathnum
    # Priority values
    elif [[ "$__wrd" =~ ^[HML]$ ]]; then
        __style=${FAST_THEME_NAME}mathnum
    # rc: options
    elif [[ "$__wrd" == rc:* || "$__wrd" == rc.*=* ]]; then
        __style=${FAST_THEME_NAME}assign
    # Double-hyphen options
    elif [[ "$__wrd" == --* ]]; then
        __style=${FAST_THEME_NAME}double-hyphen-option
    # Single-hyphen options
    elif [[ "$__wrd" == -* ]]; then
        __style=${FAST_THEME_NAME}single-hyphen-option
    # Fallback: plain argument
    else
        __style=${FAST_THEME_NAME}default
    fi

    # Apply highlighting
    if [[ -n "$__style" && $__start -ge 0 ]]; then
        reply+=("$__start $__end ${FAST_HIGHLIGHT_STYLES[$__style]}")
    fi

    # Return 1 to signal this chroma handled the token
    return 1
}
