{ lib }:
{
  # Idempotently ensure a user-writable local override file exists.
  # Used to seed machine-local files that home-manager must not own.
  mkEnsureLocalFile =
    path:
    lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      target="${path}"
      if [ ! -f "$target" ]; then
        mkdir -p "$(dirname "$target")"
        touch "$target"
      fi
    '';
}
