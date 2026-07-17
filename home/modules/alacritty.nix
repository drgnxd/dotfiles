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
    package = if pkgs.stdenv.isLinux then config.lib.nixGL.wrap pkgs.alacritty else pkgs.alacritty;
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
        opacity = 0.75;
      }
      // lib.optionalAttrs pkgs.stdenv.isDarwin {
        decorations = "buttonless";
        option_as_alt = "OnlyLeft";
      };

      font = {
        size = 13.0;
        normal = {
          family = "HackGen35 Console NF";
          style = "Regular";
        };
      };

      env = {
        CLAUDE_CONFIG_DIR = "${config.xdg.dataHome}/claude";
        TERM = "xterm-256color";
        XDG_CONFIG_HOME = config.xdg.configHome;
        XDG_CACHE_HOME = config.xdg.cacheHome;
        XDG_DATA_HOME = config.xdg.dataHome;
        XDG_STATE_HOME = config.xdg.stateHome;
        PATH = lib.concatStringsSep ":" (
          [ "${config.home.profileDirectory}/bin" ]
          ++ lib.optionals pkgs.stdenv.isDarwin [
            "/run/current-system/sw/bin"
            "/nix/var/nix/profiles/default/bin"
          ]
          ++ [
            "/usr/bin"
            "/bin"
            "/usr/sbin"
            "/sbin"
          ]
        );
      };

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
