# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for gh (GitHub CLI)
# Provides syntax highlighting for gh command options and subcommands

chroma/gh() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style

    (( __first_call )) && {
        FAST_HIGHLIGHT[chroma-gh-counter]=0
        FAST_HIGHLIGHT[chroma-gh-counter-all]=1
        FAST_HIGHLIGHT[chroma-gh-subcommand-seen]=0
        return 1
    }

    (( FAST_HIGHLIGHT[chroma-gh-counter-all] += 1, __start=__start_pos-${#PREBUFFER}, __end=__end_pos-${#PREBUFFER} ))

    # Highlighting logic for gh arguments
    case "$__wrd" in
        # Main subcommands (first non-option argument)
        alias|api|auth|browse|co|codespace|completion|config|cs|extension|gist|gpg-key|\
        issue|label|pr|project|release|repo|run|search|secret|ssh-key|status|variable|workflow)
            if (( FAST_HIGHLIGHT[chroma-gh-subcommand-seen] == 0 )); then
                __style=${FAST_THEME_NAME}subcommand
                FAST_HIGHLIGHT[chroma-gh-subcommand-seen]=1
            else
                __style=${FAST_THEME_NAME}default
            fi
            ;;
        # Secondary subcommands
        create|clone|fork|list|view|edit|close|reopen|merge|comment|delete|approve|review|\
        checks|diff|ready|status|sync|checkout|lock|unlock|add|remove|set-default|setup)
            __style=${FAST_THEME_NAME}subcommand
            ;;
        # Global options
        --help|--version|--repo|--hostname)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        # Short options
        -[hRv]*)
            __style=${FAST_THEME_NAME}single-hyphen-option
            ;;
        # Values after = in options
        --*=*)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        # Options starting with --
        --*)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        *)
            __style=${FAST_THEME_NAME}default
            ;;
    esac

    [[ -n "$__style" ]] && (( __start >= 0 )) && reply+=("$__start $__end ${FAST_HIGHLIGHT_STYLES[$__style]}")

    return 0
}
