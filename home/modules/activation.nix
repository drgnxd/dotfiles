{ config, lib, ... }:

let
  opencode_config = ../../dot_config/opencode/opencode.json;
  opencode_target = "${config.xdg.configHome}/opencode/opencode.json";
  taskwarrior_local_rc = "${config.xdg.configHome}/taskwarrior.local.rc";
  nushell_local_nu = "${config.xdg.configHome}/nushell/local.nu";

  disable_login_launch_agent = { plist_name, labels }:
    ''
      user_id="$(/usr/bin/id -u)"
      launch_agent="$HOME/Library/LaunchAgents/${plist_name}.plist"
      launch_agent_disabled="$HOME/Library/LaunchAgents/${plist_name}.plist.disabled"

      ${lib.concatMapStringsSep "\n" (label: ''
        /bin/launchctl bootout "gui/$user_id/${label}" 2>/dev/null || true
        /bin/launchctl disable "gui/$user_id/${label}" 2>/dev/null || true
      '') labels}

      if [ -f "$launch_agent" ]; then
        /bin/mv -f "$launch_agent" "$launch_agent_disabled"
      fi
    '';
in
{
  home.activation.ensureDirectories = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    mkdir -p "$HOME/.local/bin"
    mkdir -p "$HOME/Desktop/Screenshots"
    mkdir -p "$HOME/.local/state/launchagents/hammerspoon"
    mkdir -p "$HOME/.local/state/launchagents/maccy"
    mkdir -p "$HOME/.local/state/launchagents/stats"
  '';

  home.activation.syncOpencodeConfig = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    opencode_target="${opencode_target}"
    opencode_dir="$(dirname "$opencode_target")"
    mkdir -p "$opencode_dir"
    /bin/cp -f "${opencode_config}" "$opencode_target"
  '';

  home.activation.ensureTaskwarriorLocalRc = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    taskwarrior_local_rc="${taskwarrior_local_rc}"
    if [ ! -f "$taskwarrior_local_rc" ]; then
      mkdir -p "$(dirname "$taskwarrior_local_rc")"
      touch "$taskwarrior_local_rc"
    fi
  '';

  home.activation.ensureNushellLocalNu = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    nushell_local_nu="${nushell_local_nu}"
    if [ ! -f "$nushell_local_nu" ]; then
      mkdir -p "$(dirname "$nushell_local_nu")"
      touch "$nushell_local_nu"
    fi
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

  home.activation.disableStatsLaunchAtLogin = lib.hm.dag.entryAfter [ "importStats" ]
    (disable_login_launch_agent {
      plist_name = "eu.exelban.Stats";
      labels = [
        "eu.exelban.Stats"
        "eu.exelban.Stats.LaunchAtLogin"
      ];
    });

  home.activation.disableHammerspoonLaunchAtLogin = lib.hm.dag.entryAfter [ "writeBoundary" ]
    (disable_login_launch_agent {
      plist_name = "org.hammerspoon.Hammerspoon";
      labels = [
        "org.hammerspoon.Hammerspoon"
        "org.hammerspoon.Hammerspoon.LaunchAtLogin"
      ];
    });
}
