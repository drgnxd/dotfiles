# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for zk (zettelkasten note-taking assistant)
# Provides syntax highlighting for zk command options and subcommands

chroma/zk() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style

    (( __first_call )) && {
        FAST_HIGHLIGHT[chroma-zk-counter]=0
        FAST_HIGHLIGHT[chroma-zk-counter-all]=1
        FAST_HIGHLIGHT[chroma-zk-subcommand-seen]=0
        return 1
    }

    (( FAST_HIGHLIGHT[chroma-zk-counter-all] += 1, __start=__start_pos-${#PREBUFFER}, __end=__end_pos-${#PREBUFFER} ))

    # Highlighting logic for zk arguments
    case "$__wrd" in
        # Subcommands (first non-option argument)
        new|list|ls|edit|index|tag|graph|init|config|help|sync)
            if (( FAST_HIGHLIGHT[chroma-zk-subcommand-seen] == 0 )); then
                __style=${FAST_THEME_NAME}subcommand
                FAST_HIGHLIGHT[chroma-zk-subcommand-seen]=1
            else
                __style=${FAST_THEME_NAME}default
            fi
            ;;
        # Global options
        --notebook-dir|--no-input|--help|--version|--format|--header|--interactive|\
        --limit|--match|--match-strategy|--orphan|--related|--sort|--tag)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        # Short options
        -[dfhilmnst]*)
            __style=${FAST_THEME_NAME}single-hyphen-option
            ;;
        # Values after = in options
        --*=*)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        # Paths or note IDs
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
