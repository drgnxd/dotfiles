# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for btop (resource monitor)
# Provides syntax highlighting for btop command options

chroma/btop() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style

    (( __first_call )) && {
        FAST_HIGHLIGHT[chroma-btop-counter]=0
        FAST_HIGHLIGHT[chroma-btop-counter-all]=1
        return 1
    }

    (( FAST_HIGHLIGHT[chroma-btop-counter-all] += 1, __start=__start_pos-${#PREBUFFER}, __end=__end_pos-${#PREBUFFER} ))

    # Highlighting logic for btop arguments
    case "$__wrd" in
        # Long options
        --help|--version|--debug|--preset|--utf-force|--low-color|--no-color|--tty_on)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        # Short options (letters, digits and common single-char flags)
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
