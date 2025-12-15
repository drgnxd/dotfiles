# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for fd (modern find replacement)
# Provides syntax highlighting for fd command options and arguments

chroma/fd() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style

    (( __first_call )) && {
        FAST_HIGHLIGHT[chroma-fd-counter]=0
        FAST_HIGHLIGHT[chroma-fd-counter-all]=1
        FAST_HIGHLIGHT[chroma-fd-pattern-seen]=0
        return 1
    }

    (( FAST_HIGHLIGHT[chroma-fd-counter-all] += 1, __start=__start_pos-${#PREBUFFER}, __end=__end_pos-${#PREBUFFER} ))

    # Highlighting logic for fd arguments
    case "$__wrd" in
        # Long options
        --absolute-path|--base-directory|--case-sensitive|--changed-before|--changed-within|\
        --color|--exec|--exec-batch|--exclude|--extension|--follow|--full-path|--glob|\
        --hidden|--ignore-case|--ignore-file|--list-details|--max-depth|--max-results|\
        --min-depth|--no-ignore|--no-ignore-vcs|--no-ignore-parent|--owner|--prune|--regex|\
        --search-path|--show-errors|--size|--strip-cwd-prefix|--threads|--type)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        # Short options
        -[abdcEeFfgHhiILlpsStuXx0]*)
            __style=${FAST_THEME_NAME}single-hyphen-option
            ;;
        # Values after = in options
        --*=*)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        # Search pattern (first non-option argument)
        *)
            if (( FAST_HIGHLIGHT[chroma-fd-pattern-seen] == 0 )) && [[ "$__wrd" != -* ]]; then
                __style=${FAST_THEME_NAME}mathnum
                FAST_HIGHLIGHT[chroma-fd-pattern-seen]=1
            elif [[ -e "$__wrd" ]]; then
                [[ -d "$__wrd" ]] && __style=${FAST_THEME_NAME}path-to-dir || __style=${FAST_THEME_NAME}path
            else
                __style=${FAST_THEME_NAME}default
            fi
            ;;
    esac

    [[ -n "$__style" ]] && (( __start >= 0 )) && reply+=("$__start $__end ${FAST_HIGHLIGHT_STYLES[$__style]}")

    return 0
}
