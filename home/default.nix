{ config, lib, pkgs, ... }:

let
  packages = import ./packages.nix { inherit pkgs lib; };

  clean_source = { src, exclude_names ? [] }:
    let
      default_excludes = [
        ".DS_Store"
        ".pytest_cache"
        ".ruff_cache"
        ".venv"
        "__pycache__"
        "CACHEDIR.TAG"
      ];
    in
      lib.cleanSourceWith {
        inherit src;
        filter = path: type:
          let
            path_str = toString path;
            name = builtins.baseNameOf path;
          in
            !(lib.elem name (default_excludes ++ exclude_names))
            && !lib.hasInfix "/.pytest_cache/" path_str
            && !lib.hasInfix "/.ruff_cache/" path_str
            && !lib.hasInfix "/.venv/" path_str
            && !lib.hasInfix "/__pycache__/" path_str;
      };

  opencode_source = clean_source { src = ../dot_config/opencode; };

  taskwarrior_source = clean_source { src = ../dot_config/taskwarrior; };

  use_npmrc_secret = builtins.pathExists ../secrets/npmrc.age;
  has_npmrc_file = builtins.pathExists ../dot_config/npm/npmrc;
in
{
  home.username = "drgnxd";
  home.homeDirectory = "/Users/drgnxd";
  home.stateVersion = "24.11";

  programs.home-manager.enable = true;

  xdg.enable = true;

  targets.darwin.linkApps.enable = true;

  home.sessionVariables = {
    DOTFILES_DIR = "${config.home.homeDirectory}/.config/nix-config";
    DOTFILES_FLAKE_TARGET = "macbook";
  };

  home.packages = packages.packages;

  warnings = lib.optional (packages.missing != [])
    ("Missing nix packages: " + (lib.concatStringsSep ", " packages.missing));

  xdg.configFile = lib.mkMerge [
    {
      "alacritty/alacritty.toml".source = ../dot_config/alacritty/alacritty.toml;
      "alacritty/blur.toml".source = ../dot_config/alacritty/blur.toml;
      "alacritty/toggle_blur.sh" = {
        source = ../dot_config/alacritty/executable_toggle_blur.sh;
        executable = true;
      };

      "atuin/config.toml".source = ../dot_config/atuin/config.toml;
      "bat/config".source = ../dot_config/bat/config;
      "gh/config.yml".source = ../dot_config/gh/config.yml;
      "git/config".source = ../dot_config/git/config;
      "git/config.local.example".source = ../dot_config/git/config.local.example;

      "helix/config.toml".source = ../dot_config/helix/config.toml;
      "helix/languages.toml".source = ../dot_config/helix/languages.toml;
      "helix/themes/solarized_dark_transparent.toml".source = ../dot_config/helix/themes/solarized_dark_transparent.toml;

      "nushell/config.nu".source = ../dot_config/nushell/config.nu;
      "nushell/env.nu".source = ../dot_config/nushell/env.nu;
      "nushell/local.nu".source = ../dot_config/nushell/local.nu;

      "nushell/autoload/00-constants.nu".source = ../dot_config/nushell/autoload/00-constants.nu;
      "nushell/autoload/00-helpers.nu".source = ../dot_config/nushell/autoload/00-helpers.nu;
      "nushell/autoload/01-env.nu".source = ../dot_config/nushell/autoload/01-env.nu;
      "nushell/autoload/02-path.nu".source = ../dot_config/nushell/autoload/02-path.nu;
      "nushell/autoload/03-aliases.nu".source = ../dot_config/nushell/autoload/03-aliases.nu;
      "nushell/autoload/04-functions.nu".source = ../dot_config/nushell/autoload/04-functions.nu;
      "nushell/autoload/05-completions.nu".source = ../dot_config/nushell/autoload/05-completions.nu;
      "nushell/autoload/06-integrations.nu".source = ../dot_config/nushell/autoload/06-integrations.nu;
      "nushell/autoload/07-source-tools.nu".source = ../dot_config/nushell/autoload/07-source-tools.nu;
      "nushell/autoload/08-taskwarrior.nu".source = ../dot_config/nushell/autoload/08-taskwarrior.nu;
      "nushell/autoload/09-lima.nu".source = ../dot_config/nushell/autoload/09-lima.nu;

      "nushell/modules/integrations.nu".source = ../dot_config/nushell/modules/integrations.nu;
      "nushell/modules/taskwarrior.nu".source = ../dot_config/nushell/modules/taskwarrior.nu;
      "nushell/modules/lima.nu".source = ../dot_config/nushell/modules/lima.nu;

      "opencode".source = opencode_source;

      "shellcheck/shellcheckrc".source = ../dot_config/shellcheck/shellcheckrc;
      "starship/starship.toml".source = ../dot_config/starship/starship.toml;

      "taskwarrior".source = taskwarrior_source;

      "tmux/tmux.conf".source = ../dot_config/tmux/tmux.conf;

      "yazi/yazi.toml".source = ../dot_config/yazi/yazi.toml;
      "yazi/theme.toml".source = ../dot_config/yazi/theme.toml;
      "yazi/keymap.toml".source = ../dot_config/yazi/keymap.toml;
      "yazi/flavors/solarized-dark.yazi/flavor.toml".source = ../dot_config/yazi/flavors/solarized-dark.yazi/flavor.toml;
      "yazi/flavors/solarized-dark-custom/colors.toml".source = ../dot_config/yazi/flavors/solarized-dark-custom/colors.toml;
      "yazi/flavors/solarized-dark-custom/style.yazi".source = ../dot_config/yazi/flavors/solarized-dark-custom/style.yazi;

      "hammerspoon/init.lua".source = ../dot_config/hammerspoon/init.lua;
      "hammerspoon/window.lua".source = ../dot_config/hammerspoon/window.lua;
      "hammerspoon/cheatsheet.lua".source = ../dot_config/hammerspoon/cheatsheet.lua;
      "hammerspoon/reload.lua".source = ../dot_config/hammerspoon/reload.lua;
      "hammerspoon/input_switcher.lua".source = ../dot_config/hammerspoon/input_switcher.lua;
      "hammerspoon/browser_control.lua".source = ../dot_config/hammerspoon/browser_control.lua;
      "hammerspoon/caffeine.lua".source = ../dot_config/hammerspoon/caffeine.lua;

      "stats/eu.exelban.Stats.plist".source = ../dot_config/stats/eu.exelban.Stats.plist;
    }
    (lib.optionalAttrs (!use_npmrc_secret && has_npmrc_file) {
      "npm/npmrc".source = ../dot_config/npm/npmrc;
    })
  ];

  home.file = {
    ".ollama".source = config.lib.file.mkOutOfStoreSymlink "${config.xdg.dataHome}/ollama";
    ".Scilab".source = config.lib.file.mkOutOfStoreSymlink "${config.xdg.configHome}/scilab";
    ".hammerspoon".source = config.lib.file.mkOutOfStoreSymlink "${config.xdg.configHome}/hammerspoon";

    ".local/bin/cloud-symlinks" = {
      source = ../scripts/darwin/setup_cloud_symlinks.sh;
      executable = true;
    };
  };

  home.activation.ensureDirectories = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    mkdir -p "$HOME/.local/bin"
    mkdir -p "$HOME/Desktop/Screenshots"
    mkdir -p "$HOME/.local/state/launchagents/hammerspoon"
    mkdir -p "$HOME/.local/state/launchagents/maccy"
    mkdir -p "$HOME/.local/state/launchagents/stats"
  '';

  home.activation.ensureNushellInitCache = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    mkdir -p "$HOME/.cache/nushell-init"
    touch "$HOME/.cache/nushell-init/starship.nu"
    touch "$HOME/.cache/nushell-init/zoxide.nu"
    touch "$HOME/.cache/nushell-init/carapace.nu"
    touch "$HOME/.cache/nushell-init/atuin.nu"
  '';

  home.activation.applyUserDefaults = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    /usr/bin/defaults write NSGlobalDomain NSNavPanelExpandedStateForSaveMode -bool true
    /usr/bin/defaults write NSGlobalDomain NSNavPanelExpandedStateForSaveMode2 -bool true
    /usr/bin/defaults write NSGlobalDomain PMPrintingExpandedStateForPrint -bool true
    /usr/bin/defaults write NSGlobalDomain PMPrintingExpandedStateForPrint2 -bool true
    /usr/bin/defaults write NSGlobalDomain AppleLanguages -array "en-JP" "ja-JP"
    /usr/bin/defaults write NSGlobalDomain AppleLocale -string "en_JP"
    /usr/bin/defaults write NSGlobalDomain AppleMeasurementUnits -string "Centimeters"
    /usr/bin/defaults write NSGlobalDomain AppleMetricUnits -bool true
    /usr/bin/defaults write NSGlobalDomain AppleTemperatureUnit -string "Celsius"
    /usr/bin/defaults write NSGlobalDomain AppleICUDateFormatStrings -dict-add 1 "yyyy/MM/dd"
    /usr/bin/defaults write NSGlobalDomain NSAutomaticSpellingCorrectionEnabled -bool false
    /usr/bin/defaults write NSGlobalDomain NSAutomaticCapitalizationEnabled -bool false
    /usr/bin/defaults write NSGlobalDomain NSAutomaticQuoteSubstitutionEnabled -bool false
    /usr/bin/defaults write NSGlobalDomain NSAutomaticDashSubstitutionEnabled -bool false
    /usr/bin/defaults write NSGlobalDomain NSAutomaticPeriodSubstitutionEnabled -bool false

    /usr/bin/defaults write -g com.apple.mouse.scaling -int 7
    /usr/bin/defaults write -g com.apple.trackpad.scaling -int 7

    /usr/bin/defaults write NSGlobalDomain AppleShowAllExtensions -bool true
    /usr/bin/defaults write com.apple.finder AppleShowAllFiles -bool true
    /usr/bin/defaults write com.apple.finder _FXShowPosixPathInTitle -bool true
    /usr/bin/defaults write com.apple.finder ShowStatusBar -bool true
    /usr/bin/defaults write com.apple.finder ShowPathbar -bool true
    /usr/bin/defaults write com.apple.finder _FXSortFoldersFirst -bool true
    /usr/bin/defaults write com.apple.finder FXDefaultSearchScope -string "SCcf"
    /usr/bin/defaults write com.apple.desktopservices DSDontWriteNetworkStores -bool true
    /usr/bin/defaults write com.apple.desktopservices DSDontWriteUSBStores -bool true

    /usr/bin/defaults write com.apple.dock autohide -bool true
    /usr/bin/defaults write com.apple.dock autohide-delay -float 0
    /usr/bin/defaults write com.apple.dock autohide-time-modifier -float 0
    /usr/bin/defaults write com.apple.dock workspaces-swoosh-animation-off -bool true
    /usr/bin/defaults write com.apple.dock show-recents -bool false
    /usr/bin/defaults write com.apple.dock static-only -bool true
    /usr/bin/defaults write com.apple.dock tilesize -int 48

    /usr/bin/defaults write com.apple.screencapture disable-shadow -bool true
    /usr/bin/defaults write com.apple.screencapture type -string "png"
    /usr/bin/defaults write com.apple.screencapture location -string "$HOME/Desktop/Screenshots"

    /usr/bin/defaults write -g KeyRepeat -int 1
    /usr/bin/defaults write -g InitialKeyRepeat -int 15
    /usr/bin/defaults write -g ApplePressAndHoldEnabled -bool false
    /usr/bin/defaults write -g com.apple.keyboard.fnState -int 1

    /usr/bin/defaults write com.apple.controlcenter "NSStatusItem Visible Battery" -bool false
    /usr/bin/defaults write com.apple.controlcenter "NSStatusItem Visible BentoBox" -bool true
    /usr/bin/defaults -currentHost write -globalDomain NSStatusItemSpacing -int 10
    /usr/bin/defaults write -globalDomain NSStatusItemSpacing -int 10
    /usr/bin/defaults -currentHost write -globalDomain NSStatusItemSelectionPadding -int 6
    /usr/bin/defaults write -globalDomain NSStatusItemSelectionPadding -int 6
    /usr/bin/defaults write com.apple.controlcenter "NSStatusItem Visible NowPlaying" -bool false
    /usr/bin/defaults write com.apple.controlcenter "NSStatusItem Visible ScreenMirroring" -bool false
    /usr/bin/defaults write com.apple.controlcenter "NSStatusItem Visible WiFi" -bool false

    /usr/bin/defaults write com.apple.menuextra.clock IsAnalog -bool false
    /usr/bin/defaults write com.apple.menuextra.clock ShowAMPM -bool true
    /usr/bin/defaults write com.apple.menuextra.clock ShowDate -bool true
    /usr/bin/defaults write com.apple.menuextra.clock ShowDayOfWeek -bool true
    /usr/bin/defaults write com.apple.menuextra.clock ShowSeconds -bool true

    /usr/bin/killall Dock 2>/dev/null || true
    /usr/bin/killall Finder 2>/dev/null || true
    /usr/bin/killall SystemUIServer 2>/dev/null || true
    /usr/bin/killall ControlCenter 2>/dev/null || true
  '';

  home.activation.importStats = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    stats_plist="$HOME/.config/stats/eu.exelban.Stats.plist"
    if [ -f "$stats_plist" ]; then
      /usr/bin/plutil -lint "$stats_plist" >/dev/null 2>&1 && \
        /usr/bin/defaults import eu.exelban.Stats "$stats_plist" || true
      /usr/bin/killall cfprefsd 2>/dev/null || true
      /usr/bin/killall Stats 2>/dev/null || true
      /usr/bin/open -a Stats >/dev/null 2>&1 || true
    fi
  '';
}
