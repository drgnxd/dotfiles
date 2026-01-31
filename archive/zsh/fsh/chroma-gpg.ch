# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for gpg

chroma/gpg() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style

    (( __first_call )) && {
        FAST_HIGHLIGHT[chroma-gpg-counter]=0
        FAST_HIGHLIGHT[chroma-gpg-counter-all]=1
        return 1
    }

    (( FAST_HIGHLIGHT[chroma-gpg-counter-all] += 1, __start=__start_pos-${#PREBUFFER}, __end=__end_pos-${#PREBUFFER} ))

    case "$__wrd" in
        # Actions / Commands (expanded from gpg --help)
        --sign|--clear-sign|--clearsign|--detach-sign|--encrypt|--symmetric|--store|--decrypt|--verify|--list-keys|--list-secret-keys|--list-signatures|--check-signatures|--fingerprint|--list-packets|--full-generate-key|--generate-key|--generate-revocation|--edit-key|--sign-key|--lsign-key|--quick-sign-key|--delete-keys|--delete-secret-keys|--import|--export|--send-keys|--receive-keys|--search-keys|--refresh-keys|--card-status|--edit-card|--change-pin|--update-trustdb|--print-md|--server|--help|--version)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        # Options
        --armor|--auto-key-import|--auto-key-locate|--output|--recipient|--hidden-recipient|--default-key|--local-user|--compress-algo|--passphrase|--batch|--yes|--no|--keyring|--secret-keyring|--trustdb-name|--homedir|--display-charset|--verbose|--quiet|--log-file|--options|--interactive|--quiet)
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
