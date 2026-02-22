{ config, ... }:

{
  xdg.configFile."zellij/config.kdl".text = ''
    theme "solarized-dark"
    show_release_notes false
    show_startup_tips false
    default_shell "${config.home.profileDirectory}/bin/nu"
  '';
}
