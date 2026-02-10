{ config, lib, pkgs, ... }:

let
  user = "drgnxd";
  home_dir = "/Users/drgnxd";
in
{
  nix.enable = false;
  nixpkgs.config.allowUnfree = true;

  system.stateVersion = 5;

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
    brews = [ "mas" ];
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
    hammerspoon = {
      serviceConfig = {
        ProgramArguments = [ "/Applications/Hammerspoon.app/Contents/MacOS/Hammerspoon" ];
        EnvironmentVariables = {
          LANG = "en_US.UTF-8";
          LC_ALL = "en_US.UTF-8";
        };
        RunAtLoad = true;
        KeepAlive = false;
        ProcessType = "Interactive";
        StandardOutPath = "${home_dir}/.local/state/launchagents/hammerspoon/stdout.log";
        StandardErrorPath = "${home_dir}/.local/state/launchagents/hammerspoon/stderr.log";
        Umask = 77;
      };
    };

    maccy = {
      serviceConfig = {
        ProgramArguments = [ "/usr/bin/open" "-a" "Maccy" ];
        EnvironmentVariables = {
          LANG = "en_US.UTF-8";
          LC_ALL = "en_US.UTF-8";
        };
        RunAtLoad = true;
        KeepAlive = false;
        ProcessType = "Interactive";
        StandardOutPath = "${home_dir}/.local/state/launchagents/maccy/stdout.log";
        StandardErrorPath = "${home_dir}/.local/state/launchagents/maccy/stderr.log";
        Umask = 77;
      };
    };

    stats = {
      serviceConfig = {
        ProgramArguments = [ "/usr/bin/open" "-a" "Stats" ];
        EnvironmentVariables = {
          LANG = "en_US.UTF-8";
          LC_ALL = "en_US.UTF-8";
        };
        RunAtLoad = true;
        KeepAlive = false;
        ProcessType = "Interactive";
        StandardOutPath = "${home_dir}/.local/state/launchagents/stats/stdout.log";
        StandardErrorPath = "${home_dir}/.local/state/launchagents/stats/stderr.log";
        Umask = 77;
      };
    };

    login-alacritty = {
      serviceConfig = {
        ProgramArguments = [ "/usr/bin/open" "-a" "Alacritty" ];
        RunAtLoad = true;
        KeepAlive = false;
        ProcessType = "Interactive";
      };
    };

    login-floorp = {
      serviceConfig = {
        ProgramArguments = [ "/usr/bin/open" "-a" "Floorp" ];
        RunAtLoad = true;
        KeepAlive = false;
        ProcessType = "Interactive";
      };
    };

    login-proton-mail = {
      serviceConfig = {
        ProgramArguments = [ "/usr/bin/open" "-a" "Proton Mail" ];
        RunAtLoad = true;
        KeepAlive = false;
        ProcessType = "Interactive";
      };
    };

    login-proton-pass = {
      serviceConfig = {
        ProgramArguments = [ "/usr/bin/open" "-a" "Proton Pass" ];
        RunAtLoad = true;
        KeepAlive = false;
        ProcessType = "Interactive";
      };
    };

    login-protonvpn = {
      serviceConfig = {
        ProgramArguments = [ "/usr/bin/open" "-a" "ProtonVPN" ];
        RunAtLoad = true;
        KeepAlive = false;
        ProcessType = "Interactive";
      };
    };

    login-sol = {
      serviceConfig = {
        ProgramArguments = [ "/usr/bin/open" "-a" "Sol" ];
        RunAtLoad = true;
        KeepAlive = false;
        ProcessType = "Interactive";
      };
    };
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
