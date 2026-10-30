{
  pkgs,
  user,
  hostname,
  linuxHostname,
  ...
}:

let
  lsp_lua = builtins.readFile ../../xdg/config/nvim/lua/lsp.lua;
  lsp_lua_substituted =
    builtins.replaceStrings
      [ "darwinConfigurations.darwin" ''homeConfigurations."user@linux"'' ]
      [ "darwinConfigurations.${hostname}" ''homeConfigurations."${user}@${linuxHostname}"'' ]
      lsp_lua;
in
{
  programs.neovim = {
    enable = true;
    withRuby = false;
    withPython3 = false;
    withNodeJs = false;
    plugins = with pkgs.vimPlugins; [
      (nvim-treesitter.withPlugins (_: nvim-treesitter.allGrammars))
    ];
    initLua = builtins.readFile ../../xdg/config/nvim/init.lua;
  };

  xdg.configFile = {
    "nvim/colors/solarized-dark.lua".source = ../../xdg/config/nvim/colors/solarized-dark.lua;
    "nvim/lua/lsp.lua".text = lsp_lua_substituted;
    "nvim/lua/keymaps.lua".source = ../../xdg/config/nvim/lua/keymaps.lua;
  };
}
