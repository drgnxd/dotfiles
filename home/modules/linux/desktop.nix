{
  config,
  lib,
  pkgs,
  ...
}:

let
  home_dir = config.home.homeDirectory;
  config_home = config.xdg.configHome;
  render_with_theme = import ../../lib/render-theme.nix { inherit lib; };
in

{
  fonts.fontconfig.enable = true;

  imports = [
    ./hyprland.nix
    ./waybar.nix
    ./fcitx5.nix
  ];

  xdg.userDirs = {
    enable = true;
    createDirectories = true;
    setSessionVariables = true;
    desktop = "${home_dir}/Desktop";
    documents = "${home_dir}/Documents";
    download = "${home_dir}/Downloads";
    music = "${home_dir}/Music";
    pictures = "${home_dir}/Pictures";
    projects = null;
    publicShare = "${home_dir}/Public";
    templates = "${home_dir}/Templates";
    videos = "${home_dir}/Videos";
  };

  xdg.configFile = {
    "user-dirs.locale".text = "C\n";
    "wofi/config".source = ../../../dot_config/wofi/config;
    "wofi/style.css".text = render_with_theme {
      templatePath = ../../../dot_config/wofi/style.css;
    };
    "mako/config".text = render_with_theme {
      templatePath = ../../../dot_config/mako/config;
    };
  };

  home.activation.migrateLocalizedXdgUserDirs = lib.hm.dag.entryBefore [ "checkLinkTargets" ] ''
    is_store_symlink() {
      target="$1"
      if [ ! -L "$target" ]; then
        return 1
      fi

      link_target="$(readlink "$target")"
      case "$link_target" in
        /nix/store/*) return 0 ;;
        *) return 1 ;;
      esac
    }

    backup_managed_config() {
      target="$1"
      backup="$target.before-nix"

      if [ ! -e "$target" ] && [ ! -L "$target" ]; then
        return 0
      fi

      if is_store_symlink "$target"; then
        return 0
      fi

      if [ -e "$backup" ] || [ -L "$backup" ]; then
        backup="$target.before-nix.$(date +%s)"
      fi

      $DRY_RUN_CMD mv "$target" "$backup"
    }

    migrate_user_dir() {
      src="${home_dir}/$1"
      dest="${home_dir}/$2"

      if [ ! -d "$src" ] || [ -L "$src" ]; then
        return 0
      fi

      if [ ! -e "$dest" ] && [ ! -L "$dest" ]; then
        $DRY_RUN_CMD mv "$src" "$dest"
        return 0
      fi

      if [ ! -d "$dest" ] || [ -L "$dest" ]; then
        echo "Skipping XDG user dir migration: destination is not a directory: $dest" >&2
        return 0
      fi

      has_conflicts=0
      for entry in "$src"/* "$src"/.[!.]* "$src"/..?*; do
        if [ ! -e "$entry" ] && [ ! -L "$entry" ]; then
          continue
        fi

        base="$(basename "$entry")"
        if [ -e "$dest/$base" ] || [ -L "$dest/$base" ]; then
          echo "Skipping XDG user dir entry migration: already exists: $dest/$base" >&2
          has_conflicts=1
          continue
        fi

        $DRY_RUN_CMD mv "$entry" "$dest/"
      done

      if [ "$has_conflicts" -eq 0 ]; then
        $DRY_RUN_CMD rmdir "$src" 2>/dev/null || true
      else
        echo "Leaving localized XDG user dir because conflicting entries remain: $src" >&2
      fi
    }

    backup_managed_config "${config_home}/user-dirs.dirs"
    backup_managed_config "${config_home}/user-dirs.conf"
    backup_managed_config "${config_home}/user-dirs.locale"

    migrate_user_dir "デスクトップ" "Desktop"
    migrate_user_dir "ダウンロード" "Downloads"
    migrate_user_dir "テンプレート" "Templates"
    migrate_user_dir "公開" "Public"
    migrate_user_dir "ドキュメント" "Documents"
    migrate_user_dir "ミュージック" "Music"
    migrate_user_dir "ピクチャ" "Pictures"
    migrate_user_dir "ビデオ" "Videos"
  '';

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

  systemd.user.services.swayosd = {
    Unit = {
      Description = "SwayOSD server";
      PartOf = [ "graphical-session.target" ];
      After = [ "graphical-session.target" ];
    };
    Service = {
      ExecStart = "${pkgs.swayosd}/bin/swayosd-server";
      Restart = "on-failure";
      RestartSec = "3s";
    };
    Install.WantedBy = [ "hyprland-session.target" ];
  };
}
