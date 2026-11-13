{
  config,
  lib,
  pkgs,
  user,
  hostname,
  linuxHostname,
  ...
}:

let
  packages = import ./packages.nix { inherit pkgs lib; };

  # Personal autoMode.environment entries (org, source control, sensitive
  # locations) kept out of this public repo. Same local-override pattern as
  # local/identity.nix and local/packages.nix: gitignored, optional, falls
  # back to no extra entries on a fresh clone. The committed
  # xdg/data/claude/settings.json intentionally carries only
  # `"$defaults"` here — do not put personal environment prose back into
  # that file; add it to local/claude-auto-mode-environment.nix instead. See
  # local/claude-auto-mode-environment.nix.example for the shape.
  claude_local_environment_path = ../local/claude-auto-mode-environment.nix;
  claude_local_environment =
    if builtins.pathExists claude_local_environment_path then
      import claude_local_environment_path
    else
      [ ];
  # Packages built from sources that live in private repositories, kept out of
  # this public repo by name. Same local-override pattern: gitignored,
  # optional, empty on a fresh clone. See local/private-tools.nix.example.
  private_tools_path = ../local/private-tools.nix;
  private_tools =
    if builtins.pathExists private_tools_path then
      let
        tools = import private_tools_path { inherit pkgs lib; };
      in
      if builtins.isList tools then
        tools
      else
        throw "local/private-tools.nix must return a list of derivations"
    else
      [ ];
  claude_settings_base = builtins.fromJSON (builtins.readFile ../xdg/data/claude/settings.json);
  claude_settings = claude_settings_base // {
    autoMode = claude_settings_base.autoMode // {
      environment = claude_settings_base.autoMode.environment ++ claude_local_environment;
    };
  };
  claude_settings_json = pkgs.runCommand "claude-settings.json" { } ''
    ${pkgs.jq}/bin/jq . ${pkgs.writeText "claude-settings-raw.json" (builtins.toJSON claude_settings)} > $out
  '';
