# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for pandoc
# Highlights common formats, options and filters

chroma/pandoc() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style __start __end

    (( __first_call )) && {
        FAST_HIGHLIGHT[chroma-pandoc-subcommand-seen]=0
        return 1
    }

    (( __start = __start_pos - ${#PREBUFFER}, __end = __end_pos - ${#PREBUFFER} ))

    case "$__wrd" in
        -f|--from|-t|--to|-o|--output|-s|--standalone|--filter|--metadata|--template|--mathjax|--toc)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        markdown|markdown_strict|markdown_github|gfm|html|html5|docx|pdf|rst|latex)
            __style=${FAST_THEME_NAME}subcommand
            ;;
        -[a-zA-Z]*)
            __style=${FAST_THEME_NAME}single-hyphen-option
            ;;
        --*=*)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        *)
            if [[ -e "$__wrd" ]]; then
                [[ -d "$__wrd" ]] && __style=${FAST_THEME_NAME}path-to-dir || __style=${FAST_THEME_NAME}path
            else
                __style=${FAST_THEME_NAME}default
            fi
            ;;
    esac

    [[ -n "$__style" && __start -ge 0 ]] && reply+=("$__start $__end ${FAST_HIGHLIGHT_STYLES[$__style]}")

    return 0
}
