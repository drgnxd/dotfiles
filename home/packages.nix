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
  ];

  shell_tools = [
    "carapace"
    "nushell"
    "shellcheck"
    "taskwarrior3"
    "yazi"
  ];

  gui_apps_darwin = [
    # Floorp: managed via homebrew cask (not in nixpkgs for darwin)
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
    "protonvpn-gui"
  ];

  gui_apps = if pkgs.stdenv.isDarwin then gui_apps_darwin else gui_apps_linux;

  editors = [
    "helix"
  ];

  lsp_servers = [
    "pyright"
    "ruff"
    "nixd"
    "copilot-language-server"
    "marksman"
    "taplo"
    "lua-language-server"
    "yaml-language-server"
    "texlab"
    "bash-language-server"
    "dockerfile-language-server"
    "steel-language-server"
    "tinymist"
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
    "boost"
    "clang-tools"
    "cmake"
    "lldb"
    "nix-diff"
    "nix-tree"
  ];

  languages = [
    "guile"
    "nodejs"
    "uv"
    "R" # nixpkgs attr: pkgs.R (GNU R)
    # rustup provides rust-analyzer; avoid a separate package to prevent conflicts.
    "rustup"
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
    "smartmontools"
  ];

  containers = [
    "docker"
    "docker-compose"
    "lima"
  ];

  misc = [
    "ngspice"
    "opencode"
    "ollama"
    "zk"
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
    ++ containers
    ++ misc
  );

  # tryEval catches both missing attrs and broken/unfree evaluation failures.
  existing = lib.filter (
    name:
    let
      result =
        if builtins.hasAttr name pkgs then
          builtins.tryEval (builtins.getAttr name pkgs)
        else
          {
            success = false;
          };
    in
    result.success
  ) all_names;
  missing = lib.filter (
    name:
    let
      result =
        if builtins.hasAttr name pkgs then
          builtins.tryEval (builtins.getAttr name pkgs)
        else
          {
            success = false;
          };
    in
    !result.success
  ) all_names;
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
