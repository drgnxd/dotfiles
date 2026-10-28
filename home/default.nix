{
  config,
  inputs,
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
  agent_inbox_source = "${config.home.homeDirectory}/repos/agent-inbox";
  agent_inbox_source_path = builtins.path {
    name = "agent-inbox-source";
    path = agent_inbox_source;
    filter =
      path: type:
      let
        relative = lib.removePrefix "${agent_inbox_source}/" path;
        parts = lib.splitString "/" relative;
        base = lib.last parts;
      in
      !(lib.any (
        part:
        builtins.elem part [
          ".git"
          "target"
          ".direnv"
          ".idea"
          ".vscode"
          "node_modules"
        ]
      ) parts)
      && (
        relative == ""
        || base == "Cargo.toml"
        || base == "Cargo.lock"
        || base == "build.rs"
        || lib.hasPrefix "src/" relative
        || relative == "src"
      )
      && type != "symlink";
  };
  agent_inbox_package =
    if builtins.pathExists "${agent_inbox_source}/Cargo.toml" then
      pkgs.writeShellScriptBin "agent-inbox" ''
        source=${lib.escapeShellArg (toString agent_inbox_source_path)}
        if [ ! -f "$source/Cargo.toml" ]; then
          printf '%s\n' 'agent-inbox source is unavailable' >&2
          exit 127
        fi
        export CARGO_TARGET_DIR="${config.xdg.cacheHome}/agent-inbox/target"
        exec ${pkgs.cargo}/bin/cargo run --quiet --manifest-path "$source/Cargo.toml" -- "$@"
      ''
    else
      pkgs.writeShellScriptBin "agent-inbox" ''
        printf '%s\n' 'agent-inbox is unavailable; clone the optional helper repository under ~/repos/agent-inbox' >&2
        exit 127
      '';
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
  claude_notify = pkgs.writeShellScript "claude-notify" ''
    # Scheduled jobs (launchd) set this variable to run quietly.
    [ -n "$OPENCODE_NOTIFIER_CONFIG_PATH" ] && exit 0
    input=$(cat)
    cwd=$(printf '%s' "$input" | ${pkgs.jq}/bin/jq -r '.cwd // empty')
    case "$1" in
      complete) body="Session has finished" ;;
      *) body=$(printf '%s' "$input" | ${pkgs.jq}/bin/jq -r '.message // "Session needs attention"') ;;
    esac
    title="Claude Code"
    if [ -n "$cwd" ]; then
      title="Claude Code ($(basename "$cwd"))"
    fi
    /usr/bin/osascript \
      -e 'on run argv' \
      -e 'display notification (item 1 of argv) with title (item 2 of argv)' \
      -e 'end run' -- "$body" "$title"
  '';
  claude_settings = claude_settings_base // {
    autoMode = claude_settings_base.autoMode // {
      environment = claude_settings_base.autoMode.environment ++ claude_local_environment;
    };
    hooks = {
      PermissionRequest = [
        {
          matcher = "*";
          hooks = [
            {
              type = "command";
              command = "AGENT_INBOX_CLIENT=claude ${pkgs.python3}/bin/python3 -I ${../xdg/data/claude/agent_inbox_hook.py}";
              timeout = 610;
            }
          ];
        }
      ];
      PreToolUse = [
        {
          matcher = "Edit|Write|MultiEdit|NotebookEdit|Bash|EnterWorktree";
          hooks = [
            {
              type = "command";
              # No `|| true`: exit 2 must reach Claude Code. A missing script exits 0 instead of
              # python's own exit 2, which would block every tool call.
              command = ''f=${config.xdg.configHome}/opencode/skills/git-workflow/scripts/worktree_guard.py; [ -f "$f" ] || exit 0; WORKTREE_GUARD_GIT=${pkgs.git}/bin/git exec ${pkgs.python3}/bin/python3 -I "$f" --client claude'';
              timeout = 10;
            }
          ];
        }
      ];
      Stop = [
        {
          hooks = [
            {
              type = "command";
              command = "AGENT_INBOX_CLIENT=claude agent-inbox complete 2>/dev/null || true";
            }
            {
              type = "command";
              command = "${claude_notify} complete 2>/dev/null || true";
            }
          ];
        }
      ];
      Notification = [
        {
          hooks = [
            {
              type = "command";
              command = "${claude_notify} permission 2>/dev/null || true";
            }
          ];
        }
      ];
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
    ./modules/xdg_config_files.nix
    ./modules/xdg_desktop_files.nix
  ]
  ++ lib.optionals pkgs.stdenv.hostPlatform.isLinux [
    ./modules/linux/desktop.nix
  ];

  xdg.enable = true;

  xdg.configFile = lib.mkIf pkgs.stdenv.hostPlatform.isDarwin {
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
    DOTFILES_DIR = "${config.home.homeDirectory}/.config/dotfiles";
    DOTFILES_FLAKE_TARGET = if pkgs.stdenv.hostPlatform.isDarwin then hostname else linuxHostname;
    NH_FLAKE = "${config.home.homeDirectory}/.config/dotfiles";
  };

  home.packages =
    packages.packages
    ++ [
      inputs.wtctl.packages.${pkgs.stdenv.hostPlatform.system}.default
    ]
    ++ [ agent_inbox_package ]
    ++ private_tools;

  home.activation.mergeClaudeAgentInboxMcp = lib.hm.dag.entryAfter [ "linkGeneration" ] ''
    ${pkgs.python3}/bin/python3 -I ${../xdg/data/claude/agent_inbox_config.py} \
      "${config.xdg.dataHome}/claude/.claude.json" \
      "${config.home.homeDirectory}/.claude.json" \
      "${agent_inbox_package}/bin/agent-inbox"
  '';

  programs.bash = {
    enable = true;
    # The packaged Bash omits progcomp, so Home Manager's completion hook fails.
    enableCompletion = false;
    historyFile = "${config.xdg.stateHome}/bash/history";
  };

  warnings = lib.optional (packages.missing != [ ]) (
    "Missing nix packages: " + (lib.concatStringsSep ", " packages.missing)
  );

  home.file = {
    # CodexBar still creates temporary files at the legacy path despite CODEX_HOME.
    ".codex".source = config.lib.file.mkOutOfStoreSymlink "${config.xdg.dataHome}/codex";
    ".claude.json".source =
      config.lib.file.mkOutOfStoreSymlink "${config.xdg.dataHome}/claude/.claude.json";
    ".ollama".source = config.lib.file.mkOutOfStoreSymlink "${config.xdg.dataHome}/ollama";
    ".Scilab".source = config.lib.file.mkOutOfStoreSymlink "${config.xdg.configHome}/scilab";
  }
  // lib.optionalAttrs pkgs.stdenv.hostPlatform.isDarwin {
    ".local/bin/cloud-symlinks" = {
      source = ../scripts/darwin/setup_cloud_symlinks.sh;
      executable = true;
    };
  };

  xdg.dataFile."claude/CLAUDE.md".source = ../xdg/data/claude/CLAUDE.md;
  xdg.dataFile."claude/agent_inbox_hook.py".source = ../xdg/data/claude/agent_inbox_hook.py;
  xdg.dataFile."claude/agent_inbox_config.py".source = ../xdg/data/claude/agent_inbox_config.py;
  xdg.dataFile."claude/settings.json".source = claude_settings_json;
  xdg.dataFile."claude/agents/Explore.md".source = ../xdg/data/claude/agents/Explore.md;
  xdg.dataFile."claude/agents/Plan.md".source = ../xdg/data/claude/agents/Plan.md;
  xdg.dataFile."claude/agents/Review.md".source = ../xdg/data/claude/agents/Review.md;
  xdg.dataFile."copilot/copilot-instructions.md".source =
    config.lib.file.mkOutOfStoreSymlink "${config.xdg.configHome}/opencode/AGENTS.md";
  xdg.dataFile."copilot/skills".source =
    config.lib.file.mkOutOfStoreSymlink "${config.xdg.configHome}/opencode/skills";

}
