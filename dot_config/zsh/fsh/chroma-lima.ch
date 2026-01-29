# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for lima (macOS lightweight VMs)
# Highlights lima subcommands and instance names/options

chroma/lima() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style __start __end

    (( __first_call )) && {
        FAST_HIGHLIGHT[chroma-lima-subcommand-seen]=0
        return 1
    }

    (( __start = __start_pos - ${#PREBUFFER}, __end = __end_pos - ${#PREBUFFER} ))

    case "$__wrd" in
        start|stop|restart|list|ls|shell|exec|ssh|cp|mount|umount|delete|rm|edit|logs|status|create)
            if (( FAST_HIGHLIGHT[chroma-lima-subcommand-seen] == 0 )); then
                __style=${FAST_THEME_NAME}subcommand
                FAST_HIGHLIGHT[chroma-lima-subcommand-seen]=1
            else
                __style=${FAST_THEME_NAME}default
            fi
            ;;
        [a-zA-Z0-9_-]*)
            __style=${FAST_THEME_NAME}default
            ;;
        --name|--workdir|--tty|--mount|--cpu|--memory)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        -[a-zA-Z]*)
            __style=${FAST_THEME_NAME}single-hyphen-option
            ;;
        *)
            if [[ -e "$__wrd" ]]; then
                [[ -d "$__wrd" ]] && __style=${FAST_THEME_NAME}path-to-dir || __style=${FAST_THEME_NAME}path
            else
                __style=${FAST_THEME_NAME}default
            fi
            ;;
    esac

    [[ -n "$__style" && __start -ge 0 ]] && reply+=("$__start $__end ${FAST_HIGHLIGHT_STYLES[$__style]}")

    return 0
}
