{ config, lib, ... }:

let
  opencode_template = ../../../dot_config/opencode/opencode.json;
  opencode_dcp_template = ../../../dot_config/opencode/dcp.json;
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
  opencode_skills_tools = ../../../dot_config/opencode/skills/tools;
  opencode_requirements = ../../../dot_config/opencode/requirements.txt;
  opencode_command_dir = ../../../dot_config/opencode/command;
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

    cp -f "${opencode_agents_template}" "$opencode_dir/AGENTS.md"
    cp -f "${opencode_dcp_template}" "$opencode_dir/dcp.json"
    cp -f "${opencode_notifier_template}" "$opencode_dir/opencode-notifier.json"
    cp -f "${opencode_package_template}" "$opencode_dir/package.json"
    cp -Rf "${opencode_tools_template}/." "$opencode_dir/tools/"

    # Native skills
    cp -f "${opencode_skill_core_dir}/SKILL.md" "$opencode_dir/skills/core/SKILL.md"
    cp -f "${opencode_skill_languages_dir}/SKILL.md" "$opencode_dir/skills/languages/SKILL.md"
    cp -f "${opencode_skill_practices_dir}/SKILL.md" "$opencode_dir/skills/practices/SKILL.md"
    cp -f "${opencode_skill_thinking_dir}/SKILL.md" "$opencode_dir/skills/thinking/SKILL.md"
    cp -f "${opencode_skill_infrastructure_dir}/SKILL.md" "$opencode_dir/skills/infrastructure/SKILL.md"
    cp -f "${opencode_skill_research_dir}/SKILL.md" "$opencode_dir/skills/research/SKILL.md"
    cp -f "${opencode_skill_japanese_dir}/SKILL.md" "$opencode_dir/skills/japanese/SKILL.md"

    # Tools (exclude skills/local/ — user-managed)
    cp -Rf "${opencode_skills_tools}/." "$opencode_dir/skills/tools/"

    # Dependencies
    cp -f "${opencode_requirements}" "$opencode_dir/requirements.txt"

    # Commands
    cp -Rf "${opencode_command_dir}/." "$opencode_dir/command/"
  '';
}
