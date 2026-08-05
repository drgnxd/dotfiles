{ config, lib, ... }:

let
  settings = "${config.home.homeDirectory}/Library/Group Containers/group.org.sbarex.qlmarkdown/Library/Preferences/group.org.sbarex.qlmarkdown.plist";
in
{
  home.file."Library/Group Containers/group.org.sbarex.qlmarkdown/Library/Application Support/styles/terminal-font.css" =
    {
      source = ../../dot_config/qlmarkdown/terminal-font.css;
      force = true;
    };

  home.activation.configureQLMarkdownFont = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    if [ -f "${settings}" ]; then
      /usr/libexec/PlistBuddy -c 'Set :customCSS terminal-font.css' "${settings}"
      /usr/libexec/PlistBuddy -c 'Set :customCSSOverride false' "${settings}"
      /usr/bin/qlmanage -r cache >/dev/null
    fi
  '';
}
