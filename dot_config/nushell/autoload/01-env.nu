export def xdg-dirs [] {
    {
        config: ($env | get --optional XDG_CONFIG_HOME | default ($env.HOME | path join ".config"))
        cache: ($env | get --optional XDG_CACHE_HOME | default ($env.HOME | path join ".cache"))
        data: ($env | get --optional XDG_DATA_HOME | default ($env.HOME | path join ".local" "share"))
        state: ($env | get --optional XDG_STATE_HOME | default ($env.HOME | path join ".local" "state"))
    }
}

let XDG_DIRS = (xdg-dirs)

let locale = if (($nu.os-info.name | str lowercase) == "linux") {
    "C.UTF-8"
} else {
    "en_US.UTF-8"
}
$env.LANG = $locale
$env.LC_ALL = $locale

$env.ENV_CONVERSIONS = ($env.ENV_CONVERSIONS | default {}) | merge {
    "PATH": {
        from_string: {|s| $s | split row (char esep) | path expand --no-symlink }
        to_string: {|v| $v | path expand --no-symlink | str join (char esep) }
    }
    "XDG_DATA_DIRS": {
        from_string: {|s| $s | split row (char esep) }
        to_string: {|v| $v | str join (char esep) }
    }
    "TERMINFO_DIRS": {
        from_string: {|s| $s | split row (char esep) }
        to_string: {|v| $v | str join (char esep) }
    }
}

$env.XDG_CONFIG_HOME = $XDG_DIRS.config
$env.XDG_CACHE_HOME = $XDG_DIRS.cache
$env.XDG_DATA_HOME = $XDG_DIRS.data
$env.XDG_STATE_HOME = $XDG_DIRS.state

$env.GNUPGHOME = ($env.XDG_CONFIG_HOME | path join "gnupg")

$env.CARGO_HOME = ($env.XDG_DATA_HOME | path join "cargo")
$env.RUSTUP_HOME = ($env.XDG_DATA_HOME | path join "rustup")

$env.MPLCONFIGDIR = ($env.XDG_CONFIG_HOME | path join "matplotlib")

$env.NPM_CONFIG_PREFIX = ($env.XDG_DATA_HOME | path join "npm")
$env.NPM_CONFIG_CACHE = ($env.XDG_CACHE_HOME | path join "npm")
$env.NPM_CONFIG_USERCONFIG = ($env.XDG_CONFIG_HOME | path join "npm" "npmrc")

$env.BUN_INSTALL_CACHE_DIR = ($env.XDG_CACHE_HOME | path join "bun" "install" "cache")
$env.BUN_RUNTIME_TRANSPILER_CACHE_PATH = ($env.XDG_CACHE_HOME | path join "bun" "runtime-transpiler")

$env._ZO_DATA_DIR = ($env.XDG_DATA_HOME | path join "zoxide")

$env.BAT_CONFIG_DIR = ($env.XDG_CONFIG_HOME | path join "bat")
$env.BAT_CACHE_DIR = ($env.XDG_CACHE_HOME | path join "bat")

$env.STARSHIP_CONFIG = ($env.XDG_CONFIG_HOME | path join "starship" "starship.toml")

$env.TERMINFO_DIRS = [($env.XDG_DATA_HOME | path join "terminfo") "/usr/share/terminfo"]
$env.TERMINFO = ($env.XDG_DATA_HOME | path join "terminfo")

$env.SCIHOME = ($env.XDG_CONFIG_HOME | path join "scilab")

$env.SHELLCHECK_OPTS = "--rcfile=" + ($env.XDG_CONFIG_HOME | path join "shellcheck" "shellcheckrc" | path expand)

$env.DOCKER_CONFIG = ($env.XDG_CONFIG_HOME | path join "docker")

$env.LIMA_HOME = ($env.XDG_DATA_HOME | path join "lima")

$env.OLLAMA_MODELS = ($env.XDG_DATA_HOME | path join "ollama" "models")
$env.OLLAMA_FLASH_ATTENTION = "1"
$env.OLLAMA_KV_CACHE_TYPE = "q8_0"
$env.OLLAMA_KEEP_ALIVE = "5m"

$env.LESSHISTFILE = ($env.XDG_STATE_HOME | path join "less" "history")

$env.SHELL_SESSION_DIR = ($env.XDG_STATE_HOME | path join "nushell" "sessions")

if ($env | get -o DOTFILES_DIR | default "" | is-empty) {
    $env.DOTFILES_DIR = ($env.HOME | path join ".config" "nix-config")
}
if ($env | get -o DOTFILES_FLAKE_TARGET | default "" | is-empty) {
    $env.DOTFILES_FLAKE_TARGET = "darwin"
}

if (($nu.os-info.name | str lowercase) == "linux") {
    $env.MOZ_ENABLE_WAYLAND = "1"
    $env.QT_QPA_PLATFORM = "wayland"
    $env.SDL_VIDEODRIVER = "wayland"
}

$env.EDITOR = "hx"
$env.VISUAL = $env.EDITOR

let nu_path = (which nu | get path.0?)
if $nu_path != null {
    $env.SHELL = $nu_path
}

$env.LS_COLORS = "di=1;34:ln=1;36:so=32:pi=33:ex=31:bd=34;46:cd=34;43:su=30;41:sg=30;46:tw=30;42:ow=30;43"

$env.CLICOLOR = "1"
$env.LSCOLORS = "Gxfxcxdxbxegedabagacad"

$env.COLORTERM = "truecolor"

$env.FZF_DEFAULT_OPTS = "
  --color=bg+:#073642,bg:#002b36,spinner:#719e07,hl:#719e07
  --color=fg:#839496,header:#586e75,info:#cb4b16,pointer:#719e07
  --color=marker:#719e07,fg+:#839496,prompt:#719e07,hl+:#719e07
"
