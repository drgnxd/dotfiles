{
  config,
  lib,
  pkgs,
  user,
  ...
}:

let
  home_dir = "/Users/${user}";
in
{
  imports = [ ./launchd.nix ];
  nix.enable = false;
  nixpkgs.config.allowUnfree = true;

  system.stateVersion = 5;

  # ── macOS system defaults (declarative) ──────────────────────────────
  system.defaults = {
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

    dock = {
      autohide = true;
      autohide-delay = 0.0;
      autohide-time-modifier = 0.0;
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

  home-manager.backupFileExtension = "before-nix";

  homebrew = {
    enable = true;
    onActivation = {
      autoUpdate = false;
      upgrade = false;
      cleanup = "zap";
    };
    taps = [
      "protonpass/homebrew-tap"
    ];
    brews = [
      "mas"
      "pass-cli"
    ];
    casks = [
      "hammerspoon"
      "pearcleaner"
      "sol"
      "stats"

      "gimp"
      "floorp"
      "google-chrome"
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

  age.secrets = lib.mkMerge [
    (lib.optionalAttrs (builtins.pathExists ../../secrets/gh-hosts.age) {
      gh-hosts = {
        file = ../../secrets/gh-hosts.age;
        path = "${home_dir}/.config/gh/hosts.yml";
        owner = user;
        group = "staff";
      };
    })
    (lib.optionalAttrs (builtins.pathExists ../../secrets/npmrc.age) {
      npmrc = {
        file = ../../secrets/npmrc.age;
        path = "${home_dir}/.config/npm/npmrc";
        owner = user;
        group = "staff";
      };
    })
    (lib.optionalAttrs (builtins.pathExists ../../secrets/git-config-local.age) {
      git-config-local = {
        file = ../../secrets/git-config-local.age;
        path = "${home_dir}/.config/git/config.local";
        owner = user;
        group = "staff";
      };
    })
  ];

  system.activationScripts.securityHardening.text = ''
    /usr/bin/defaults delete /Library/Preferences/com.apple.loginwindow LoginwindowText 2>/dev/null || true

    /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on || true
    /usr/libexec/ApplicationFirewall/socketfilterfw --setstealthmode on || true
    /usr/libexec/ApplicationFirewall/socketfilterfw --setallowsigned on || true
    /usr/bin/pkill -HUP socketfilterfw 2>/dev/null || true

    /usr/sbin/systemsetup -setremotelogin off || true
    /System/Library/CoreServices/RemoteManagement/ARDAgent.app/Contents/Resources/kickstart -deactivate -configure -access -off || true
    /usr/sbin/sysadminctl -guestAccount off || true
  '';
}
