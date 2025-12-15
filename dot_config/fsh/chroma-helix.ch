# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for helix (post-modern modal text editor)
# Provides syntax highlighting for helix command options and arguments

chroma/helix() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style

    (( __first_call )) && {
        FAST_HIGHLIGHT[chroma-helix-counter]=0
        FAST_HIGHLIGHT[chroma-helix-counter-all]=1
        return 1
    }

    (( FAST_HIGHLIGHT[chroma-helix-counter-all] += 1, __start=__start_pos-${#PREBUFFER}, __end=__end_pos-${#PREBUFFER} ))

    # Highlighting logic for helix (hx) arguments
    case "$__wrd" in
        # Long options
        --help|--version|--health|--tutor|--grammar|--vsplit|--hsplit|--working-dir|\
        --config|--log)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        # Short options
        -[hvgVHw]*)
            __style=${FAST_THEME_NAME}single-hyphen-option
            ;;
        # Values after = in options
        --*=*)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        # Subcommands
        fetch|build)
            __style=${FAST_THEME_NAME}subcommand
            ;;
        # File paths
        *)
            if [[ -e "$__wrd" ]]; then
                [[ -f "$__wrd" ]] && __style=${FAST_THEME_NAME}path || __style=${FAST_THEME_NAME}path-to-dir
            else
                __style=${FAST_THEME_NAME}default
            fi
            ;;
    esac

    [[ -n "$__style" ]] && (( __start >= 0 )) && reply+=("$__start $__end ${FAST_HIGHLIGHT_STYLES[$__style]}")

    return 0
}

# Alias for hx command
chroma/hx() {
    chroma/helix "$@"
}
