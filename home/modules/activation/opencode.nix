{ config, lib, ... }:

let
  opencode_template = ../../../dot_config/opencode/opencode.json;
  opencode_dcp_template = ../../../dot_config/opencode/dcp.json;
  opencode_local_example = ../../../dot_config/opencode/opencode.local.json.example;
  opencode_agents_template = ../../../dot_config/opencode/AGENTS.md;
  opencode_notifier_template = ../../../dot_config/opencode/opencode-notifier.json;
  opencode_package_template = ../../../dot_config/opencode/package.json;
  opencode_tools_template = ../../../dot_config/opencode/tools;
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
      /bin/cp -f "${opencode_local_example}" "$opencode_local_example_target"
    fi
  '';

  home.activation.syncOpencodeConfig = lib.hm.dag.entryAfter [ "ensureOpencodeLocalConfig" ] ''
    opencode_target="${opencode_target}"
    opencode_local_override="${opencode_local_override}"
    opencode_dir="$(dirname "$opencode_target")"
    mkdir -p "$opencode_dir"
    if [ -s "$opencode_local_override" ]; then
      /bin/cp -f "$opencode_local_override" "$opencode_target"
    else
      /bin/cp -f "${opencode_template}" "$opencode_target"
    fi
  '';

  home.activation.syncOpencodeRules = lib.hm.dag.entryAfter [ "syncOpencodeConfig" ] ''
    opencode_dir="$(dirname "${opencode_target}")"
    mkdir -p "$opencode_dir"
    mkdir -p "$opencode_dir/tools"

    /bin/cp -f "${opencode_agents_template}" "$opencode_dir/AGENTS.md"
    /bin/cp -f "${opencode_dcp_template}" "$opencode_dir/dcp.json"
    /bin/cp -f "${opencode_notifier_template}" "$opencode_dir/opencode-notifier.json"
    /bin/cp -f "${opencode_package_template}" "$opencode_dir/package.json"
    /bin/cp -Rf "${opencode_tools_template}/." "$opencode_dir/tools/"
  '';
}
