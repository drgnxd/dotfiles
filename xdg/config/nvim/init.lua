vim.g.mapleader = " "

local o = vim.opt
o.termguicolors = true
o.background = "dark"
o.number = true
o.list = true
o.listchars = { space = "·", tab = "→ " }
o.signcolumn = "yes"
o.completeopt = { "menuone", "noselect", "popup" }
o.autocomplete = true
o.wrap = false
o.expandtab = true
o.tabstop = 2
o.shiftwidth = 2
o.virtualedit = "onemore"

vim.cmd.colorscheme("solarized")
-- Match the transparent terminal background used by the Helix theme.
for _, group in ipairs({ "Normal", "NormalNC", "SignColumn", "EndOfBuffer" }) do
  vim.api.nvim_set_hl(0, group, { bg = "NONE" })
end

vim.diagnostic.config({ virtual_text = { current_line = true }, severity_sort = true })

vim.api.nvim_create_autocmd("FileType", {
  callback = function(args)
    pcall(vim.treesitter.start, args.buf)
  end,
})

vim.api.nvim_create_autocmd("FileType", {
  pattern = "markdown",
  callback = function()
    vim.opt_local.wrap = true
    vim.opt_local.linebreak = true
  end,
})

vim.api.nvim_create_autocmd("TextYankPost", {
  callback = function()
    vim.hl.on_yank()
  end,
})

require("keymaps")
require("lsp")
