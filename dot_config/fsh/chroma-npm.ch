# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for npm

(( next_word = 2 | 8192 ))

local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
local __style

(( __first_call )) && {
    FAST_HIGHLIGHT[chroma-npm-counter]=0
    FAST_HIGHLIGHT[chroma-npm-counter-all]=1
    FAST_HIGHLIGHT[chroma-npm-subcommand-seen]=0
    return 1
}

(( FAST_HIGHLIGHT[chroma-npm-counter-all] += 1, __start=__start_pos-${#PREBUFFER}, __end=__end_pos-${#PREBUFFER} ))

case "$__wrd" in
    # Subcommands
    access|adduser|audit|bin|bugs|cache|ci|completion|config|dedupe|deprecate|diff|dist-tag|docs|doctor|edit|exec|explain|explore|find-dupes|fund|get|help|hook|init|install|install-ci-test|install-test|link|ll|login|logout|ls|org|outdated|owner|pack|ping|pkg|prefix|profile|prune|publish|query|rebuild|repo|restart|root|run|run-script|search|set|shrinkwrap|star|stars|start|stop|team|test|token|uninstall|unpublish|update|version|view|whoami|i|un|t)
        if (( FAST_HIGHLIGHT[chroma-npm-subcommand-seen] == 0 )); then
            __style=${FAST_THEME_NAME}subcommand
            FAST_HIGHLIGHT[chroma-npm-subcommand-seen]=1
        else
            __style=${FAST_THEME_NAME}default
        fi
        ;;
    # Options
    --version|--help|--save|--save-dev|--global|--force|--json|--parseable|--long|--prefix|--userconfig|--globalconfig|--scripts-prepend-node-path|--no-optional|--no-shrinkwrap|--no-package-lock|--only|--dry-run|--silent|--verbose|--quiet)
        __style=${FAST_THEME_NAME}double-hyphen-option
        ;;
    -[gSDfE?v])
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
