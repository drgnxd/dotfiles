{
  config,
  lib,
  pkgs,
  ...
}:

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
          background = "#002b36";
          foreground = "#839496";
        };

        normal = {
          black = "#073642";
          red = "#dc322f";
          green = "#859900";
          yellow = "#b58900";
          blue = "#268bd2";
          magenta = "#d33682";
          cyan = "#2aa198";
          white = "#eee8d5";
        };

        bright = {
          black = "#002b36";
          red = "#cb4b16";
          green = "#586e75";
          yellow = "#657b83";
          blue = "#839496";
          magenta = "#6c71c4";
          cyan = "#93a1a1";
          white = "#fdf6e3";
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
