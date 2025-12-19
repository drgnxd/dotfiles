# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for task/taskwarrior (feature-rich console based todo list manager)
# Provides syntax highlighting for task command options and subcommands
#
# Note: This chroma overrides shell reserved words (done, do, etc.) when used
# as taskwarrior subcommands by returning 1 to take control of highlighting.

chroma/task() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style __start __end

    (( __first_call )) && {
        FAST_HIGHLIGHT[chroma-task-subcommand-seen]=0
        return 1
    }

    (( __start = __start_pos - ${#PREBUFFER}, __end = __end_pos - ${#PREBUFFER} ))

    # Task ID patterns (numeric or UUID)
    if [[ "$__wrd" =~ ^[0-9]+$ ]]; then
        __style=${FAST_THEME_NAME}mathnum
    elif [[ "$__wrd" =~ ^[0-9a-fA-F-]{8,}$ ]]; then
        __style=${FAST_THEME_NAME}mathnum
    # Subcommands (including shell reserved words like 'done')
    elif [[ "$__wrd" =~ ^(add|annotate|append|calendar|completed|config|context|count|delete|denotate|done|duplicate|edit|execute|export|help|ids|import|information|list|log|logo|ls|modify|next|prepend|purge|ready|redo|show|start|stats|stop|summary|sync|tags|timesheet|undo|uuids|version|mod|rm|del|info|calc)$ ]]; then
        if (( FAST_HIGHLIGHT[chroma-task-subcommand-seen] == 0 )); then
            __style=${FAST_THEME_NAME}subcommand
            FAST_HIGHLIGHT[chroma-task-subcommand-seen]=1
        else
            __style=${FAST_THEME_NAME}default
        fi
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

    # Apply highlighting and return 1 to override default/reserved word highlighting
    if [[ -n "$__style" && $__start -ge 0 ]]; then
        reply+=("$__start $__end ${FAST_HIGHLIGHT_STYLES[$__style]}")
    fi

    # Return 1 to signal that this chroma handled the token completely
    # This prevents fast-syntax-highlighting from applying reserved word styles
    return 1
}
