# Single source of truth: programs.git.settings + programs.delta.options.
# Keep generated Git/Delta config in Nix; only local override template is static.
{ pkgs, ... }:

{
  xdg.configFile."git/config.local.example".source = ../../dot_config/git/config.local.example;

  programs.delta = {
    enable = true;
    enableGitIntegration = true;
    options = {
      navigate = true;
      light = false;
      line-numbers = true;
      side-by-side = true;
      syntax-theme = "Solarized (dark)";
      # Solarized Dark Palette
      minus-style = ''syntax "#3e2329"'';
      minus-emph-style = ''syntax "#5a2d34"'';
      plus-style = ''syntax "#18322c"'';
      plus-emph-style = ''syntax "#1f453a"'';
      file-style = ''"#839496" bold'';
      file-decoration-style = ''"#586e75" box'';
      hunk-header-style = "file line-number syntax";
      hunk-header-decoration-style = ''"#073642" box'';
      line-numbers-minus-style = ''"#dc322f"'';
      line-numbers-plus-style = ''"#859900"'';
      line-numbers-zero-style = ''"#586e75"'';
    };
  };

  programs.git = {
    enable = true;

    settings = {
      diff = {
        algorithm = "histogram";
        external = "${pkgs.difftastic}/bin/difft";
        tool = "difftastic";
      };
      "difftool \"difftastic\"" = {
        cmd = ''${pkgs.difftastic}/bin/difft "$LOCAL" "$REMOTE"'';
      };
      pager.difftool = true;
      core = {
        editor = "hx";
        ignorecase = false;
        quotepath = false;
        precomposeunicode = true;
      };
      init.defaultBranch = "main";
      merge.conflictstyle = "zdiff3";
      pull.rebase = false;
      rerere.enabled = true;
      rebase = {
        autosquash = true;
        autostash = true;
        updateRefs = true;
      };
      branch.sort = "-committerdate";
      tag.sort = "version:refname";
      push = {
        autoSetupRemote = true;
        default = "simple";
      };
      fetch.prune = true;
      fetch.fsckobjects = true;
      transfer.fsckobjects = true;
      receive.fsckobjects = true;
      gpg.format = "ssh";
      user.signingkey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFQed3Gye7yVML0fXiyN5VYAqPlttXwoetxVl1qk5w09 git-signing";
      commit.gpgsign = true;
      commit.verbose = true;
      tag.gpgsign = true;
      help.autocorrect = "prompt";
      include.path = "config.local";

      alias = {
        st = "status -s";
        co = "checkout";
        br = "branch";
        cm = "commit -m";
        a = "add";
        aa = "add .";
        d = "diff";
        ds = "diff --staged";
        amend = "commit --amend --no-edit";
        undo = "reset --soft HEAD^";
        lg = "!lazygit";
        hist = "log --graph --abbrev-commit --decorate --format=format:'%C(bold blue)%h%C(reset) - %C(bold green)(%ar)%C(reset) %C(white)%s%C(reset) %C(dim white)- %an%C(reset)%C(bold yellow)%d%C(reset)' --all";
      };
    };
  };
}
