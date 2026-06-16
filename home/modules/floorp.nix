{
  config,
  lib,
  pkgs,
  preferences,
  ...
}:

let
  browser_class = preferences.browserClass or "floorp";
  enabled = browser_class == "floorp";
  profile_rel_path =
    if pkgs.stdenv.isDarwin then "Library/Application Support/Floorp/default" else ".floorp/default";
  profile_root =
    if pkgs.stdenv.isDarwin then
      "${config.home.homeDirectory}/Library/Application Support/Floorp"
    else
      "${config.home.homeDirectory}/.floorp";
  settings = import ./floorp/settings.nix;
  awk = "${pkgs.gawk}/bin/awk";
  mkUserJs =
    prefs:
    lib.concatStringsSep "\n" (
      lib.mapAttrsToList (k: v: ''user_pref("${k}", ${builtins.toJSON v});'') prefs
    );
in
{
  config = lib.mkIf enabled {
    home.file."${profile_rel_path}/user.js".text = mkUserJs settings;
    home.file."${profile_rel_path}/chrome/userChrome.css".source =
      ../../dot_config/floorp/chrome/userChrome.css;
    home.file."${profile_rel_path}/chrome/userContent.css".source =
      ../../dot_config/floorp/chrome/userContent.css;

    home.activation.ensureFloorpDefaultProfile = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      profile_root="${profile_root}"
      profile_dir="$profile_root/default"
      profiles_ini="$profile_root/profiles.ini"
      installs_ini="$profile_root/installs.ini"

      write_default_profiles_ini() {
        umask 077
        {
          printf '%s\n' '[General]'
          printf '%s\n' 'StartWithLastProfile=1'
          printf '%s\n' 'Version=2'
          printf '\n'
          printf '%s\n' '[Profile0]'
          printf '%s\n' 'Name=default'
          printf '%s\n' 'IsRelative=1'
          printf '%s\n' 'Path=default'
          printf '%s\n' 'Default=1'
        } >"$profiles_ini"
      }

      next_profile_index() {
        ${awk} '
          /^\[Profile[0-9]+\]$/ {
            index_value = substr($0, 9, length($0) - 9) + 0
            if (index_value >= max) {
              max = index_value + 1
            }
          }
          END { print max + 0 }
        ' "$profiles_ini"
      }

      normalize_profiles_ini() {
        tmp_file="$profiles_ini.tmp.$$"
        ${awk} '
          function set_line(key, value,    i, found) {
            found = 0
            for (i = 1; i <= count; i++) {
              if (lines[i] ~ "^" key "=") {
                lines[i] = key "=" value
                found = 1
              }
            }
            if (!found) {
              lines[++count] = key "=" value
            }
          }

          function flush_section(    i) {
            if (count == 0) {
              return
            }
            if (section == "General") {
              seen_general = 1
              set_line("StartWithLastProfile", "1")
              set_line("Version", "2")
            }
            if (section ~ /^Profile[0-9]+$/ && has_path_default) {
              found_default_profile = 1
              set_line("Name", "default")
              set_line("IsRelative", "1")
              set_line("Path", "default")
              set_line("Default", "1")
            }
            for (i = 1; i <= count; i++) {
              print lines[i]
            }
            delete lines
            count = 0
            section = ""
            has_path_default = 0
          }

          /^\[[^]]+\]$/ {
            flush_section()
            section = substr($0, 2, length($0) - 2)
          }

          {
            lines[++count] = $0
            if ($0 == "Path=default") {
              has_path_default = 1
            }
          }

          END {
            flush_section()
            if (!seen_general) {
              print ""
              print "[General]"
              print "StartWithLastProfile=1"
              print "Version=2"
            }
            if (!found_default_profile) {
              print ""
              print "[Profile" next_index "]"
              print "Name=default"
              print "IsRelative=1"
              print "Path=default"
              print "Default=1"
            }
          }
        ' next_index="$(next_profile_index)" "$profiles_ini" >"$tmp_file"
        mv "$tmp_file" "$profiles_ini"
      }

      normalize_installs_ini() {
        tmp_file="$installs_ini.tmp.$$"
        ${awk} '
          function flush_section(    i) {
            if (count == 0) {
              return
            }
            if (section != "" && !has_default) {
              lines[++count] = "Default=default"
            }
            for (i = 1; i <= count; i++) {
              print lines[i]
            }
            delete lines
            count = 0
            section = ""
            has_default = 0
          }

          /^\[[^]]+\]$/ {
            flush_section()
            section = substr($0, 2, length($0) - 2)
          }

          /^Default=/ && section != "" {
            lines[++count] = "Default=default"
            has_default = 1
            next
          }

          {
            lines[++count] = $0
          }

          END {
            flush_section()
          }
        ' "$installs_ini" >"$tmp_file"
        mv "$tmp_file" "$installs_ini"
      }

      ensure_floorp_profile() {
        mkdir -p "$profile_dir"
        if [ -f "$profiles_ini" ]; then
          normalize_profiles_ini
        else
          write_default_profiles_ini
        fi
        if [ -f "$installs_ini" ]; then
          normalize_installs_ini
        fi
      }

      $DRY_RUN_CMD mkdir -p "$profile_dir"
      run ensure_floorp_profile
    '';
  };
}
