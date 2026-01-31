# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for uv (Python package manager)
# Provides syntax highlighting for uv command options and subcommands
# Reference: https://docs.astral.sh/uv/reference/cli/ (2025-01-30)

chroma/uv() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style

    (( __first_call )) && {
        FAST_HIGHLIGHT[chroma-uv-counter]=0
        FAST_HIGHLIGHT[chroma-uv-counter-all]=1
        FAST_HIGHLIGHT[chroma-uv-subcommand-seen]=0
        return 1
    }

    (( FAST_HIGHLIGHT[chroma-uv-counter-all] += 1, __start=__start_pos-${#PREBUFFER}, __end=__end_pos-${#PREBUFFER} ))

    case "$__wrd" in
        # Core subcommands (pip replacement)
        pip|add|remove|sync|lock|export|tree|venv|run|init)
            if (( FAST_HIGHLIGHT[chroma-uv-subcommand-seen] == 0 )); then
                __style=${FAST_THEME_NAME}subcommand
                FAST_HIGHLIGHT[chroma-uv-subcommand-seen]=1
            else
                __style=${FAST_THEME_NAME}default
            fi
            ;;
        # Python version management
        python|"python pin"|"python install"|"python uninstall"|"python list"|"python find")
            if (( FAST_HIGHLIGHT[chroma-uv-subcommand-seen] == 0 )); then
                __style=${FAST_THEME_NAME}subcommand
                FAST_HIGHLIGHT[chroma-uv-subcommand-seen]=1
            else
                __style=${FAST_THEME_NAME}default
            fi
            ;;
        # Build and publish
        build|publish)
            if (( FAST_HIGHLIGHT[chroma-uv-subcommand-seen] == 0 )); then
                __style=${FAST_THEME_NAME}subcommand
                FAST_HIGHLIGHT[chroma-uv-subcommand-seen]=1
            else
                __style=${FAST_THEME_NAME}default
            fi
            ;;
        # Tool management
        tool|"tool run"|"tool install"|"tool uninstall"|"tool upgrade"|"tool list"|"tool update-shell")
            if (( FAST_HIGHLIGHT[chroma-uv-subcommand-seen] == 0 )); then
                __style=${FAST_THEME_NAME}subcommand
                FAST_HIGHLIGHT[chroma-uv-subcommand-seen]=1
            else
                __style=${FAST_THEME_NAME}default
            fi
            ;;
        # Cache and self management
        cache|"cache dir"|"cache clean"|"cache prune"|self|"self update")
            if (( FAST_HIGHLIGHT[chroma-uv-subcommand-seen] == 0 )); then
                __style=${FAST_THEME_NAME}subcommand
                FAST_HIGHLIGHT[chroma-uv-subcommand-seen]=1
            else
                __style=${FAST_THEME_NAME}default
            fi
            ;;
        # Utility commands
        version|help)
            if (( FAST_HIGHLIGHT[chroma-uv-subcommand-seen] == 0 )); then
                __style=${FAST_THEME_NAME}subcommand
                FAST_HIGHLIGHT[chroma-uv-subcommand-seen]=1
            else
                __style=${FAST_THEME_NAME}default
            fi
            ;;
        # Long options (with or without =value)
        --*=*|--*)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        # Short options
        -*)
            __style=${FAST_THEME_NAME}single-hyphen-option
            ;;
        # Files and directories
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
