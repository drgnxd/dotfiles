# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for eza (modern ls replacement)
# Provides syntax highlighting for eza command options and arguments

chroma/eza() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style

    (( __first_call )) && {
        FAST_HIGHLIGHT[chroma-eza-counter]=0
        FAST_HIGHLIGHT[chroma-eza-counter-all]=1
        return 1
    }

    (( FAST_HIGHLIGHT[chroma-eza-counter-all] += 1, __start=__start_pos-${#PREBUFFER}, __end=__end_pos-${#PREBUFFER} ))

    # Highlighting logic for eza arguments
    case "$__wrd" in
        # Long options
        --all|--almost-all|--binary|--bytes|--classify|--color|--color-scale|--color-scale-mode|\
        --icons|--icons-auto|--no-icons|--group-directories-first|--group-directories-last|\
        --git|--git-ignore|--git-repos|--header|--hyperlink|--inode|--links|--long|--modified|\
        --created|--accessed|--no-quotes|--no-permissions|--numeric|--octal-permissions|--only-dirs|\
        --only-files|--reverse|--recurse|--sort|--time|--time-style|--tree|--level|--ignore-glob|\
        --oneline|--grid|--absolute|--across|--width)
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
        # Glob patterns and paths
        *\**|\[*\]|*\?*)
            __style=${FAST_THEME_NAME}globbing
            ;;
        # Regular paths/files
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
