# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for bat (cat with syntax highlighting)
# Provides syntax highlighting for bat command options and arguments

chroma/bat() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style

    (( __first_call )) && {
        FAST_HIGHLIGHT[chroma-bat-counter]=0
        FAST_HIGHLIGHT[chroma-bat-counter-all]=1
        return 1
    }

    (( FAST_HIGHLIGHT[chroma-bat-counter-all] += 1, __start=__start_pos-${#PREBUFFER}, __end=__end_pos-${#PREBUFFER} ))

    # Highlighting logic for bat arguments
    case "$__wrd" in
        # Long options
        --show-all|--nonprintable|--language|--line-range|--highlight-line|--file-name|\
        --diff|--diff-context|--tabs|--wrap|--terminal-width|--number|--color|--italic-text|\
        --decorations|--paging|--pager|--map-syntax|--theme|--theme-dark|--theme-light|--force-colorization|--strip-ansi|--list-themes|--list-languages|\
        --config-file|--config-dir|--cache-dir|--generate-config-file|--acknowledgements|\
        --plain|--no-paging|--style)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        # Short options (letters, digits and common single-char flags)
        -[0-9A-Za-z@]*)
            __style=${FAST_THEME_NAME}single-hyphen-option
            ;;
        # Values after = in options
        --*=*)
            __style=${FAST_THEME_NAME}double-hyphen-option
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
