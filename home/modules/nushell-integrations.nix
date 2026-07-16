# Phase 3: Nushell integration init scripts via Nix derivations (Plan B)
#
# Tools classified as Plan B generate deterministic init output with no
# host-specific content, so their init scripts can be built at nix-build
# time and deployed as read-only config files.  This eliminates the
# runtime SHA-256 hash-sync cost (~350 ms) for these three tools.
#
# Carapace completion is configured directly in config.nu and does not need
# generated init output.
{ config, pkgs, ... }:

let
  mkNushellInit =
    name: pkg: cmd:
    pkgs.runCommand "${name}-nushell-init"
      {
        nativeBuildInputs = [ pkg ];
      }
      ''
        ${builtins.concatStringsSep " " cmd} > $out
      '';

  # atuin init writes under $HOME while generating its script, so use a
  # temporary writable HOME here.  Keep this separate from mkNushellInit to
  # make the workaround explicit and avoid accidental removal later.
  mkNushellInitHome =
    name: pkg: cmd:
    pkgs.runCommand "${name}-nushell-init"
      {
        nativeBuildInputs = [ pkg ];
      }
      ''
        export HOME="$TMPDIR"
        ${builtins.concatStringsSep " " cmd} > $out
      '';

  # Nushell >= 0.86 replaces completed prompts with transient output, reducing
  # scrollback to a character plus the command.
  starshipInit = pkgs.runCommand "starship-nushell-init" { } ''
    ${config.programs.starship.package}/bin/starship init nu > $out
    cat >> $out <<'EOF'
    $env.TRANSIENT_PROMPT_COMMAND = {|| ^${config.programs.starship.package}/bin/starship module character }
    $env.TRANSIENT_PROMPT_COMMAND_RIGHT = {|| "" }
    EOF
  '';

  zoxideInit = mkNushellInit "zoxide" config.programs.zoxide.package [
    "zoxide"
    "init"
    "nushell"
  ];

  atuinInit = mkNushellInitHome "atuin" config.programs.atuin.package [
    "atuin"
    "init"
    "nu"
  ];
in
{
  xdg.configFile = {
    "nushell/generated/starship.nu".source = starshipInit;
    "nushell/generated/zoxide.nu".source = zoxideInit;
    "nushell/generated/atuin.nu".source = atuinInit;
  };
}
