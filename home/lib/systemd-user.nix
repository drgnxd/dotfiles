{
  # Standard skeleton for a Hyprland graphical-session user service.
  # Callers pass only what differs (description, ExecStart).
  mkGraphicalUserService =
    {
      description,
      execStart,
      restartSec ? "3s",
    }:
    {
      Unit = {
        Description = description;
        PartOf = [ "graphical-session.target" ];
        After = [ "graphical-session.target" ];
      };
      Service = {
        ExecStart = execStart;
        Restart = "on-failure";
        RestartSec = restartSec;
      };
      Install.WantedBy = [ "hyprland-session.target" ];
    };
}
