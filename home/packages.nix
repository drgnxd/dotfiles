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
    "jaq"
    "ncdu"
    "ripgrep"
    "sd"
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
    "marksman"
    "taplo"
    "lua-language-server"
    "yaml-language-server"
    "texlab"
  ];

  git_tools = [
    "git-crypt"
    "git-lfs"
    "lazygit"
  ];

  dev_tools = [
    "boost"
    "cmake"
  ];

  languages = [
    "guile"
    "nodejs"
    "uv"
    "R"
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
