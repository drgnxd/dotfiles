{ lib, ... }:

let
  render_with_theme = import ../../lib/render-theme.nix { inherit lib; };
in

{
  imports = [
    ./hyprland.nix
    ./waybar.nix
    ./fcitx5.nix
  ];

  xdg.configFile = {
    "wofi/config".source = ../../../dot_config/wofi/config;
    "wofi/style.css".text = render_with_theme {
      templatePath = ../../../dot_config/wofi/style.css;
    };
    "mako/config".text = render_with_theme {
      templatePath = ../../../dot_config/mako/config;
    };
  };

  home.file = {
    ".local/bin/hypr-cheatsheet" = {
      source = ../../../scripts/linux/hypr-cheatsheet;
      executable = true;
    };
    ".local/bin/hypr-caffeine-toggle" = {
      source = ../../../scripts/linux/hypr-caffeine-toggle;
      executable = true;
    };
    ".local/bin/hypr-caffeine-status" = {
      source = ../../../scripts/linux/hypr-caffeine-status;
      executable = true;
    };
    ".local/bin/hypr-input-watcher" = {
      source = ../../../scripts/linux/hypr-input-watcher;
      executable = true;
    };
  };

  systemd.user.services.hypr-input-watcher = {
    Unit = {
      Description = "Hyprland input source auto-switcher (socket2)";
      PartOf = [ "graphical-session.target" ];
      After = [ "graphical-session.target" ];
    };
    Service = {
      ExecStart = "%h/.local/bin/hypr-input-watcher";
      Restart = "on-failure";
      RestartSec = "3s";
    };
    Install.WantedBy = [ "hyprland-session.target" ];
  };
}
