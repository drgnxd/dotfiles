# OpenCode asset contract:
# - Read-only managed assets are store symlinks via xdg.configFile.
# - OpenCode-writable files stay as real files synced during activation.
# - AGENTS.md is synced as a real file built by concatenating the public
#   global_rules.md template with a machine-local, git-ignored AGENTS.local.md
#   appendix, so machine-specific paths never enter the public repo.
# - Custom tools are synced as real files because Bun resolves imports from
#   realpaths and store symlinks cannot reach ~/.config/opencode/node_modules.
# - Conflicting real files at migrated symlink paths are backed up as `.before-nix`.
{ config, lib, ... }:

let
  opencode_template = ../../../dot_config/opencode/opencode.json;
  opencode_local_example = ../../../dot_config/opencode/opencode.local.json.example;
  opencode_agents_template = ../../../dot_config/opencode/global_rules.md;
  opencode_agents_local_example = ../../../dot_config/opencode/AGENTS.local.md.example;
  opencode_notifier_template = ../../../dot_config/opencode/opencode-notifier.json;
  opencode_package_template = ../../../dot_config/opencode/package.json;
  opencode_tools_template = ../../../dot_config/opencode/tools;
  opencode_skills_dir = ../../../dot_config/opencode/skills;
  skillEntries = builtins.readDir opencode_skills_dir;
  managedSkillNames = builtins.filter (name: skillEntries.${name} == "directory") (
    builtins.attrNames skillEntries
  );
  managedSkills = builtins.listToAttrs (
    map (name: {
      inherit name;
      value = opencode_skills_dir + "/${name}";
    }) managedSkillNames
  );
  opencode_target = "${config.xdg.configHome}/opencode/opencode.json";
  opencode_local_override = "${config.xdg.configHome}/opencode/opencode.local.json";
  opencode_local_example_target = "${config.xdg.configHome}/opencode/opencode.local.json.example";
  agents_target = "${config.xdg.configHome}/opencode/AGENTS.md";
  agents_local_override = "${config.xdg.configHome}/opencode/AGENTS.local.md";
  agents_local_example_target = "${config.xdg.configHome}/opencode/AGENTS.local.md.example";
  legacyOpencodeAssets = [
    "command"
    "requirements.txt"
    "skills/tools"
    "skills/infrastructure"
    "skills/languages"
    "skills/practices"
  ];
  migratedAssetTargets = [
    "${config.xdg.configHome}/opencode/opencode-notifier.json"
  ]
  ++ lib.mapAttrsToList (name: _: "${config.xdg.configHome}/opencode/skills/${name}") managedSkills;
  migrateManagedAssetCommands = builtins.concatStringsSep "\n" (
    map (target: ''
      migrate_managed_asset "${target}"
    '') migratedAssetTargets
  );
