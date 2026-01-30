# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for ncdu (NCurses Disk Usage)
# Provides syntax highlighting for ncdu command options
# Reference: https://dev.yorhel.nl/ncdu (2025-01-30)

chroma/ncdu() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style

    (( __first_call )) && {
        FAST_HIGHLIGHT[chroma-ncdu-counter]=0
        FAST_HIGHLIGHT[chroma-ncdu-counter-all]=1
        return 1
    }

    (( FAST_HIGHLIGHT[chroma-ncdu-counter-all] += 1, __start=__start_pos-${#PREBUFFER}, __end=__end_pos-${#PREBUFFER} ))

    case "$__wrd" in
        # Long options (with or without =value)
        --*=*|--*)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        # Short options
        -*)
            __style=${FAST_THEME_NAME}single-hyphen-option
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
