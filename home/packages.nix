{ pkgs, lib }:

let
  cli_tools = [
    "btop"
    "choose"
    "dust"
    "duf"
    "eza"
    "fd"
    "grex"
    "hexyl"
    "hyperfine"
    "jaq"
    "ncdu"
    "procs"
    "ripgrep"
    "sd"
    "tealdeer"
    "tokei"
    "tree"
    "typos"
    "watchexec"
    "wget"
    "xh"
    "just"
    "difftastic"
    "glow"
    "gping"
    "doggo"
    "viddy"
  ];

  shell_tools = [
    "carapace"
    "nushell"
    "shellcheck"
    "yazi"
  ];

  gui_apps_darwin = [
    # Floorp: managed via homebrew cask; Linux uses floorp-bin from nixpkgs
    "maccy"
  ];

  gui_apps_linux = [
    "wl-clipboard"
    "cliphist"
    "socat"
    "networkmanagerapplet"
    "wofi"
    "grim"
    "slurp"
    "hyprpicker"
    "mako"
    "wtype"
    "wlsunset"
    "brightnessctl"
    "playerctl"
    "pamixer"
    "pavucontrol"
    "swayosd"
    "libnotify"
    "proton-pass"
    "protonmail-desktop"
    "proton-vpn-cli"
    "plemoljp-nf"
    "ibm-plex"
    "floorp-bin"
  ];

  gui_apps = if pkgs.stdenv.isDarwin then gui_apps_darwin else gui_apps_linux;

  editors = [
    "helix"
  ];

  lsp_servers = [
    "nixd"
    "copilot-language-server"
  ];

  git_tools = [
    "git-absorb"
    "git-cliff"
    "git-crypt"
    "git-lfs"
    "lazygit"
  ];

  dev_tools = [
    "ast-grep"
    "nh"
    "nix-diff"
    "nixfmt"
    "nix-tree"
    "nix-output-monitor"
  ];

  languages = [
    "bun"
    "uv"
  ];

  document_tools = [
    "pandoc"
    "tectonic"
    "typst"
  ];

  security = [
    "age"
    "gnupg"
  ];

  linux_cli_tools = lib.optionals pkgs.stdenv.isLinux [
    "proton-pass-cli"
  ];

  system_tools = [
    "p7zip"
    "proton-drive-cli"
    "smartmontools"
    "restic"
  ];

  chess_tools = [
    "en-croissant"
    "stockfish"
  ];

  # Package names that should not be disclosed in this public repo (e.g.
  # personal-finance tooling). Same local-override pattern as
  # local/identity.nix and local/preferences.nix: gitignored, optional,
  # falls back to an empty list on a fresh clone. See
  # local/packages.nix.example for the shape.
  local_packages_path = ../local/packages.nix;
  local_packages =
    if builtins.pathExists local_packages_path then import local_packages_path else [ ];

  containers = [
    "docker"
    "docker-compose"
    "lima"
  ];

  misc = [
    "claude-code"
    "ngspice"
    "opencode"
    # ollama: managed via homebrew formula on Darwin for MLX support (see hosts/darwin/default.nix).
  ];

  all_names = lib.unique (
    cli_tools
    ++ shell_tools
    ++ gui_apps
    ++ editors
    ++ lsp_servers
    ++ git_tools
    ++ dev_tools
    ++ languages
    ++ document_tools
    ++ security
    ++ linux_cli_tools
    ++ system_tools
    ++ chess_tools
    ++ local_packages
    ++ containers
    ++ misc
  );

  # tryEval catches both missing attrs and broken/unfree evaluation failures.
  resolves =
    name:
    if builtins.hasAttr name pkgs then
      (builtins.tryEval (builtins.getAttr name pkgs)).success
    else
      false;
  existing = lib.filter resolves all_names;
  missing = lib.filter (name: !resolves name) all_names;
  report = {
    inherit existing missing;
  };
  strict_packages = builtins.getEnv "STRICT_PACKAGES" == "1";
  missing_message = "Missing nix packages: " + (lib.concatStringsSep ", " missing);
  resolved_existing =
    if missing != [ ] && strict_packages then
      throw missing_message
    else
      lib.warnIf (missing != [ ]) missing_message existing;
in
{
  packages = map (name: pkgs.${name}) resolved_existing;
  inherit missing report;
  passthru = {
    inherit report;
  };
}
