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
        # Long options
        --algo|--ansi|--bind|--border|--border-label|--border-label-pos|--color|--cycle|\
        --delimiter|--disabled|--ellipsis|--expect|--extended|--filepath-word|--filter|\
        --header|--header-first|--header-lines|--height|--help|--highlight-line|--history|\
        --history-size|--hscroll|--hscroll-off|--info|--jump-labels|--keep-right|--layout|\
        --listen|--literal|--margin|--marker|--min-height|--multi|--no-bold|--no-hscroll|\
        --no-mouse|--no-sort|--no-unicode|--nth|--padding|--phony|--pointer|--preview|\
        --preview-label|--preview-label-pos|--preview-window|--print-query|--print0|\
        --prompt|--query|--read0|--regex|--reverse|--scheme|--scroll-off|--select-1|\
        --separator|--sync|--tabstop|--tac|--tiebreak|--track|--version|--walker|\
        --walker-root|--walker-skip|--with-nth|--with-shell|--wrap)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        # Short options  
        -[0deifmnqx1]*)
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
