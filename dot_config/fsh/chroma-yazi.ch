# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for yazi (terminal file manager)
# Provides syntax highlighting for yazi command options and arguments

chroma/yazi() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style

    (( __first_call )) && {
        FAST_HIGHLIGHT[chroma-yazi-counter]=0
        FAST_HIGHLIGHT[chroma-yazi-counter-all]=1
        return 1
    }

    (( FAST_HIGHLIGHT[chroma-yazi-counter-all] += 1, __start=__start_pos-${#PREBUFFER}, __end=__end_pos-${#PREBUFFER} ))

    # Highlighting logic for yazi arguments
    case "$__wrd" in
        # Long options
        --cwd-file|--chooser-file|--clear-cache|--client-id|--debug|--entry|--local-events|\
        --remote-events|--version|--help)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        # Short options
        -[hV]*)
            __style=${FAST_THEME_NAME}single-hyphen-option
            ;;
        # Values after = in options
        --*=*)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        # Paths
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
