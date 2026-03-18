# LaunchAgent management
#
# All launch agent definitions and app-native agent cleanup in one place.
# nix-darwin manages the agents; activation scripts disable duplicate
# "Launch at Login" agents that apps create on their own.
{
  lib,
  user,
  ...
}:

let
  home_dir = "/Users/${user}";

  # ── Helpers ──────────────────────────────────────────────────────────

  # Managed LaunchAgent with UTF-8 environment, logging, and strict umask
  mkManagedAgent =
    { name, programArgs }:
    {
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

  # Simple login app agent (open -a)
  mkLoginApp = appName: {
    serviceConfig = {
      ProgramArguments = [
        "/usr/bin/open"
        "-a"
        appName
      ];
      RunAtLoad = true;
      KeepAlive = false;
      ProcessType = "Interactive";
    };
  };

  # Disable app-native "Launch at Login" agent to prevent double-launch.
  # Apps like Stats and Hammerspoon register their own LaunchAgent when
  # "Launch at Login" is enabled in their preferences.  Since nix-darwin
  # already manages the agent, the app-native one must be suppressed.
  disable_login_launch_agent =
    { plist_name, labels }:
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
  # ── nix-darwin LaunchAgent definitions ───────────────────────────────

  launchd.user.agents = {
    # Managed agents: environment variables, logging, and umask
    hammerspoon = mkManagedAgent {
      name = "hammerspoon";
      programArgs = [ "/Applications/Hammerspoon.app/Contents/MacOS/Hammerspoon" ];
    };
    maccy = mkManagedAgent {
      name = "maccy";
      programArgs = [
        "/usr/bin/open"
        "-a"
        "Maccy"
      ];
    };
    stats = mkManagedAgent {
      name = "stats";
      programArgs = [
        "/usr/bin/open"
        "-a"
        "Stats"
      ];
    };

    # Simple login apps: open -a at login
    login-alacritty = mkLoginApp "Alacritty";
    login-floorp = mkLoginApp "Floorp";
    login-proton-mail = mkLoginApp "Proton Mail";
    login-proton-pass = mkLoginApp "Proton Pass";
    login-protonvpn = mkLoginApp "ProtonVPN";
    login-sol = mkLoginApp "Sol";
  };

  # ── App-native agent cleanup (home-manager activation) ──────────────

  home-manager.users.${user} =
    { lib, ... }:
    {
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

      home.activation.disableStatsLaunchAtLogin =
        lib.hm.dag.entryAfter [ "importStats" ]
          (disable_login_launch_agent {
            plist_name = "eu.exelban.Stats";
            labels = [
              "eu.exelban.Stats"
              "eu.exelban.Stats.LaunchAtLogin"
            ];
          });

      home.activation.disableHammerspoonLaunchAtLogin =
        lib.hm.dag.entryAfter [ "writeBoundary" ]
          (disable_login_launch_agent {
            plist_name = "org.hammerspoon.Hammerspoon";
            labels = [
              "org.hammerspoon.Hammerspoon"
              "org.hammerspoon.Hammerspoon.LaunchAtLogin"
            ];
          });
    };
}
