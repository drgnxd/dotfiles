{ config, lib, pkgs, ... }:

let
  user = "drgnxd";
  home_dir = "/Users/drgnxd";

  # Helper: managed LaunchAgent with environment variables, logging, and umask
  mkManagedAgent = { name, programArgs }: {
    serviceConfig = {
      ProgramArguments = programArgs;
      EnvironmentVariables = {
        LANG = "en_US.UTF-8";
        LC_ALL = "en_US.UTF-8";
      };
      RunAtLoad = true;
      KeepAlive = false;
      ProcessType = "Interactive";
      StandardOutPath = "${home_dir}/.local/state/launchagents/${name}/stdout.log";
      StandardErrorPath = "${home_dir}/.local/state/launchagents/${name}/stderr.log";
      Umask = 77;
    };
  };

  # Helper: simple login app LaunchAgent (open -a)
  mkLoginApp = appName: {
    serviceConfig = {
      ProgramArguments = [ "/usr/bin/open" "-a" appName ];
      RunAtLoad = true;
      KeepAlive = false;
      ProcessType = "Interactive";
    };
  };
in
{
  nix.enable = false;
  nixpkgs.config.allowUnfree = true;

  system.stateVersion = 5;

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
      "font-hackgen-nerd"

      "gimp"
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

  fonts.packages = [
    pkgs.hackgen-font
  ];

  users.users.${user}.home = home_dir;
  system.primaryUser = user;

  launchd.user.agents = {
    # Managed agents: environment variables, logging, and umask
    hammerspoon = mkManagedAgent {
      name = "hammerspoon";
      programArgs = [ "/Applications/Hammerspoon.app/Contents/MacOS/Hammerspoon" ];
    };
    maccy = mkManagedAgent {
      name = "maccy";
      programArgs = [ "/usr/bin/open" "-a" "Maccy" ];
    };
    stats = mkManagedAgent {
      name = "stats";
      programArgs = [ "/usr/bin/open" "-a" "Stats" ];
    };

    # Simple login apps: open -a at login
    login-alacritty  = mkLoginApp "Alacritty";
    login-floorp     = mkLoginApp "Floorp";
    login-proton-mail = mkLoginApp "Proton Mail";
    login-proton-pass = mkLoginApp "Proton Pass";
    login-protonvpn  = mkLoginApp "ProtonVPN";
    login-sol        = mkLoginApp "Sol";
  };

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
