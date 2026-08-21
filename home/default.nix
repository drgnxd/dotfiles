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
  # dot_local/share/claude/settings.json intentionally carries only
  # `"$defaults"` here — do not put personal environment prose back into
  # that file; add it to local/claude-auto-mode-environment.nix instead. See
  # local/claude-auto-mode-environment.nix.example for the shape.
  claude_local_environment_path = ../local/claude-auto-mode-environment.nix;
  claude_local_environment =
    if builtins.pathExists claude_local_environment_path then
      import claude_local_environment_path
    else
      [ ];
  claude_settings_base = builtins.fromJSON (
    builtins.readFile ../dot_local/share/claude/settings.json
  );
  # opencode-notifier's absolute path depends on this machine's username, so
  # it is built here from `user`/`config.home.homeDirectory` rather than
  # hardcoded in the committed settings.json (see AGENTS.md: "Never
  # hardcode usernames or hostnames").
  opencode_notifier_cli = "${config.home.homeDirectory}/repos/opencode-notifier/src/cli.ts";
  per_user_bun = "/etc/profiles/per-user/${user}/bin/bun";
  claude_settings = claude_settings_base // {
    autoMode = claude_settings_base.autoMode // {
      environment = claude_settings_base.autoMode.environment ++ claude_local_environment;
    };
    hooks = {
      Stop = [
        {
          hooks = [
            {
              type = "command";
              command = "${per_user_bun} run ${opencode_notifier_cli} --event complete 2>/dev/null || true";
            }
          ];
        }
      ];
      Notification = [
        {
          hooks = [
            {
              type = "command";
              command = "${per_user_bun} run ${opencode_notifier_cli} --event permission 2>/dev/null || true";
            }
          ];
        }
      ];
    };
  };
  claude_settings_json = pkgs.runCommand "claude-settings.json" { } ''
    ${pkgs.jq}/bin/jq . ${builtins.toFile "claude-settings-raw.json" (builtins.toJSON claude_settings)} > $out
  '';
in
{
  home.username = user;
  home.homeDirectory = if pkgs.stdenv.isDarwin then "/Users/${user}" else "/home/${user}";
  home.stateVersion = "24.11";

  programs.home-manager.enable = true;

  imports = [
    ./modules/activation/directories.nix
    ./modules/activation/nushell_ensure.nix
    ./modules/activation/opencode.nix
    ./modules/activation/claude_skills.nix
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
    ./modules/helix.nix
    ./modules/jujutsu.nix
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
  ++ lib.optionals pkgs.stdenv.isDarwin [
    ./modules/activation/macos_defaults.nix
    ./modules/qlmarkdown.nix
    ./modules/xdg_config_files.nix
    ./modules/xdg_desktop_files.nix
  ]
  ++ lib.optionals pkgs.stdenv.isLinux [
    ./modules/linux/desktop.nix
  ];

  xdg.enable = true;

  targets.darwin.linkApps.enable = lib.mkIf pkgs.stdenv.isDarwin true;

  home.sessionVariables = {
    CLAUDE_CONFIG_DIR = "${config.xdg.dataHome}/claude";
    COPILOT_HOME = "${config.xdg.dataHome}/copilot";
    NPM_CONFIG_CACHE = "${config.xdg.cacheHome}/npm";
    NPM_CONFIG_PREFIX = "${config.xdg.dataHome}/npm";
    NPM_CONFIG_USERCONFIG = "${config.xdg.configHome}/npm/npmrc";
    DOTFILES_DIR = "${config.home.homeDirectory}/.config/dotfiles";
    DOTFILES_FLAKE_TARGET = if pkgs.stdenv.isDarwin then hostname else linuxHostname;
    NH_FLAKE = "${config.home.homeDirectory}/.config/dotfiles";
  };

  home.packages = packages.packages;

  warnings = lib.optional (packages.missing != [ ]) (
    "Missing nix packages: " + (lib.concatStringsSep ", " packages.missing)
  );

  home.file = {
    ".claude.json".source =
      config.lib.file.mkOutOfStoreSymlink "${config.xdg.dataHome}/claude/.claude.json";
    ".ollama".source = config.lib.file.mkOutOfStoreSymlink "${config.xdg.dataHome}/ollama";
    ".Scilab".source = config.lib.file.mkOutOfStoreSymlink "${config.xdg.configHome}/scilab";
  }
  // lib.optionalAttrs pkgs.stdenv.isDarwin {
    ".local/bin/cloud-symlinks" = {
      source = ../scripts/darwin/setup_cloud_symlinks.sh;
      executable = true;
    };
  };

  xdg.dataFile."claude/CLAUDE.md".source = ../dot_local/share/claude/CLAUDE.md;
  xdg.dataFile."claude/settings.json".source = claude_settings_json;
  xdg.dataFile."claude/agents/Explore.md".source = ../dot_local/share/claude/agents/Explore.md;
  xdg.dataFile."claude/agents/Plan.md".source = ../dot_local/share/claude/agents/Plan.md;
  xdg.dataFile."claude/agents/Review.md".source = ../dot_local/share/claude/agents/Review.md;
  xdg.dataFile."copilot/copilot-instructions.md".source =
    config.lib.file.mkOutOfStoreSymlink "${config.xdg.configHome}/opencode/AGENTS.md";
  xdg.dataFile."copilot/skills".source =
    config.lib.file.mkOutOfStoreSymlink "${config.xdg.configHome}/opencode/skills";

}
