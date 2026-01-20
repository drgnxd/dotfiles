# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for lazygit (simple terminal UI for git commands)
# Provides syntax highlighting for lazygit command options and arguments

chroma/lazygit() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style

    (( __first_call )) && {
        FAST_HIGHLIGHT[chroma-lazygit-counter]=0
        FAST_HIGHLIGHT[chroma-lazygit-counter-all]=1
        return 1
    }

    (( FAST_HIGHLIGHT[chroma-lazygit-counter-all] += 1, __start=__start_pos-${#PREBUFFER}, __end=__end_pos-${#PREBUFFER} ))

    # Highlighting logic for lazygit arguments
    case "$__wrd" in
        # Long options
        --config|--custom-config|--debug|--filter|--git-dir|--help|--logs|--print-config-dir|\
        --print-default-config|--use-config-dir|--use-config-file|--version|--work-tree)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        # Short options
        -[cdghlfpvw]*)
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
