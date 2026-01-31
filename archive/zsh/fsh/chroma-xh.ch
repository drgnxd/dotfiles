# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for xh (Friendly and fast tool for sending HTTP requests)
# Provides syntax highlighting for xh command options and subcommands
# Reference: https://github.com/ducaale/xh (2025-01-30)

chroma/xh() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style

    (( __first_call )) && {
        FAST_HIGHLIGHT[chroma-xh-counter]=0
        FAST_HIGHLIGHT[chroma-xh-counter-all]=1
        FAST_HIGHLIGHT[chroma-xh-subcommand-seen]=0
        return 1
    }

    (( FAST_HIGHLIGHT[chroma-xh-counter-all] += 1, __start=__start_pos-${#PREBUFFER}, __end=__end_pos-${#PREBUFFER} ))

    case "$__wrd" in
        # HTTP methods (positional)
        GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS|TRACE)
            __style=${FAST_THEME_NAME}subcommand
            ;;
        # Long options (with or without =value)
        --*=*|--*)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        # Short options
        -*)
            __style=${FAST_THEME_NAME}single-hyphen-option
            ;;
        # URL-like patterns
        http://*|https://*)
            __style=${FAST_THEME_NAME}path
            ;;
        # Files and directories
        *)
            if [[ -e "$__wrd" ]]; then
                [[ -d "$__wrd" ]] && __style=${FAST_THEME_NAME}path-to-dir || __style=${FAST_THEME_NAME}path
            else
                __style=${FAST_THEME_NAME}default
            fi
            ;;
    esac

    [[ -n "$__style" ]] && (( __start >= 0 )) && reply+=("$__start $__end ${FAST_HIGHLIGHT_STYLES[$__style]}")

    return 0
}
