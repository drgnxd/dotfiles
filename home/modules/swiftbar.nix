{ config, ... }:

let
  # The plugins are compiled from a separate repository and installed under the data home; SwiftBar
  # reads the refresh interval from the file name, so the installed binaries carry it.
  bin = "${config.xdg.dataHome}/swiftbar-plugins/bin";
in
{
  xdg.configFile = {
    "swiftbar/plugins/caffeine.5s.bin".source =
      config.lib.file.mkOutOfStoreSymlink "${bin}/caffeine.5s.bin";
    "swiftbar/plugins/attention.1m.bin".source =
      config.lib.file.mkOutOfStoreSymlink "${bin}/attention.1m.bin";
  };
}
