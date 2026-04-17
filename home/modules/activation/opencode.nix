# Sync contract for OpenCode assets:
# - Managed files are refreshed from dotfiles sources on each activation.
# - User-added files in managed directories are preserved.
# - Conflicting edits are backed up as `.before-nix` before replacement.
{ config, lib, ... }:

let
  opencode_template = ../../../dot_config/opencode/opencode.json;
  opencode_local_example = ../../../dot_config/opencode/opencode.local.json.example;
  opencode_agents_template = ../../../dot_config/opencode/AGENTS.md;
  opencode_notifier_template = ../../../dot_config/opencode/opencode-notifier.json;
  opencode_package_template = ../../../dot_config/opencode/package.json;
  opencode_tools_template = ../../../dot_config/opencode/tools;
  opencode_skill_core_dir = ../../../dot_config/opencode/skills/core;
  opencode_skill_languages_dir = ../../../dot_config/opencode/skills/languages;
  opencode_skill_practices_dir = ../../../dot_config/opencode/skills/practices;
  opencode_skill_thinking_dir = ../../../dot_config/opencode/skills/thinking;
  opencode_skill_infrastructure_dir = ../../../dot_config/opencode/skills/infrastructure;
  opencode_skill_research_dir = ../../../dot_config/opencode/skills/research;
  opencode_skill_japanese_dir = ../../../dot_config/opencode/skills/japanese;
  opencode_skill_local_dir = ../../../dot_config/opencode/skills/local;
  opencode_skills_tools = ../../../dot_config/opencode/skills/tools;
  opencode_requirements = ../../../dot_config/opencode/requirements.txt;
  opencode_command_dir = ../../../dot_config/opencode/command;
  managedSkills = {
    core = opencode_skill_core_dir;
    languages = opencode_skill_languages_dir;
    practices = opencode_skill_practices_dir;
    thinking = opencode_skill_thinking_dir;
    infrastructure = opencode_skill_infrastructure_dir;
    research = opencode_skill_research_dir;
    japanese = opencode_skill_japanese_dir;
  };
  syncSkillCommands = builtins.concatStringsSep "\n" (
    lib.mapAttrsToList (name: src: ''
      sync_managed_file "${src}/SKILL.md" "$opencode_dir/skills/${name}/SKILL.md"
    '') managedSkills
  );
  opencode_target = "${config.xdg.configHome}/opencode/opencode.json";
  opencode_local_override = "${config.xdg.configHome}/opencode/opencode.local.json";
  opencode_local_example_target = "${config.xdg.configHome}/opencode/opencode.local.json.example";
in
{
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
  '';

  home.activation.syncOpencodeRules = lib.hm.dag.entryAfter [ "syncOpencodeConfig" ] ''
    opencode_dir="$(dirname "${opencode_target}")"
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
    }

    sync_managed_tree() {
      src_root="$1"
      dest_root="$2"

      mkdir -p "$dest_root"
      find "$src_root" -type f | while IFS= read -r src_file; do
        rel_path="''${src_file#''${src_root}/}"
        sync_managed_file "$src_file" "$dest_root/$rel_path"
      done
    }

    mkdir -p "$opencode_dir"
    mkdir -p "$opencode_dir/tools"
    mkdir -p "$opencode_dir/skills/core"
    mkdir -p "$opencode_dir/skills/languages"
    mkdir -p "$opencode_dir/skills/practices"
    mkdir -p "$opencode_dir/skills/thinking"
    mkdir -p "$opencode_dir/skills/infrastructure"
    mkdir -p "$opencode_dir/skills/research"
    mkdir -p "$opencode_dir/skills/japanese"
    mkdir -p "$opencode_dir/skills/local"
    mkdir -p "$opencode_dir/skills/tools"
    mkdir -p "$opencode_dir/command"

    sync_managed_file "${opencode_agents_template}" "$opencode_dir/AGENTS.md"
    sync_managed_file "${opencode_notifier_template}" "$opencode_dir/opencode-notifier.json"
    sync_managed_file "${opencode_package_template}" "$opencode_dir/package.json"
    sync_managed_tree "${opencode_tools_template}" "$opencode_dir/tools"

    # Native skills
    ${syncSkillCommands}

    # Tools and default local assets (non-destructive for user-managed files)
    sync_managed_tree "${opencode_skills_tools}" "$opencode_dir/skills/tools"
    cp -Rn "${opencode_skill_local_dir}/." "$opencode_dir/skills/local/"

    # Dependencies
    sync_managed_file "${opencode_requirements}" "$opencode_dir/requirements.txt"

    # Commands
    sync_managed_tree "${opencode_command_dir}" "$opencode_dir/command"
  '';
}
