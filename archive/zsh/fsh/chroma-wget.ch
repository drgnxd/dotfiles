# -*- mode: sh; sh-indentation: 4; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# Chroma function for wget

chroma/wget() {
    (( next_word = 2 | 8192 ))

    local __first_call="$1" __wrd="$2" __start_pos="$3" __end_pos="$4"
    local __style

    (( __first_call )) && {
        FAST_HIGHLIGHT[chroma-wget-counter]=0
        FAST_HIGHLIGHT[chroma-wget-counter-all]=1
        return 1
    }

    (( FAST_HIGHLIGHT[chroma-wget-counter-all] += 1, __start=__start_pos-${#PREBUFFER}, __end=__end_pos-${#PREBUFFER} ))

    case "$__wrd" in
        # Options (expanded from wget manpage)
        --help|--version|--quiet|--verbose|--no-clobber|--continue|--timestamping|--server-response|--spider|--user-agent|--referer|--header|--save-headers|--output-document|--output-file|--directory-prefix|--force-directories|--no-host-directories|--protocol-directories|--timeout|--tries|--wait|--waitretry|--random-wait|--proxy|--proxy-user|--proxy-password|--quota|--limit-rate|--recursive|--level|--delete-after|--convert-links|--convert-file-only|--backup-converted|--mirror|--page-requisites|--strict-comments|--accept|--reject|--accept-regex|--reject-regex|--input-file|--load-cookies|--save-cookies|--hsts-file|--https-only|--no-check-certificate|--check-certificate|--ca-certificate|--ca-directory|--certificate|--private-key|--private-key-type|--pinnedpubkey|--post-data|--post-file|--method|--referer|--span-hosts|--warc-file|--warc-max-size)
            __style=${FAST_THEME_NAME}double-hyphen-option
            ;;
        # Short options (match common single-letter flags)
        -[0-9A-Za-z]*)
            __style=${FAST_THEME_NAME}single-hyphen-option
            ;;
        http://*|https://*|ftp://*)
            __style=${FAST_THEME_NAME}path
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
