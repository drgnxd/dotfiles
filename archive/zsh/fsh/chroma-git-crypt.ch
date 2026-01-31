# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for git-crypt (transparent encryption/decryption of files in git)
# Provides syntax highlighting for git-crypt command options and subcommands

chroma/git-crypt() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style

    (( __first_call )) && {
        FAST_HIGHLIGHT[chroma-git-crypt-counter]=0
        FAST_HIGHLIGHT[chroma-git-crypt-counter-all]=1
        FAST_HIGHLIGHT[chroma-git-crypt-subcommand-seen]=0
        return 1
    }

    (( FAST_HIGHLIGHT[chroma-git-crypt-counter-all] += 1, __start=__start_pos-${#PREBUFFER}, __end=__end_pos-${#PREBUFFER} ))

    # Highlighting logic for git-crypt arguments
    case "$__wrd" in
        # Subcommands
        init|status|lock|unlock|add-gpg-user|export-key|help|version)
            if (( FAST_HIGHLIGHT[chroma-git-crypt-subcommand-seen] == 0 )); then
                __style=${FAST_THEME_NAME}subcommand
                FAST_HIGHLIGHT[chroma-git-crypt-subcommand-seen]=1
            else
                __style=${FAST_THEME_NAME}default
            fi
            ;;
        # Options
        --help|--version|--force|--key-name|--trusted)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        -[hfkt]*)
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