in
{
  xdg.configFile = {
    "opencode/opencode-notifier.json".source = opencode_notifier_template;
  }
  // lib.mapAttrs' (
    name: src: lib.nameValuePair "opencode/skills/${name}" { source = src; }
  ) managedSkills;

  home.activation.migrateOpencodeManagedAssets = lib.hm.dag.entryBefore [ "checkLinkTargets" ] ''
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

    migrate_managed_asset() {
      target="$1"
      backup="$target.before-nix"

      if [ -e "$target" ] || [ -L "$target" ]; then
        if is_store_symlink "$target"; then
          return 0
        fi

        $DRY_RUN_CMD mv -f "$target" "$backup"
      fi
    }

    ${migrateManagedAssetCommands}
  '';

  home.activation.removeLegacyOpencodeAssets = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    opencode_dir="${config.xdg.configHome}/opencode"

    # Remove only store symlinks created by older generations; preserve user files.
    remove_legacy_store_symlink() {
      target="$1"
      if [ ! -L "$target" ]; then
        return 0
      fi

      link_target="$(readlink "$target")"
      case "$link_target" in
        /nix/store/*) $DRY_RUN_CMD rm -f "$target" ;;
      esac
    }

    ${builtins.concatStringsSep "\n" (
      map (path: ''
        remove_legacy_store_symlink "$opencode_dir/${path}"
      '') legacyOpencodeAssets
    )}
  '';

  home.activation.ensureOpencodeLocalConfig = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    opencode_local_override="${opencode_local_override}"
    opencode_local_example_target="${opencode_local_example_target}"
    opencode_dir="$(dirname "$opencode_local_override")"
    mkdir -p "$opencode_dir"
    if [ ! -f "$opencode_local_override" ]; then
      touch "$opencode_local_override"
    fi
    if [ ! -f "$opencode_local_example_target" ]; then
      cp -f "${opencode_local_example}" "$opencode_local_example_target"
    fi
    chmod u+w "$opencode_local_override" "$opencode_local_example_target"
  '';

  home.activation.ensureOpencodeAgentsLocal = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    agents_local_override="${agents_local_override}"
    agents_local_example_target="${agents_local_example_target}"
    agents_dir="$(dirname "$agents_local_override")"
    mkdir -p "$agents_dir"
    if [ ! -f "$agents_local_override" ]; then
      touch "$agents_local_override"
    fi
    if [ ! -f "$agents_local_example_target" ]; then
      cp -f "${opencode_agents_local_example}" "$agents_local_example_target"
    fi
    chmod u+w "$agents_local_override" "$agents_local_example_target"
  '';

  home.activation.syncOpencodeAgents = lib.hm.dag.entryAfter [ "ensureOpencodeAgentsLocal" ] ''
    agents_target="${agents_target}"
    agents_local_override="${agents_local_override}"
    agents_dir="$(dirname "$agents_target")"
    mkdir -p "$agents_dir"

    {
      cat "${opencode_agents_template}"
      if [ -s "$agents_local_override" ]; then
        printf '\n'
        cat "$agents_local_override"
      fi
    } > "$agents_target.tmp"
    mv -f "$agents_target.tmp" "$agents_target"
    chmod u+w "$agents_target"
  '';

  home.activation.syncOpencodeConfig = lib.hm.dag.entryAfter [ "ensureOpencodeLocalConfig" ] ''
    opencode_target="${opencode_target}"
    opencode_local_override="${opencode_local_override}"
    opencode_dir="$(dirname "$opencode_target")"
    mkdir -p "$opencode_dir"
    if [ -s "$opencode_local_override" ]; then
      cp -f "$opencode_local_override" "$opencode_target"
    else
      cp -f "${opencode_template}" "$opencode_target"
    fi
    chmod u+w "$opencode_target"
  '';

  home.activation.syncOpencodeTools = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    tools_src="${opencode_tools_template}"
    tools_dest="${config.xdg.configHome}/opencode/tools"

    # Bun resolves imports from a file's realpath; a Nix-store symlink makes
    # ~/.config/opencode/node_modules unreachable from custom tools. Sync real files.
    if [ -L "$tools_dest" ]; then
      $DRY_RUN_CMD rm -f "$tools_dest"
    fi
    $DRY_RUN_CMD mkdir -p "$tools_dest"

    for src_file in "$tools_src"/*; do
      [ -e "$src_file" ] || continue
      base="$(basename "$src_file")"
      dest_file="$tools_dest/$base"
      if [ -f "$dest_file" ] && diff -q "$src_file" "$dest_file" >/dev/null 2>&1; then
        continue
      fi
      $DRY_RUN_CMD cp -fL "$src_file" "$dest_file"
      $DRY_RUN_CMD chmod u+w "$dest_file"
    done

    for dest_file in "$tools_dest"/*; do
      [ -e "$dest_file" ] || continue
      base="$(basename "$dest_file")"
      if [ ! -e "$tools_src/$base" ]; then
        $DRY_RUN_CMD rm -f "$dest_file"
      fi
    done
  '';

  home.activation.syncOpencodeRules = lib.hm.dag.entryAfter [ "syncOpencodeConfig" ] ''
    opencode_target="${opencode_target}"
    opencode_local_override="${opencode_local_override}"
    opencode_local_example_target="${opencode_local_example_target}"
    opencode_dir="$(dirname "$opencode_target")"
    backup_suffix=".before-nix"

    sync_managed_file() {
      src_file="$1"
      dest_file="$2"
      backup_file="$dest_file$backup_suffix"

      mkdir -p "$(dirname "$dest_file")"

      if [ -e "$dest_file" ] || [ -L "$dest_file" ]; then
        if diff -q "$src_file" "$dest_file" >/dev/null 2>&1; then
          return 0
        fi
        mv -f "$dest_file" "$backup_file"
      fi

      cp -f "$src_file" "$dest_file"
      chmod u+w "$dest_file"
    }

    mkdir -p "$opencode_dir"

    sync_managed_file "${opencode_package_template}" "$opencode_dir/package.json"

    # Keep only the real files OpenCode writes back to user-writable.
    chmod u+w \
      "$opencode_target" \
      "$opencode_local_override" \
      "$opencode_local_example_target" \
      "$opencode_dir/package.json"
  '';
}
