{
  config,
  lib,
  pkgs,
  ...
}:

let
  markql_repo = "${config.home.homeDirectory}/repos/markql";
  markql_app = "${config.home.homeDirectory}/Applications/MarkQL.app";
  markql_state_dir = "${config.xdg.stateHome}/markql";
  markql_stamp = "${markql_state_dir}/source-revision";
  bash = "${pkgs.bash}/bin/bash";
  cat = "${pkgs.coreutils}/bin/cat";
  git = "${pkgs.git}/bin/git";
  mkdir = "${pkgs.coreutils}/bin/mkdir";
  mv = "${pkgs.coreutils}/bin/mv";
in
{
  config = lib.mkIf pkgs.stdenv.isDarwin {
    home.activation.installMarkQL = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      markql_repo="${markql_repo}"
      markql_app="${markql_app}"
      markql_state_dir="${markql_state_dir}"
      markql_stamp="${markql_stamp}"

      if [ -d "$markql_repo" ]; then
        if markql_revision="$(${git} -C "$markql_repo" rev-parse HEAD 2>/dev/null)"; then
          markql_stamp_revision=""
          if [ -f "$markql_stamp" ]; then
            markql_stamp_revision="$(${cat} "$markql_stamp" 2>/dev/null || true)"
          fi

          if [ ! -d "$markql_app" ] || [ "$markql_stamp_revision" != "$markql_revision" ]; then
            if [ -n "''${DRY_RUN_CMD:-}" ]; then
              echo "Would build and install MarkQL from $markql_repo"
            elif ${bash} "$markql_repo/build.sh" && ${bash} "$markql_repo/install.sh" && [ -d "$markql_app" ]; then
              ${mkdir} -p "$markql_state_dir"
              markql_stamp_tmp="$markql_stamp.$$"
              printf '%s\n' "$markql_revision" >"$markql_stamp_tmp"
              ${mv} -f "$markql_stamp_tmp" "$markql_stamp"
            else
              echo "warning: MarkQL build/install failed; will retry on the next activation" >&2
            fi
          fi
        else
          echo "warning: unable to read the MarkQL git revision; skipping its build" >&2
        fi
      else
        echo "warning: MarkQL repository not found at $markql_repo; skipping its build" >&2
      fi

      if [ -d "$markql_app" ]; then
        /usr/bin/pluginkit -a "$markql_app/Contents/PlugIns/MarkQLPreview.appex" || true
        /usr/bin/pluginkit -e use -i com.drgnxd.MarkQL.Preview
        /usr/bin/pluginkit -e ignore -i org.sbarex.QLMarkdown.QLExtension || true
        /usr/bin/qlmanage -r >/dev/null 2>&1 || true
        /usr/bin/qlmanage -r cache >/dev/null 2>&1 || true
      else
        echo "warning: MarkQL.app is not installed; Quick Look preference was not changed" >&2
      fi
    '';
  };
}
