_:

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
      core = {
        editor = "hx";
        ignorecase = false;
        quotepath = false;
        precomposeunicode = true;
      };
      init.defaultBranch = "main";
      merge.conflictstyle = "diff3";
      pull.rebase = false;
      push = {
        autoSetupRemote = true;
        default = "simple";
      };
      fetch.prune = true;
      gpg.format = "ssh";
      commit.gpgsign = true;
      tag.gpgsign = true;
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
