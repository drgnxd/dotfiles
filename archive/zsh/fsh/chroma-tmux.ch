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
        # Main subcommands (sourced from tmux list-commands when available)
        attach-session|bind-key|break-pane|capture-pane|choose-buffer|choose-client|choose-tree|\
        clear-history|clock-mode|command-prompt|confirm-before|copy-mode|customize-mode|\
        delete-buffer|detach-client|display-menu|display-message|display-panes|display-popup|\
        find-window|has-session|if-shell|join-pane|kill-pane|kill-server|kill-session|kill-window|\
        last-pane|last-window|link-window|list-buffers|list-clients|list-commands|list-keys|\
        list-panes|list-sessions|list-windows|load-buffer|lock-client|lock-server|lock-session|\
        move-pane|move-window|new-session|new-window|next-layout|next-window|paste-buffer|pipe-pane|\
        previous-layout|previous-window|refresh-client|rename-session|rename-window|resize-pane|\
        resize-window|respawn-pane|respawn-window|rotate-window|run-shell|save-buffer|select-layout|\
        select-pane|select-window|send-keys|send-prefix|set-buffer|set-environment|set-hook|set-option|\
        set-window-option|show-buffer|show-environment|show-hooks|show-messages|show-options|\
        show-window-options|source-file|split-window|start-server|suspend-client|swap-pane|swap-window|\
        switch-client|unbind-key|unlink-window|wait-for)
            if (( FAST_HIGHLIGHT[chroma-tmux-subcommand-seen] == 0 )); then
                __style=${FAST_THEME_NAME}subcommand
                FAST_HIGHLIGHT[chroma-tmux-subcommand-seen]=1
            else
                __style=${FAST_THEME_NAME}default
            fi
            ;;
        # Global options (single-hyphen options include letters, digits)
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
