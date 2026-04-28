{
  config,
  lib,
  pkgs,
  ...
}:

let
  solarized_dark = import ../themes/solarized-dark.nix;
in
{
  xdg.configFile = {
    "alacritty/blur.toml".source = ../../dot_config/alacritty/blur.toml;
  }
  // lib.optionalAttrs pkgs.stdenv.isDarwin {
    "alacritty/toggle_blur.sh" = {
      source = ../../dot_config/alacritty/executable_toggle_blur.sh;
      executable = true;
    };
  };

  programs.alacritty = {
    enable = true;
    settings = {
      general.import = [ "blur.toml" ];

      terminal.shell = {
        program = "${config.home.profileDirectory}/bin/nu";
        args = [
          "-l"
          "--config"
          "${config.xdg.configHome}/nushell/config.nu"
          "--env-config"
          "${config.xdg.configHome}/nushell/env.nu"
        ];
      };

      window = {
        padding = {
          x = 10;
          y = 10;
        };
      }
      // lib.optionalAttrs pkgs.stdenv.isDarwin {
        decorations = "buttonless";
        opacity = 0.75;
        option_as_alt = "OnlyLeft";
      };

      font = {
        size = 13.0;
        normal = {
          family = "HackGen35 Console NF";
          style = "Regular";
        };
      };

      env.TERM = "xterm-256color";

      colors = {
        primary = {
          background = solarized_dark.base03;
          foreground = solarized_dark.base0;
        };

        normal = {
          black = solarized_dark.base02;
          inherit (solarized_dark)
            red
            green
            yellow
            blue
            magenta
            cyan
            ;
          white = solarized_dark.base2;
        };

        bright = {
          black = solarized_dark.base03;
          red = solarized_dark.orange;
          green = solarized_dark.base01;
          yellow = solarized_dark.base00;
          blue = solarized_dark.base0;
          magenta = solarized_dark.violet;
          cyan = solarized_dark.base1;
          white = solarized_dark.base3;
        };
      };

      keyboard.bindings = lib.optionals pkgs.stdenv.isDarwin [
        {
          key = "B";
          mods = "Command";
          command = {
            program = "/bin/sh";
            args = [
              "-c"
              "\${XDG_CONFIG_HOME:-$HOME/.config}/alacritty/toggle_blur.sh"
            ];
          };
        }
      ];
    };
  };
}
