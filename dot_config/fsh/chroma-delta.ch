# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for git-delta (syntax-highlighting pager for git and diff output)
# Provides syntax highlighting for delta command options

chroma/delta() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style

    (( __first_call )) && {
        FAST_HIGHLIGHT[chroma-delta-counter]=0
        FAST_HIGHLIGHT[chroma-delta-counter-all]=1
        return 1
    }

    (( FAST_HIGHLIGHT[chroma-delta-counter-all] += 1, __start=__start_pos-${#PREBUFFER}, __end=__end_pos-${#PREBUFFER} ))

    # Highlighting logic for delta arguments
    case "$__wrd" in
        # Long options (comprehensive list of commonly used options)
        --color-only|--commit-decoration-style|--commit-style|--dark|--diff-highlight|\
        --diff-so-fancy|--features|--file-added-label|--file-copied-label|--file-decoration-style|\
        --file-modified-label|--file-removed-label|--file-renamed-label|--file-style|\
        --grep-context-line-style|--grep-file-style|--grep-line-number-style|--grep-match-line-style|\
        --grep-match-word-style|--grep-separator-symbol|--help|--hunk-header-decoration-style|\
        --hunk-header-file-style|--hunk-header-line-number-style|--hunk-header-style|\
        --hyperlinks|--hyperlinks-file-link-format|--inline-hint-style|--inspect-raw-lines|\
        --keep-plus-minus-markers|--light|--line-buffer-size|--line-fill-method|--line-numbers|\
        --line-numbers-left-format|--line-numbers-left-style|--line-numbers-minus-style|\
        --line-numbers-plus-style|--line-numbers-right-format|--line-numbers-right-style|\
        --line-numbers-zero-style|--list-languages|--list-syntax-themes|--map-styles|\
        --max-line-distance|--max-line-length|--merge-conflict-begin-symbol|\
        --merge-conflict-end-symbol|--merge-conflict-ours-diff-header-decoration-style|\
        --merge-conflict-ours-diff-header-style|--merge-conflict-theirs-diff-header-decoration-style|\
        --merge-conflict-theirs-diff-header-style|--minus-emph-style|--minus-empty-line-marker-style|\
        --minus-non-emph-style|--minus-style|--navigate|--navigate-regex|--no-gitconfig|\
        --pager|--paging|--parse-ansi|--plus-emph-style|--plus-empty-line-marker-style|\
        --plus-non-emph-style|--plus-style|--raw|--relative-paths|--right-arrow|--show-colors|\
        --show-config|--show-syntax-themes|--show-themes|--side-by-side|--syntax-theme|\
        --tabs|--true-color|--version|--whitespace-error-style|--width|--word-diff-regex|\
        --wrap-left-symbol|--wrap-max-lines|--wrap-right-percent|--wrap-right-prefix-symbol|\
        --wrap-right-symbol|--zero-style)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        # Short options
        -[dnpsw]*)
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
