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
    "tree"
    "wget"
    "xh"
  ];

  shell_tools = [
    "carapace"
    "nushell"
    "shellcheck"
    "taskwarrior3"
    "yazi"
  ];

  gui_apps = [
    "floorp-bin"
    "maccy"
  ];

  editors = [
    "helix"
  ];

  lsp_servers = [
    "pyright"
    "ruff"
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
    "git-crypt"
    "git-lfs"
    "lazygit"
  ];

  dev_tools = [
    "boost"
    "clang-tools"
    "cmake"
    "lldb"
  ];

  languages = [
    "guile"
    "nodejs"
    "uv"
    "R"
    # rustup provides rust-analyzer; avoid a separate package to prevent conflicts.
    "rustup"
  ];

  document_tools = [
    "pandoc"
    "tectonic"
    "typst"
  ];

  security = [
    "gnupg"
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
    ++ system_tools
    ++ containers
    ++ misc
  );

  existing = lib.filter (name: builtins.hasAttr name pkgs) all_names;
  missing = lib.filter (name: !(builtins.hasAttr name pkgs)) all_names;
in
{
  packages = map (name: pkgs.${name}) existing;
  inherit missing;
}
