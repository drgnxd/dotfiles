_:

{
  imports = [
    ./hyprland.nix
    ./waybar.nix
    ./fcitx5.nix
  ];

  xdg.configFile = {
    "wofi/config".source = ../../../dot_config/wofi/config;
    "wofi/style.css".source = ../../../dot_config/wofi/style.css;
    "mako/config".source = ../../../dot_config/mako/config;
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
  };
}
