# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for docker-compose (Docker Compose CLI)
# Provides syntax highlighting for docker-compose command options and subcommands
# Reference: https://docs.docker.com/compose/reference/ (2025-01-30)

chroma/docker-compose() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style

    (( __first_call )) && {
        FAST_HIGHLIGHT[chroma-docker-compose-counter]=0
        FAST_HIGHLIGHT[chroma-docker-compose-counter-all]=1
        FAST_HIGHLIGHT[chroma-docker-compose-subcommand-seen]=0
        return 1
    }

    (( FAST_HIGHLIGHT[chroma-docker-compose-counter-all] += 1, __start=__start_pos-${#PREBUFFER}, __end=__end_pos-${#PREBUFFER} ))

    case "$__wrd" in
        # Core subcommands
        up|down|build|ps|logs|exec|run|config|images|port|push|pull|restart|rm|start|stop|top|unpause|pause|create|events|kill|ls|pause|unpause|version|wait)
            if (( FAST_HIGHLIGHT[chroma-docker-compose-subcommand-seen] == 0 )); then
                __style=${FAST_THEME_NAME}subcommand
                FAST_HIGHLIGHT[chroma-docker-compose-subcommand-seen]=1
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
