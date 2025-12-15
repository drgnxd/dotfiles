# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for tmux (terminal multiplexer)
# Provides syntax highlighting for tmux command options and subcommands

chroma/tmux() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style

    (( __first_call )) && {
        FAST_HIGHLIGHT[chroma-tmux-counter]=0
        FAST_HIGHLIGHT[chroma-tmux-counter-all]=1
        FAST_HIGHLIGHT[chroma-tmux-subcommand-seen]=0
        return 1
    }

    (( FAST_HIGHLIGHT[chroma-tmux-counter-all] += 1, __start=__start_pos-${#PREBUFFER}, __end=__end_pos-${#PREBUFFER} ))

    # Highlighting logic for tmux arguments
    case "$__wrd" in
        # Main subcommands
        attach|attach-session|bind|bind-key|break-pane|capture-pane|choose-buffer|choose-client|\
        choose-tree|clear-history|clock-mode|command-prompt|confirm-before|copy-mode|\
        customize-mode|delete-buffer|detach|detach-client|display|display-menu|display-message|\
        display-panes|display-popup|find-window|has|has-session|if|if-shell|join-pane|\
        kill-pane|kill-server|kill-session|kill-window|last|last-pane|last-window|link-window|\
        list-buffers|list-clients|list-commands|list-keys|list-panes|list-sessions|list-windows|\
        load-buffer|lock|lock-client|lock-server|lock-session|move-pane|move-window|new|new-session|\
        new-window|next|next-layout|next-window|paste-buffer|pipe-pane|prev|previous-layout|\
        previous-window|refresh|refresh-client|rename|rename-session|rename-window|resize-pane|\
        resize-window|respawn-pane|respawn-window|rotate-window|run|run-shell|save-buffer|\
        select-layout|select-pane|select-window|send|send-keys|send-prefix|set|set-buffer|\
        set-environment|set-hook|set-option|set-window-option|show|show-buffer|show-environment|\
        show-hooks|show-messages|show-options|show-window-options|source|source-file|split-window|\
        start|start-server|suspend-client|swap-pane|swap-window|switch-client|unbind|unbind-key|\
        unlink-window|wait|wait-for)
            if (( FAST_HIGHLIGHT[chroma-tmux-subcommand-seen] == 0 )); then
                __style=${FAST_THEME_NAME}subcommand
                FAST_HIGHLIGHT[chroma-tmux-subcommand-seen]=1
            else
                __style=${FAST_THEME_NAME}default
            fi
            ;;
        # Global options
        -[2CDdEfLlNPsTuUvV]*)
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
