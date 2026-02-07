{ pkgs, lib }:

let
  base_names = [
    "bat"
    "btop"
    "choose"
    "dust"
    "duf"
    "eza"
    "fd"
    "fzf"
    "grex"
    "jaq"
    "ncdu"
    "ripgrep"
    "sd"
    "tree"
    "wget"
    "xh"

    "atuin"
    "carapace"
    "direnv"
    "nushell"
    "shellcheck"
    "starship"
    "taskwarrior2"
    "tmux"
    "yazi"
    "zoxide"

    "alacritty"
    "floorp-bin"
    "maccy"
    "stats"

    "helix"

    "pyright"
    "ruff"
    "marksman"
    "taplo"
    "lua-language-server"
    "yaml-language-server"
    "texlab"

    "git"
    "gh"
    "git-crypt"
    "delta"
    "git-lfs"
    "lazygit"

    "boost"
    "cmake"

    "guile"
    "nodejs"
    "uv"
    "R"
    "rustup"

    "pandoc"
    "tectonic"
    "typst"

    "gnupg"
    "pass"

    "p7zip"
    "smartmontools"

    "docker"
    "docker-compose"
    "lima"

    "ngspice"
    "opencode"
    "ollama"
    "zk"
  ];

  names = lib.unique base_names;
  existing = lib.filter (name: builtins.hasAttr name pkgs) names;
  missing = lib.filter (name: !(builtins.hasAttr name pkgs)) names;
in
{
  packages = map (name: pkgs.${name}) existing;
  missing = missing;
}
