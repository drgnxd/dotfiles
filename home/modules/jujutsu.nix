# jj coexists with git via colocated repos (`jj git init --colocate`).
# User identity is intentionally NOT managed here; it lives in the unmanaged
# local config (`jj config set --user user.name ...`), mirroring git's
# config.local pattern so no personal data enters the repo.
_: {
  programs.jujutsu = {
    enable = true;
    settings = {
      ui.default-command = [ "log" ];
      ui.diff-editor = ":builtin";
    };
  };
}
