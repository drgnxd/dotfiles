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

-- The plugin uses several light-theme colors even when 'background' is dark.
local highlights = {
  Normal = { fg = "#839496", bg = "NONE" },
  NormalNC = { link = "Normal" },
  SignColumn = { link = "Normal" },
  EndOfBuffer = { fg = "#586e75", bg = "NONE" },
  Identifier = { fg = "#839496" },
  Statement = { fg = "#859900" },
  Define = { fg = "#cb4b16" },
  SpecialChar = { fg = "#cb4b16" },
  SpecialComment = { fg = "#93a1a1" },
  Ignore = { fg = "#586e75" },
  NonText = { fg = "#586e75" },
  Whitespace = { fg = "#586e75" },
  Conceal = { fg = "#93a1a1" },
  Folded = { fg = "#93a1a1", bg = "#073642" },
  CursorLineNr = { fg = "#b58900", bold = true },
  ModeMsg = { fg = "#839496" },
  MoreMsg = { fg = "#859900" },
  NormalFloat = { fg = "#839496", bg = "#073642" },
  Pmenu = { fg = "#839496", bg = "#073642" },
  PmenuSel = { fg = "#002b36", bg = "#839496" },
  Visual = { bg = "#073642" },
  VisualNOS = { bg = "#073642" },
  Search = { fg = "#002b36", bg = "#b58900" },
  IncSearch = { fg = "#002b36", bg = "#cb4b16" },
  ColorColumn = { bg = "#073642" },
  CursorColumn = { bg = "#073642" },
  VertSplit = { fg = "#586e75" },
  TabLineSel = { fg = "#002b36", bg = "#839496", bold = true },
  NormalMode = { fg = "#002b36", bg = "#839496" },
  CommandMode = { fg = "#002b36", bg = "#2aa198" },
  DashboardHeader = { fg = "#268bd2" },
  DashboardShortCut = { fg = "#2aa198" },
  DashboardCenter = { fg = "#839496" },
  TSField = { fg = "#839496" },
  TSOperator = { fg = "#839496" },
  TSPunctDelimiter = { fg = "#839496" },
  TSPunctBracket = { fg = "#839496" },
  TSPunctSpecial = { fg = "#839496" },
  TSStringEscape = { fg = "#cb4b16" },
  NvimTreeEmptyFolderName = { fg = "#93a1a1" },
  NvimTreeFolderIcon = { fg = "#268bd2" },
  NvimTreeIndentMarker = { fg = "#586e75" },
  WhichKey = { fg = "#2aa198", bold = true },
  LspSagaSignatureHelpBorder = { fg = "#2aa198" },
  BufferLineIndicatorSelected = { fg = "#2aa198" },
  Sneak = { fg = "#002b36", bg = "#b58900" },
  IndentBlanklineContextChar = { fg = "#586e75" },
  ["@variable"] = { fg = "#839496" },
  ["@variable.member"] = { fg = "#839496" },
  ["@operator"] = { fg = "#839496" },
  ["@punctuation"] = { fg = "#839496" },
}
vim.api.nvim_create_autocmd("ColorScheme", {
  pattern = "solarized",
  callback = function()
    for group, highlight in pairs(highlights) do
      vim.api.nvim_set_hl(0, group, highlight)
    end
    -- The plugin applies its remaining groups asynchronously after ColorScheme.
    local util = require("solarized.util")
    local apply = util.highlight_table_members
    util.highlight_table_members = function(groups)
      local filtered = {}
      for group, highlight in pairs(groups) do
        if not highlights[group] then
          filtered[group] = highlight
        end
      end
      apply(filtered)
    end
  end,
})
vim.cmd.colorscheme("solarized")

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
