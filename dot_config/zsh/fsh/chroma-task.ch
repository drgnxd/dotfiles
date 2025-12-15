# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for task/taskwarrior (feature-rich console based todo list manager)
# Provides syntax highlighting for task command options and subcommands

chroma/task() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style

    (( __first_call )) && {
        FAST_HIGHLIGHT[chroma-task-counter]=0
        FAST_HIGHLIGHT[chroma-task-counter-all]=1
        FAST_HIGHLIGHT[chroma-task-subcommand-seen]=0
        return 1
    }

    (( FAST_HIGHLIGHT[chroma-task-counter-all] += 1, __start=__start_pos-${#PREBUFFER}, __end=__end_pos-${#PREBUFFER} ))

    # Highlighting logic for task arguments
    case "$__wrd" in
        # Main subcommands
        add|annotate|append|calendar|completed|config|context|count|delete|denotate|done|\
        duplicate|edit|execute|export|help|ids|import|information|list|log|logo|ls|\
        modify|next|prepend|purge|ready|redo|show|start|stats|stop|summary|sync|\
        tags|timesheet|undo|uuids|version|\
        mod|rm|del|info|calc)
            if (( FAST_HIGHLIGHT[chroma-task-subcommand-seen] == 0 )); then
                __style=${FAST_THEME_NAME}subcommand
                FAST_HIGHLIGHT[chroma-task-subcommand-seen]=1
            else
                __style=${FAST_THEME_NAME}default
            fi
            ;;
        # Attributes
        project:|priority:|due:|wait:|until:|scheduled:|recur:|depends:|tags:|description:|\
        status:|entry:|end:|modified:|start:|estimate:|\
        pro:|pri:|du:|wa:|sch:|dep:|desc:|est:)
            __style=${FAST_THEME_NAME}assign
            ;;
        # Status values
        pending|completed|deleted|waiting|recurring)
            __style=${FAST_THEME_NAME}mathnum
            ;;
        # Priority values
        H|M|L)
            __style=${FAST_THEME_NAME}mathnum
            ;;
        # Options
        rc:*|rc.*=*)
            __style=${FAST_THEME_NAME}assign
            ;;
        *)
            __style=${FAST_THEME_NAME}default
            ;;
    esac

    [[ -n "$__style" ]] && (( __start >= 0 )) && reply+=("$__start $__end ${FAST_HIGHLIGHT_STYLES[$__style]}")

    return 0
}
