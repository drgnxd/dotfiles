# Mirrors OpenCode's managed skills into Claude Code's personal skills
# directory (<CLAUDE_CONFIG_DIR>/skills) as Nix store symlinks, so any skill
# added under dot_config/opencode/skills is automatically readable by both
# tools without touching this file. Claude Code does not discover
# .opencode/skills on its own, but it does follow a <skill-name> entry under
# its skills directory that is itself a symlink to a directory elsewhere on
# disk. Kept separate from ./opencode.nix to preserve that file's
# OpenCode-only asset contract.
{ lib, ... }:

let
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
in
{
  xdg.dataFile = lib.mapAttrs' (
    name: src: lib.nameValuePair "claude/skills/${name}" { source = src; }
  ) managedSkills;
}
