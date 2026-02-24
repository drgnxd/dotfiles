{ lib, ... }:

let
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
}
