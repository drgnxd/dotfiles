# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for gpg

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
    # Actions / Commands
    --sign|--clearsign|--detach-sign|--encrypt|--symmetric|--store|--decrypt|--verify|--list-keys|--list-secret-keys|--check-sigs|--fingerprint|--list-packets|--gen-key|--edit-key|--sign-key|--lsign-key|--nrsign-key|--delete-key|--delete-secret-key|--delete-secret-and-public-key|--gen-revoke|--desig-revoke|--export|--send-keys|--recv-keys|--search-keys|--refresh-keys|--import|--card-status|--card-edit|--change-pin|--update-trustdb|--print-md|--server|--help|--version)
        __style=${FAST_THEME_NAME}double-hyphen-option
        ;;
    # Options
    --armor|--output|--recipient|--hidden-recipient|--default-key|--local-user|--compress-algo|--passphrase|--batch|--yes|--no|--keyring|--secret-keyring|--trustdb-name|--homedir|--display-charset|--verbose|--quiet)
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
