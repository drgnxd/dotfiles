-- Language servers are resolved from PATH; project devShells provide them.
local servers = {
  bashls = { cmd = { "bash-language-server", "start" }, filetypes = { "sh", "bash" } },
  clangd = { cmd = { "clangd" }, filetypes = { "c", "cpp" } },
  dockerls = { cmd = { "docker-langserver", "--stdio" }, filetypes = { "dockerfile" } },
  lua_ls = { cmd = { "lua-language-server" }, filetypes = { "lua" } },
  marksman = { cmd = { "marksman", "server" }, filetypes = { "markdown" } },
  nixd = {
    cmd = { "nixd" },
    filetypes = { "nix" },
    settings = {
      nixd = {
        formatting = { command = { "nixfmt" } },
        -- These expressions evaluate the local flake; override per project if needed.
        options = {
          nixos = { expr = '(builtins.getFlake (toString ./.)).darwinConfigurations.darwin.options' },
          ["home-manager"] = {
            expr = '(builtins.getFlake (toString ./.)).homeConfigurations."user@linux".options',
          },
        },
      },
    },
  },
  nushell = { cmd = { "nu", "--lsp" }, filetypes = { "nu" } },
  pyright = { cmd = { "pyright-langserver", "--stdio" }, filetypes = { "python" } },
  r_language_server = {
    cmd = { "R", "--slave", "-e", "languageserver::run()" },
    filetypes = { "r", "rmd" },
  },
  ruff = { cmd = { "ruff", "server" }, filetypes = { "python" } },
  rust_analyzer = { cmd = { "rust-analyzer" }, filetypes = { "rust" } },
  steel = { cmd = { "steel-language-server" }, filetypes = { "scheme" } },
  taplo = { cmd = { "taplo", "lsp", "stdio" }, filetypes = { "toml" } },
  texlab = { cmd = { "texlab" }, filetypes = { "tex", "plaintex", "bib" } },
  tinymist = { cmd = { "tinymist" }, filetypes = { "typst" } },
  yamlls = { cmd = { "yaml-language-server", "--stdio" }, filetypes = { "yaml" } },
}

for name, config in pairs(servers) do
  config.root_markers = config.root_markers or { ".git" }
  vim.lsp.config(name, config)
  vim.lsp.enable(name)
end

vim.api.nvim_create_autocmd("LspAttach", {
  callback = function(args)
    local client = vim.lsp.get_client_by_id(args.data.client_id)
    if client and client:supports_method("textDocument/completion") then
      vim.lsp.completion.enable(true, client.id, args.buf, { autotrigger = true })
    end
    if client and client:supports_method("textDocument/formatting")
      and vim.tbl_contains({ "nixd", "dockerls", "bashls", "r_language_server" }, client.name) then
      local group = vim.api.nvim_create_augroup("lsp_format_" .. args.buf, { clear = true })
      vim.api.nvim_create_autocmd("BufWritePre", {
        group = group,
        buffer = args.buf,
        callback = function()
          vim.lsp.buf.format({ bufnr = args.buf, name = client.name })
        end,
      })
    end
  end,
})
