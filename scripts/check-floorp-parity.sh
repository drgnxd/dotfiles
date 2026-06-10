#!/bin/sh

set -eu

warned=0
pattern='stdenv\.is|isDarwin|isLinux'

warn() {
	file=$1
	printf '%s\n' "WARNING: $file contains platform-specific branching in the shared Floorp UI/settings layer." >&2
	printf '%s\n' "The shared Floorp layer must stay platform-identical; move OS-specific logic to home/modules/floorp.nix." >&2
	warned=1
}

check_settings_region() {
	file=$1
	if awk '
    /# >>> shared-platform-independent \(do not add isDarwin\/isLinux branching below\)/ { in_region = 1; next }
    /# <<< shared-platform-independent/ { in_region = 0 }
    in_region { print }
  ' "$file" | grep -E "$pattern" >/dev/null 2>&1; then
		warn "$file"
	fi
}

check_whole_file() {
	file=$1
	if grep -E "$pattern" "$file" >/dev/null 2>&1; then
		warn "$file"
	fi
}

check_settings_region "home/modules/floorp/settings.nix"
check_whole_file "dot_config/floorp/chrome/userChrome.css"
check_whole_file "dot_config/floorp/chrome/userContent.css"

if [ "$warned" -eq 1 ]; then
	printf '%s\n' "WARNING: Floorp parity drift guard is advisory only; exiting 0." >&2
fi

exit 0
