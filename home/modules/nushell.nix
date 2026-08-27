{ lib, pkgs, ... }:

let
  nushellSrc = ../../dot_config/nushell;

  # config.nu + env.nu + autoload/* + modules/*, keyed under `prefix`.
  # `extraAttrs` is merged into every entry (used to pass `force = true`).
  mkTree =
    prefix: extraAttrs:
    let
      mkEntry = src: { source = src; } // extraAttrs;
      mkSubdir =
        subdir:
        let
          srcDir = nushellSrc + "/${subdir}";
        in
        lib.mapAttrs' (
          name: _type: lib.nameValuePair "${prefix}/${subdir}/${name}" (mkEntry (srcDir + "/${name}"))
        ) (lib.filterAttrs (_name: type: type == "regular") (builtins.readDir srcDir));
    in
    {
      "${prefix}/config.nu" = mkEntry (nushellSrc + "/config.nu");
      "${prefix}/env.nu" = mkEntry (nushellSrc + "/env.nu");
    }
    // mkSubdir "autoload"
    // mkSubdir "modules";
in
{
  xdg.configFile = mkTree "nushell" { };

  # nushell resolves its config directory to ~/Library/Application Support/
  # nushell on macOS whenever XDG_CONFIG_HOME is unset. It normally is set
  # (hosts/darwin/default.nix environment.variables + the setenv-user-env
  # launchd agent), but the login shell is nushell itself and login-alacritty
  # autostarts, so a shell that starts before the launchd session env is
  # seeded early in a post-boot login would otherwise fall back to nushell's
  # own empty default stubs there. Mirror the managed tree to that path so
  # that degraded case gets the real config. With XDG_CONFIG_HOME set these
  # files are never read.
  #
  # `force = true`: the only thing that ever lands at this path is nushell's
  # own regenerated stub (the managed login config is the ~/.config copy),
  # so overwrite it without a `.before-nix` backup -- a backup here is pure
  # litter and a later mirror toggle would abort activation on the stale
  # backup. The mirrored files source everything else (modules/, generated/,
  # local.nu) by absolute ~/.config/nushell path, so that tree stays the
  # single source those references resolve against.
  home.file = lib.mkIf pkgs.stdenv.isDarwin (
    mkTree "Library/Application Support/nushell" { force = true; }
  );
}
