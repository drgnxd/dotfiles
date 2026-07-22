# LaunchAgent management
#
# All launch agent definitions and app-native agent cleanup in one place.
# nix-darwin manages the agents; activation scripts disable duplicate
# "Launch at Login" agents that apps create on their own.
{
  lib,
  pkgs,
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

  # `open -a <app>` wrapped in a name-specific derivation so the process
  # shows up in macOS's Background Activity as e.g. "open-floorp" instead
  # of a generic "open" indistinguishable from every other login item.
  mkOpenWrapper =
    id: appName:
    pkgs.writeShellApplication {
      name = "open-${id}";
      text = ''exec /usr/bin/open -a "${appName}" "$@"'';
    };

  # Simple login app agent (open -a), routed through a named wrapper
  mkLoginApp = id: appName: {
    serviceConfig = {
      ProgramArguments = [ "${mkOpenWrapper id appName}/bin/open-${id}" ];
      RunAtLoad = true;
      KeepAlive = false;
      ProcessType = "Interactive";
    };
  };

  # Disable app-native "Launch at Login" agent to prevent double-launch.
  # Apps like Stats, Hammerspoon, and Maccy register their own LaunchAgent
  # when "Launch at Login" is enabled in their preferences.  Since
  # nix-darwin already manages the agent, the app-native one must be
  # suppressed. The plist is deleted rather than renamed so no inert file
  # lingers in ~/Library/LaunchAgents for the security audit to flag as
  # undeclared persistence.
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

      /bin/rm -f "$launch_agent" "$launch_agent_disabled"
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
      programArgs = [ "${mkOpenWrapper "maccy" "Maccy"}/bin/open-maccy" ];
    };
    stats = mkManagedAgent {
      name = "stats";
      programArgs = [ "${mkOpenWrapper "stats" "Stats"}/bin/open-stats" ];
    };

    # Sets the SCIHOME env var (Scilab's config home) for GUI-launched apps.
    # Supersedes a hand-installed ~/Library/LaunchAgents/setenv.SCIHOME.plist.
    setenv-scihome = mkManagedAgent {
      name = "setenv-scihome";
      programArgs = [
        "/bin/launchctl"
        "setenv"
        "SCIHOME"
        "${home_dir}/.config/scilab"
      ];
    };

    # Simple login apps: open -a at login
    login-alacritty = mkLoginApp "alacritty" "Alacritty";
    login-floorp = mkLoginApp "floorp" "Floorp";
    login-proton-mail = mkLoginApp "proton-mail" "Proton Mail";
    login-proton-pass = mkLoginApp "proton-pass" "Proton Pass";
    login-protonvpn = mkLoginApp "protonvpn" "ProtonVPN";
    login-sol = mkLoginApp "sol" "Sol";
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

      home.activation.disableMaccyLaunchAtLogin =
        lib.hm.dag.entryAfter [ "writeBoundary" ]
          (disable_login_launch_agent {
            plist_name = "org.p0deje.Maccy";
            labels = [ "org.p0deje.Maccy" ];
          });

      # One-time cleanup of the hand-installed agent now superseded by
      # the declared setenv-scihome agent above.
      home.activation.removeLegacyScihomeAgent = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
        /bin/launchctl bootout "gui/$(/usr/bin/id -u)/setenv.SCIHOME" 2>/dev/null || true
        /bin/rm -f "$HOME/Library/LaunchAgents/setenv.SCIHOME.plist"
      '';
    };
}