in
{
  home.username = user;
  home.homeDirectory =
    if pkgs.stdenv.hostPlatform.isDarwin then "/Users/${user}" else "/home/${user}";
  home.stateVersion = "24.11";

  programs.home-manager.enable = true;

  imports = [
    ./modules/activation/directories.nix
    ./modules/activation/nushell_ensure.nix
    ./modules/activation/opencode.nix
    ./modules/activation/claude_skills.nix
    ./modules/activation/copilot.nix
    ./modules/alacritty.nix
    ./modules/atuin.nix
    ./modules/bat.nix
    ./modules/btop.nix
    ./modules/direnv.nix
    ./modules/floorp.nix
    ./modules/fzf.nix
    ./modules/gh.nix
    ./modules/git.nix
    ./modules/glow.nix
    ./modules/neovim.nix
    ./modules/nix_gc.nix
    ./modules/nix_index.nix
    ./modules/nushell.nix
    ./modules/nushell-integrations.nix
    ./modules/secrets.nix
    ./modules/shellcheck.nix
    ./modules/ssh.nix
    ./modules/starship.nix
    ./modules/yazi.nix
    ./modules/zellij.nix
    ./modules/zoxide.nix
  ]
  ++ lib.optionals pkgs.stdenv.hostPlatform.isDarwin [
    ./modules/activation/spotlight_apps.nix
    ./modules/activation/macos_defaults.nix
    ./modules/markql.nix
    ./modules/swiftbar.nix
    ./modules/npmrc.nix
    ./modules/stats.nix
  ]
  ++ lib.optionals pkgs.stdenv.hostPlatform.isLinux [
    ./modules/linux/desktop.nix
  ];

  xdg.enable = true;

  # Option documentation and the man-page index add evaluation and build work
  # to every switch.
  manual = {
    manpages.enable = false;
    html.enable = false;
    json.enable = false;
  };
  programs.man.generateCaches = false;

  xdg.configFile = lib.optionalAttrs pkgs.stdenv.hostPlatform.isDarwin {
    "zsh/.zshrc".source = ../xdg/config/zsh/.zshrc;
  };

  targets.darwin.linkApps.enable = lib.mkIf pkgs.stdenv.hostPlatform.isDarwin true;

  home.sessionVariables = {
    CLAUDE_CONFIG_DIR = "${config.xdg.dataHome}/claude";
    COPILOT_HOME = "${config.xdg.dataHome}/copilot";
    NIXPKGS_OPENCODE_DISABLE_LEGACY_DB_WORKAROUND = "1";
    OPENCODE_ENABLE_EXA = "1";
    NPM_CONFIG_CACHE = "${config.xdg.cacheHome}/npm";
    NPM_CONFIG_PREFIX = "${config.xdg.dataHome}/npm";
    NPM_CONFIG_USERCONFIG = "${config.xdg.configHome}/npm/npmrc";
    KERAS_HOME = "${config.xdg.dataHome}/keras";
    DOTFILES_DIR = "${config.home.homeDirectory}/.config/dotfiles";
    DOTFILES_FLAKE_TARGET = if pkgs.stdenv.hostPlatform.isDarwin then hostname else linuxHostname;
    NH_FLAKE = "${config.home.homeDirectory}/.config/dotfiles";
  };

  home.sessionPath = [ "${config.home.homeDirectory}/.local/bin" ];

  home.packages = packages.packages ++ private_tools;

  programs.bash = {
    # Login and terminal shells are Nushell on Darwin, so the generated
    # ~/.bashrc, ~/.bash_profile and ~/.profile would only add home symlinks.
    enable = !pkgs.stdenv.hostPlatform.isDarwin;
    # The packaged Bash omits progcomp, so Home Manager's completion hook fails.
    enableCompletion = false;
    historyFile = "${config.xdg.stateHome}/bash/history";
  };

  warnings = lib.optional (packages.missing != [ ]) (
    "Missing nix packages: " + (lib.concatStringsSep ", " packages.missing)
  );

  home.file = {
    ".local/bin/copilot" = {
      source = ../scripts/copilot;
      executable = true;
    };
    # CodexBar still creates temporary files at the legacy path despite CODEX_HOME.
    ".codex".source = config.lib.file.mkOutOfStoreSymlink "${config.xdg.dataHome}/codex";
    # Ollama hardcodes ~/.ollama for its key and has no environment override.
    ".ollama".source = config.lib.file.mkOutOfStoreSymlink "${config.xdg.dataHome}/ollama";
    # Scilab 2027 ignores SCIHOME and always uses ~/.Scilab.
    ".Scilab".source = config.lib.file.mkOutOfStoreSymlink "${config.xdg.configHome}/scilab";
  }
  // lib.optionalAttrs pkgs.stdenv.hostPlatform.isDarwin {
    ".local/bin/cloud-symlinks" = {
      source = ../scripts/darwin/setup_cloud_symlinks.sh;
      executable = true;
    };
  };

  xdg.dataFile."claude/CLAUDE.md".source = ../xdg/data/claude/CLAUDE.md;
  xdg.dataFile."claude/settings.json".source = claude_settings_json;
  xdg.dataFile."claude/agents/Explore.md".source = ../xdg/data/claude/agents/Explore.md;
  xdg.dataFile."claude/agents/Plan.md".source = ../xdg/data/claude/agents/Plan.md;
  xdg.dataFile."claude/agents/Review.md".source = ../xdg/data/claude/agents/Review.md;
  xdg.dataFile."claude/agents/researcher.md".source = ../xdg/data/claude/agents/researcher.md;
  xdg.dataFile."claude/agents/pdf-reader.md".source = ../xdg/data/claude/agents/pdf-reader.md;
  xdg.dataFile."claude/agents/browser-operator.md".source =
    ../xdg/data/claude/agents/browser-operator.md;
  xdg.dataFile."copilot/copilot-instructions.md".source =
    config.lib.file.mkOutOfStoreSymlink "${config.xdg.configHome}/opencode/AGENTS.md";
  xdg.dataFile."copilot/skills".source =
    config.lib.file.mkOutOfStoreSymlink "${config.xdg.configHome}/opencode/skills";

}
