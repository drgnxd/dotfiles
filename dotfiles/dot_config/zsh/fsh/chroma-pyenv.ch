# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for pyenv

chroma/pyenv() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style

    (( __first_call )) && {
        FAST_HIGHLIGHT[chroma-pyenv-counter]=0
        FAST_HIGHLIGHT[chroma-pyenv-counter-all]=1
        FAST_HIGHLIGHT[chroma-pyenv-subcommand-seen]=0
        return 1
    }

    (( FAST_HIGHLIGHT[chroma-pyenv-counter-all] += 1, __start=__start_pos-${#PREBUFFER}, __end=__end_pos-${#PREBUFFER} ))

    case "$__wrd" in
        # Subcommands
        commands|local|global|shell|install|uninstall|rehash|version|versions|which|whence|init|exec|root|prefix|hooks|shims)
            if (( FAST_HIGHLIGHT[chroma-pyenv-subcommand-seen] == 0 )); then
                __style=${FAST_THEME_NAME}subcommand
                FAST_HIGHLIGHT[chroma-pyenv-subcommand-seen]=1
            else
                __style=${FAST_THEME_NAME}default
            fi
            ;;
        # Options
        --help|--version)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        -*)
            __style=${FAST_THEME_NAME}single-hyphen-option
            ;;
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
