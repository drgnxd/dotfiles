# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for chezmoi (dotfile manager)
# Provides syntax highlighting for chezmoi command options and subcommands

chroma/chezmoi() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style

    (( __first_call )) && {
        FAST_HIGHLIGHT[chroma-chezmoi-counter]=0
        FAST_HIGHLIGHT[chroma-chezmoi-counter-all]=1
        FAST_HIGHLIGHT[chroma-chezmoi-subcommand-seen]=0
        return 1
    }

    (( FAST_HIGHLIGHT[chroma-chezmoi-counter-all] += 1, __start=__start_pos-${#PREBUFFER}, __end=__end_pos-${#PREBUFFER} ))

    # Highlighting logic for chezmoi arguments
    case "$__wrd" in
        # Subcommands (first non-option argument)
        add|apply|archive|cat|cd|chattr|completion|data|decrypt|diff|doctor|dump|edit|\
        execute-template|forget|git|help|import|init|manage|managed|merge|merge-all|purge|\
        re-add|remove|rm|secret|source|source-path|state|status|unmanage|unmanaged|update|\
        upgrade|verify)
            if (( FAST_HIGHLIGHT[chroma-chezmoi-subcommand-seen] == 0 )); then
                __style=${FAST_THEME_NAME}subcommand
                FAST_HIGHLIGHT[chroma-chezmoi-subcommand-seen]=1
            else
                __style=${FAST_THEME_NAME}default
            fi
            ;;
        # Global options
        --cache|--color|--config|--config-format|--debug|--destination|--dry-run|--force|\
        --help|--init|--keep-going|--no-pager|--no-tty|--output|--persistent-state|--refresh-externals|\
        --source|--use-builtin-age|--use-builtin-git|--verbose|--version|--working-tree)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        # Short options
        -[cDfhknRSvVw]*)
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
