{ config, lib, ... }:

let
  settings = "${config.home.homeDirectory}/Library/Group Containers/group.org.sbarex.qlmarkdown/Library/Preferences/group.org.sbarex.qlmarkdown.plist";
  solarized_dark = import ../themes/solarized-dark.nix;
in
{
  home.file."Library/Group Containers/group.org.sbarex.qlmarkdown/Library/Application Support/styles/terminal-font.css" =
    {
      force = true;
      text = ''
        /* Keep Finder Quick Look typography and colors consistent with Alacritty. */
        :root {
          --code-font: "PlemolJP Console NF", monospace;
          --textPrimary: ${solarized_dark.base0};
          --background: ${solarized_dark.base03};
          --body-border-color: ${solarized_dark.base02};
          --link: ${solarized_dark.blue};
          --link-highlight: ${solarized_dark.base02};
          --code-background: ${solarized_dark.base02};
          --hr-background: ${solarized_dark.base01};
          --thead-background: ${solarized_dark.base02};
          --thead-border: ${solarized_dark.base01};
          --tr-border: ${solarized_dark.base01};
          --tr-alt-background: ${solarized_dark.base02};
          --kbd-background: ${solarized_dark.base02};
          --kbd-color: ${solarized_dark.base1};
          --kbd-border: ${solarized_dark.base01};
          --blockquote-color: ${solarized_dark.base1};
          --blockquote-border: ${solarized_dark.cyan};
          --heading-color: ${solarized_dark.base1};
          --header-bottom-border: ${solarized_dark.base01};
          --h6-color: ${solarized_dark.base0};
          --frame-border: ${solarized_dark.base01};
          --frame-color: ${solarized_dark.base0};
          --mention-color: ${solarized_dark.base0};
          --keyword-color: ${solarized_dark.base01};
          --hl_Background: ${solarized_dark.base02};
          --hl_Number: ${solarized_dark.blue};
          --hl_Escape: ${solarized_dark.cyan};
          --hl_String: ${solarized_dark.cyan};
          --hl_String_Pre_Processor: ${solarized_dark.orange};
          --hl_Block_Comment: ${solarized_dark.base01};
          --hl_Line_Comment: ${solarized_dark.base01};
          --hl_Pre_Processor: ${solarized_dark.red};
          --hl_Line_Number: ${solarized_dark.base00};
          --hl_Operator: ${solarized_dark.cyan};
          --hl_Interpolation: ${solarized_dark.violet};
          --hl_Keyword-1: ${solarized_dark.green};
          --hl_Keyword-2: ${solarized_dark.yellow};
          --hl_Keyword-3: ${solarized_dark.base0};
          --hl_Keyword-4: ${solarized_dark.violet};
          --hl_Keyword-5: ${solarized_dark.orange};
          --hl_Keyword-6: ${solarized_dark.red};
        }

        html {
          font-family: "PlemolJP Console NF", monospace;
        }

        /* Preserve MathJax's metric-aware TeX glyphs; style only text and fallback glyphs. */
        mjx-mtext,
        mjx-merror,
        mjx-unknown {
          font-family: "IBM Plex Math", "PlemolJP Console NF", monospace !important;
        }
      '';
    };

  home.activation.configureQLMarkdownFont = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    if [ -f "${settings}" ]; then
      /usr/libexec/PlistBuddy -c 'Set :customCSS terminal-font.css' "${settings}"
      /usr/libexec/PlistBuddy -c 'Set :customCSSOverride false' "${settings}"
      /usr/libexec/PlistBuddy -c 'Set :footnotesOption true' "${settings}"
      /usr/libexec/PlistBuddy -c 'Set :strikethroughExtension 1' "${settings}"
      /usr/libexec/PlistBuddy -c 'Set :subExtension false' "${settings}"
      /usr/libexec/PlistBuddy -c 'Set :supExtension false' "${settings}"
      /usr/bin/qlmanage -r cache >/dev/null
    fi
  '';
}
