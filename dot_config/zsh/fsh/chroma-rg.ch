# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for ripgrep (rg)
# Provides syntax highlighting for ripgrep command options and arguments

chroma/rg() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style

    (( __first_call )) && {
        FAST_HIGHLIGHT[chroma-rg-counter]=0
        FAST_HIGHLIGHT[chroma-rg-counter-all]=1
        FAST_HIGHLIGHT[chroma-rg-pattern-seen]=0
        return 1
    }

    (( FAST_HIGHLIGHT[chroma-rg-counter-all] += 1, __start=__start_pos-${#PREBUFFER}, __end=__end_pos-${#PREBUFFER} ))

    # Highlighting logic for rg arguments
    case "$__wrd" in
        # Long options
        --after-context|--before-context|--context|--color|--colors|--column|--context-separator|\
        --count|--count-matches|--debug|--dfa-size-limit|--encoding|--engine|--file|--files|\
        --files-with-matches|--files-without-match|--fixed-strings|--follow|--glob|--glob-case-insensitive|\
        --heading|--hidden|--iglob|--ignore-case|--ignore-file|--ignore-file-case-insensitive|\
        --include-zero|--invert-match|--json|--line-number|--line-regexp|--max-columns|--max-count|\
        --max-depth|--max-filesize|--mmap|--multiline|--multiline-dotall|--no-config|--no-ignore|\
        --no-ignore-dot|--no-ignore-exclude|--no-ignore-files|--no-ignore-global|--no-ignore-messages|\
        --no-ignore-parent|--no-ignore-vcs|--no-messages|--no-pcre2-unicode|--null|--null-data|\
        --one-file-system|--only-matching|--passthru|--path-separator|--pcre2|--pre|--pre-glob|\
        --pretty|--quiet|--regex-size-limit|--regexp|--replace|--search-zip|--smart-case|--sort|\
        --sortr|--stats|--text|--threads|--trim|--type|--type-add|--type-clear|--type-list|\
        --type-not|--unrestricted|--vimgrep|--with-filename|--word-regexp)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        # Short options
        -[ACBcEeFfgHhiIjLlmMNnopqRrsStuUvwxz0]*)
            __style=${FAST_THEME_NAME}single-hyphen-option
            ;;
        # Values after = in options
        --*=*)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        # Search pattern (first non-option argument)
        *)
            if (( FAST_HIGHLIGHT[chroma-rg-pattern-seen] == 0 )) && [[ "$__wrd" != -* ]]; then
                __style=${FAST_THEME_NAME}mathnum
                FAST_HIGHLIGHT[chroma-rg-pattern-seen]=1
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
