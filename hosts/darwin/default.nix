{
  pkgs,
  user,
  ...
}:

let
  home_dir = "/Users/${user}";

  # User launchd session environment. nix-darwin applies this only during
  # activation (a one-shot `launchctl setenv` per key); the values are not
  # persisted, so a reboot or any recreation of the user launchd session
  # drops all of them until the next `darwin-rebuild`. The setenv-user-env
  # agent in ./launchd.nix replays this exact set at login to work around
  # that, so keep it as the single source of truth.
  user_launchd_env = {
    PATH = "${home_dir}/.nix-profile/bin:/etc/profiles/per-user/${user}/bin:/run/current-system/sw/bin:/nix/var/nix/profiles/default/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin";
    CLAUDE_CONFIG_DIR = "${home_dir}/.local/share/claude";
    XDG_CONFIG_HOME = "${home_dir}/.config";
    XDG_CACHE_HOME = "${home_dir}/.cache";
    XDG_DATA_HOME = "${home_dir}/.local/share";
    XDG_STATE_HOME = "${home_dir}/.local/state";
    CODEX_HOME = "${home_dir}/.local/share/codex";
    NPM_CONFIG_CACHE = "${home_dir}/.cache/npm";
    NPM_CONFIG_PREFIX = "${home_dir}/.local/share/npm";
    NPM_CONFIG_USERCONFIG = "${home_dir}/.config/npm/npmrc";
  };
in
{
  imports = [ ./launchd.nix ];
  _module.args.userLaunchdEnv = user_launchd_env;
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

  system.defaults = {
    SoftwareUpdate.AutomaticallyInstallMacOSUpdates = false;
    CustomSystemPreferences."/Library/Preferences/com.apple.SoftwareUpdate" = {
      AutomaticCheckEnabled = true;
      AutomaticDownload = true;
    };

    NSGlobalDomain = {
      NSNavPanelExpandedStateForSaveMode = true;
      NSNavPanelExpandedStateForSaveMode2 = true;
      PMPrintingExpandedStateForPrint = true;
      PMPrintingExpandedStateForPrint2 = true;

      AppleMeasurementUnits = "Centimeters";
      AppleMetricUnits = 1;
      AppleTemperatureUnit = "Celsius";

      NSAutomaticSpellingCorrectionEnabled = false;
      NSAutomaticCapitalizationEnabled = false;
      NSAutomaticQuoteSubstitutionEnabled = false;
      NSAutomaticDashSubstitutionEnabled = false;
      NSAutomaticPeriodSubstitutionEnabled = false;

      AppleShowAllExtensions = true;

      KeyRepeat = 1;
      InitialKeyRepeat = 15;
      ApplePressAndHoldEnabled = false;

      # Fixed Dark mode (no time-based auto switching): keeps the UI
      # surround luminance constant for color-critical viewing/comparison.
      AppleInterfaceStyle = "Dark";
      AppleInterfaceStyleSwitchesAutomatically = false;
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
      _FXShowPosixPathInTitle = false;
      ShowStatusBar = true;
      ShowPathbar = true;
      _FXSortFoldersFirst = true;
      FXDefaultSearchScope = "SCcf";
      FXPreferredViewStyle = "clmv";
      FXEnableExtensionChangeWarning = false;
    };

    screencapture = {
      disable-shadow = true;
      type = "png";
      location = "~/Desktop/Screenshots";
    };

    # NOTE: system.defaults.universalaccess.reduceTransparency was tried
    # here for color-viewing consistency but removed: on this macOS
    # version `defaults write com.apple.universalaccess ...` is TCC-blocked
    # even under sudo ("Could not write domain com.apple.universalaccess;
    # exiting"), and that failure was observed to abort the rest of the
    # user-defaults activation step, silently skipping later settings
    # (e.g. CustomUserPreferences.NSGlobalDomain.AppleAccentColor). Reduce
    # Transparency defaults to Off anyway, so the loss is minimal; set it
    # manually in System Settings > Accessibility > Display if it drifts.

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
      # Accessibility color-shifting filters, kept off for the same
      # color-consistency reason as universalaccess.reduceTransparency
      # above. No dedicated nix-darwin option exists for this domain.
      "com.apple.Accessibility" = {
        DifferentiateWithoutColor = false;
        EnhancedBackgroundContrastEnabled = false;
        AXSClassicInvertColorsPreference = false;
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
    CODEX_HOME = "$HOME/.local/share/codex";
    # compinit (run by macOS's /etc/zshrc) writes its dump to ZDOTDIR; must be
    # set via /etc/zshenv (sourced before /etc/zshrc) to take effect.
    ZDOTDIR = "$HOME/.config/zsh";
  };
  # Seed direct user agents. LaunchServices apps may sanitize this environment,
  # so terminal-specific variables are also declared in the Alacritty config.
  # Replayed at login by the setenv-user-env agent in ./launchd.nix; see the
  # user_launchd_env binding above.
  launchd.user.envVariables = user_launchd_env;

  home-manager.backupFileExtension = "before-nix";

  homebrew = {
    enable = true;
    onActivation = {
      autoUpdate = false;
      upgrade = false;
      cleanup = "zap";
      extraFlags = [ "--force" ];
    };
    taps = [
      "protonpass/tap"
    ];
    brews = [
      "mas"
      "pass-cli"
      # nixpkgs' ollama build disables MLX (-DOLLAMA_MLX_BACKENDS=""); Homebrew's
      # formula depends on mlx-c and builds with MLX support for Apple Silicon.
      "ollama"
    ];
    casks = [
      "codex"
      "codexbar"
      "copilot-cli"
      "qlmarkdown"
      "sol"
      "stats"

      "gimp"
      "floorp"
      "libreoffice"

      "kicad"
      "orcaslicer"
      "signal"

      "logi-options+"

      "proton-drive"
      "proton-mail"
      "proton-pass"
      "protonvpn"
      "scilab"
      "tailscale"
    ];
    masApps = {
      "Proton Pass for Safari" = 6502835663;
    };
  };

  fonts.packages = with pkgs; [
    plemoljp-nf
    ibm-plex
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
