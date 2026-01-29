# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for fzf (command-line fuzzy finder)
# Provides syntax highlighting for fzf command options

chroma/fzf() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style

    (( __first_call )) && {
        FAST_HIGHLIGHT[chroma-fzf-counter]=0
        FAST_HIGHLIGHT[chroma-fzf-counter-all]=1
        return 1
    }

    (( FAST_HIGHLIGHT[chroma-fzf-counter-all] += 1, __start=__start_pos-${#PREBUFFER}, __end=__end_pos-${#PREBUFFER} ))

    # Highlighting logic for fzf arguments
    case "$__wrd" in
        # Long options (expanded from local manpage)
        --accept-nth|--algo|--ambidouble|--ansi|--bash|--bind|--black|--border|--border-label|--border-label-pos|--brief|\
        --color|--column|--cycle|--delimiter|--disabled|--ellipsis|--exact|--exit-0|--expect|--extended|--filepath-word|\
        --filter|--fish|--footer|--footer-border|--footer-label|--footer-label-pos|--freeze-left|--freeze-right|--gap|\
        --gap-line|--ghost|--graph|--gutter|--gutter-raw|--header|--header-border|--header-first|--header-label|\
        --header-label-pos|--header-lines|--header-lines-border|--height|--help|--highlight-line|--history|--history-size|\
        --hscroll-off|--ignore-case|--info|--info-command|--input-border|--input-label|--input-label-pos|--jump-labels|\
        --keep-right|--layout|--line-number|--list-border|--list-label|--list-label-pos|--listen|--listen-unsafe|--literal|\
        --man|--margin|--marker|--marker-multi-line|--min-height|--multi|--no-bold|--no-clear|--no-color|--no-expect|\
        --no-extended|--no-header-lines-border|--no-heading|--no-hscroll|--no-ignore-case|--no-info|--no-input|--no-list-border|\
        --no-mouse|--no-multi|--no-multi-line|--no-scrollbar|--no-separator|--no-sort|--no-tty-default|--no-unicode|--nth|\
        --oneline|--padding|--pointer|--preview|--preview-border|--preview-label|--preview-label-pos|--preview-window|\
        --print-query|--print0|--prompt|--query|--raw|--read0|--reverse|--scheme|--scroll-off|--scrollbar|--select-1|\
        --separator|--smart-case|--style|--sync|--tabstop|--tac|--tail|--tiebreak|--tmux|--track|--tty-|--unix-socket|--version|\
        --walker|--walker-root|--walker-skip|--with-nth|--with-shell|--wrap|--wrap-sign|--zsh)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        # Short options — accept any common short option to reduce misses
        -[0-9A-Za-z]*)
            __style=${FAST_THEME_NAME}single-hyphen-option
            ;;
        # Values after = in options
        --*=*)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        *)
            __style=${FAST_THEME_NAME}default
            ;;
    esac

    [[ -n "$__style" ]] && (( __start >= 0 )) && reply+=("$__start $__end ${FAST_HIGHLIGHT_STYLES[$__style]}")

    return 0
}
