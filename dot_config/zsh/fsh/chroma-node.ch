# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for node
# Provides syntax highlighting for node options/flags and simple subcommands

chroma/node() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style __start __end

    (( __first_call )) && {
        FAST_HIGHLIGHT[chroma-node-subcommand-seen]=0
        return 1
    }

    (( __start = __start_pos - ${#PREBUFFER}, __end = __end_pos - ${#PREBUFFER} ))

    case "$__wrd" in
        --version|-v|--help|-h|repl|run)
            if (( FAST_HIGHLIGHT[chroma-node-subcommand-seen] == 0 )); then
                __style=${FAST_THEME_NAME}subcommand
                FAST_HIGHLIGHT[chroma-node-subcommand-seen]=1
            else
                __style=${FAST_THEME_NAME}default
            fi
            ;;
        -e|--eval|-p|--print)
            __style=${FAST_THEME_NAME}single-hyphen-option
            ;;
        --inspect*|--trace-warnings|--stack-trace-limit|--trace-deprecation|--no-deprecation)
            __style=${FAST_THEME_NAME}double-hyphen-option
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
