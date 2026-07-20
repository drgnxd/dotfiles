{
  pkgs,
  user,
  ...
}:

let
  home_dir = "/Users/${user}";
in
{
  imports = [ ./launchd.nix ];
  # Disable nix-darwin's Nix daemon management.
  # Nix is installed and managed externally (e.g., Determinate Nix installer).
  # Enabling this would conflict with the external installation.
  nix.enable = false;

  system.stateVersion = 5;
  system.startup.chime = false;
  time.timeZone = "Asia/Tokyo";

  security.pam.services.sudo_local = {
    touchIdAuth = true; # Touch ID for sudo in Terminal
    reattach = true; # Touch ID inside tmux/screen/Zellij sessions
  };
  # nix-darwin runs Homebrew Bundle through sudo as the primary user. Preserve
  # the XDG config path only for that RunAs target, not for sudo-to-root calls.
  security.sudo.extraConfig = ''
    Defaults>${user} env_keep += "XDG_CONFIG_HOME"
  '';

  networking.applicationFirewall = {
    enable = true;
    enableStealthMode = true;
    blockAllIncoming = false;
    allowSigned = true;
    allowSignedApp = true;
  };

  # ── macOS system defaults (declarative) ──────────────────────────────
  system.defaults = {
    # Auto-check and auto-download macOS updates, but never auto-install:
    # installation (including the OS itself) stays a deliberate, manual step
    # so it can't restart the machine mid-work.
    SoftwareUpdate.AutomaticallyInstallMacOSUpdates = false;
    CustomSystemPreferences."/Library/Preferences/com.apple.SoftwareUpdate" = {
      AutomaticCheckEnabled = true;
      AutomaticDownload = true;
    };

    NSGlobalDomain = {
      # Save/print dialogs
      NSNavPanelExpandedStateForSaveMode = true;
      NSNavPanelExpandedStateForSaveMode2 = true;
      PMPrintingExpandedStateForPrint = true;
      PMPrintingExpandedStateForPrint2 = true;

      # Locale & units
      AppleMeasurementUnits = "Centimeters";
      AppleMetricUnits = 1;
      AppleTemperatureUnit = "Celsius";

      # Disable auto-corrections
      NSAutomaticSpellingCorrectionEnabled = false;
      NSAutomaticCapitalizationEnabled = false;
      NSAutomaticQuoteSubstitutionEnabled = false;
      NSAutomaticDashSubstitutionEnabled = false;
      NSAutomaticPeriodSubstitutionEnabled = false;

      # Show file extensions everywhere
      AppleShowAllExtensions = true;

      # Keyboard
      KeyRepeat = 1;
      InitialKeyRepeat = 15;
      ApplePressAndHoldEnabled = false;
    };

    screensaver = {
      askForPassword = true;
      askForPasswordDelay = 0;
    };

    loginwindow = {
      GuestEnabled = false;
      DisableConsoleAccess = true;
    };

    dock = {
      autohide = true;
      autohide-delay = 0.0;
      autohide-time-modifier = 0.0;
      mru-spaces = false;
      show-recents = false;
      static-only = true;
      tilesize = 48;
    };

    finder = {
      AppleShowAllFiles = true;
      _FXShowPosixPathInTitle = true;
      ShowStatusBar = true;
      ShowPathbar = true;
      _FXSortFoldersFirst = true;
      FXDefaultSearchScope = "SCcf";
    };

    screencapture = {
      disable-shadow = true;
      type = "png";
      location = "~/Desktop/Screenshots";
    };

    # Settings without dedicated nix-darwin options
    CustomUserPreferences = {
      NSGlobalDomain = {
        AppleLanguages = [
          "en-JP"
          "ja-JP"
        ];
        AppleLocale = "en_JP";
        AppleICUDateFormatStrings = {
          "1" = "yyyy/MM/dd";
        };
        "com.apple.mouse.scaling" = 7;
        "com.apple.trackpad.scaling" = 7;
        "com.apple.keyboard.fnState" = 1;
      };
      "com.apple.desktopservices" = {
        DSDontWriteNetworkStores = true;
        DSDontWriteUSBStores = true;
      };
      "com.apple.dock" = {
        workspaces-swoosh-animation-off = true;
      };
      "com.apple.controlcenter" = {
        "NSStatusItem Visible Battery" = false;
        "NSStatusItem Visible BentoBox" = true;
        "NSStatusItem Visible NowPlaying" = false;
        "NSStatusItem Visible ScreenMirroring" = false;
        "NSStatusItem Visible WiFi" = false;
      };
      "com.apple.menuextra.clock" = {
        IsAnalog = false;
        ShowAMPM = true;
        ShowDate = true;
        ShowDayOfWeek = true;
        ShowSeconds = true;
      };
      "org.hammerspoon.Hammerspoon" = {
        MJConfigFile = "${home_dir}/.config/hammerspoon/init.lua";
      };
    };
  };

  # Ensure XDG base directories are set system-wide so Nushell (and other tools)
  # find configs at ~/.config/ instead of macOS ~/Library/Application Support/
  environment.variables = {
    XDG_CONFIG_HOME = "$HOME/.config";
    XDG_CACHE_HOME = "$HOME/.cache";
    XDG_DATA_HOME = "$HOME/.local/share";
    XDG_STATE_HOME = "$HOME/.local/state";
  };
  # Seed direct user agents. LaunchServices apps may sanitize this environment,
  # so terminal-specific variables are also declared in the Alacritty config.
  launchd.user.envVariables = {
    PATH = "${home_dir}/.nix-profile/bin:/etc/profiles/per-user/${user}/bin:/run/current-system/sw/bin:/nix/var/nix/profiles/default/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin";
    CLAUDE_CONFIG_DIR = "${home_dir}/.local/share/claude";
    XDG_CONFIG_HOME = "${home_dir}/.config";
    XDG_CACHE_HOME = "${home_dir}/.cache";
    XDG_DATA_HOME = "${home_dir}/.local/share";
    XDG_STATE_HOME = "${home_dir}/.local/state";
  };

  home-manager.backupFileExtension = "before-nix";

  homebrew = {
    enable = true;
    onActivation = {
      # Keep casks/brews/mas apps current automatically on every switch.
      autoUpdate = true;
      upgrade = true;
      cleanup = "zap";
      extraFlags = [ "--force" ];
    };
    taps = [
      "protonpass/tap"
    ];
    brews = [
      "mas"
      "pass-cli"
    ];
    casks = [
      "codexbar"
      "hammerspoon"
      "pearcleaner"
      "sol"
      "stats"

      "gimp"
      "floorp"
      "libreoffice"

      "kicad"
      "orcaslicer"
      "qflipper"
      "signal"

      "logi-options+"

      "proton-drive"
      "proton-mail"
      "proton-pass"
      "protonvpn"
      "scilab"
    ];
    masApps = {
      "Proton Pass for Safari" = 6502835663;
    };
  };

  fonts.packages = with pkgs; [
    hackgen-font
    hackgen-nf-font
  ];

  users.users.${user}.home = home_dir;
  system.primaryUser = user;

  system.activationScripts.preActivation.text = ''
    export XDG_CONFIG_HOME="${home_dir}/.config"
  '';

  system.activationScripts.extraActivation.text = ''
    if [ -x /opt/homebrew/bin/brew ]; then
      /usr/bin/sudo --user=${user} --set-home /usr/bin/env \
        XDG_CONFIG_HOME="${home_dir}/.config" \
        /opt/homebrew/bin/brew trust --tap protonpass/tap >/dev/null
      /usr/bin/sudo --user=${user} --set-home /usr/bin/env \
        XDG_CONFIG_HOME="${home_dir}/.config" \
        /opt/homebrew/bin/brew trust --formula protonpass/tap/pass-cli >/dev/null
    fi
  '';

  system.activationScripts.securityHardening.text = ''
    /usr/bin/defaults delete /Library/Preferences/com.apple.loginwindow LoginwindowText 2>/dev/null || true

    /usr/sbin/systemsetup -setremotelogin off || true
    /System/Library/CoreServices/RemoteManagement/ARDAgent.app/Contents/Resources/kickstart -deactivate -configure -access -off || true
  '';

  system.activationScripts.postActivation.text = ''
    /System/Library/PrivateFrameworks/SystemAdministration.framework/Resources/activateSettings -u
  '';
}
