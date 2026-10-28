{
  pkgs,
  cacheHome,
}:

pkgs.writeShellScriptBin "agent-inbox" ''
  cache_home="''${XDG_CACHE_HOME:-${cacheHome}}"
  binary="$cache_home/agent-inbox/target/release/agent-inbox"
  if [ ! -x "$binary" ]; then
    printf '%s\n' 'agent-inbox binary is missing from the local cache; build the helper into its release target directory' >&2
    exit 127
  fi
  exec "$binary" "$@"
''
