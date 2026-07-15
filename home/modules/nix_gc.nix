{
  config,
  lib,
  pkgs,
  ...
}:

let
  gc_script = pkgs.writeShellApplication {
    name = "nix-gc-run";
    runtimeInputs = [ pkgs.nh ];
    text = ''
      # Determinate Nix installs the daemon profile here; launchd/systemd user units
      # do not inherit an interactive PATH, so nix must be reachable explicitly.
      export PATH="$PATH:/nix/var/nix/profiles/default/bin:/usr/bin:/bin"
      nh clean user --keep 5 --keep-since 7d
    '';
  };
in
lib.mkMerge [
  (lib.mkIf pkgs.stdenv.isDarwin {
    launchd.agents.nix-gc = {
      enable = true;
      config = {
        ProgramArguments = [ "${gc_script}/bin/nix-gc-run" ];
        StartCalendarInterval = [
          {
            Weekday = 0;
            Hour = 5;
            Minute = 0;
          }
        ];
        RunAtLoad = false;
        KeepAlive = false;
        ProcessType = "Background";
        StandardOutPath = "${config.home.homeDirectory}/.local/state/launchagents/nix-gc/stdout.log";
        StandardErrorPath = "${config.home.homeDirectory}/.local/state/launchagents/nix-gc/stderr.log";
      };
    };
  })

  (lib.mkIf pkgs.stdenv.isLinux {
    systemd.user.services.nix-gc = {
      Unit.Description = "Weekly Nix store garbage collection (nh clean)";
      Service = {
        Type = "oneshot";
        ExecStart = "${gc_script}/bin/nix-gc-run";
      };
    };

    systemd.user.timers.nix-gc = {
      Unit.Description = "Weekly Nix GC timer";
      Timer = {
        OnCalendar = "Sun 05:00";
        Persistent = true;
      };
      Install.WantedBy = [ "timers.target" ];
    };
  })
]
