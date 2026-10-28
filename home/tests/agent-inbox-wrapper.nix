{ pkgs }:

let
  wrapper = import ../lib/agent-inbox-package.nix {
    inherit pkgs;
    cacheHome = "unused-test-cache";
  };
in
pkgs.runCommand "agent-inbox-wrapper-test" { } ''
    missing_cache="$TMPDIR/missing-cache"
    mkdir -p "$missing_cache"
    set +e
    missing_output="$(XDG_CACHE_HOME="$missing_cache" ${wrapper}/bin/agent-inbox mcp 2>&1)"
    missing_status=$?
    set -e
    [ "$missing_status" -eq 127 ]
    case "$missing_output" in
      *"agent-inbox binary is missing from the local cache"*) ;;
      *) exit 1 ;;
    esac

    present_cache="$TMPDIR/present-cache"
    binary="$present_cache/agent-inbox/target/release/agent-inbox"
    mkdir -p "$(dirname "$binary")"
    cat > "$binary" <<'FIXTURE'
  #!${pkgs.runtimeShell}
    printf 'fixture:%s\n' "$*"
  FIXTURE
    chmod +x "$binary"
    output="$(XDG_CACHE_HOME="$present_cache" ${wrapper}/bin/agent-inbox mcp permission-request)"
    [ "$output" = "fixture:mcp permission-request" ]
    touch "$out"
''
