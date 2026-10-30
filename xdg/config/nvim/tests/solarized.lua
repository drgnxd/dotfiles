local function check()
  for group, foreground in pairs({
    Normal = 0x839496,
    NormalNC = 0x839496,
    SignColumn = 0x839496,
    Identifier = 0x839496,
    Statement = 0x859900,
    Define = 0xcb4b16,
    SpecialChar = 0xcb4b16,
    SpecialComment = 0x93a1a1,
    CursorLineNr = 0xb58900,
    TSOperator = 0x839496,
    TSPunctBracket = 0x839496,
    TSField = 0x839496,
    NvimTreeFolderIcon = 0x268bd2,
    ["@variable"] = 0x839496,
    ["@punctuation"] = 0x839496,
  }) do
    local hl = vim.api.nvim_get_hl(0, { name = group, link = false })
    assert(hl.fg == foreground, group .. " foreground: " .. vim.inspect(hl))
    if group == "Normal" or group == "NormalNC" or group == "SignColumn" then
      assert(hl.bg == nil, group .. " must be transparent")
    end
  end
end

check()
vim.wait(200)
check()
vim.cmd.new()
vim.bo.filetype = "lua"
vim.api.nvim_buf_set_lines(0, 0, -1, false, { "local answer = 42", "print(answer)" })
vim.api.nvim_buf_set_text(0, 0, 6, 0, 12, { "result" })
check()
vim.cmd.colorscheme("solarized")
vim.wait(200)
check()
print("Solarized dark highlight regression passed")
