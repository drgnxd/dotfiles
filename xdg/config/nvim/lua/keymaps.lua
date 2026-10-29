-- Readline-style insert-mode keys carried over from the Helix configuration.
local map = vim.keymap.set

map("i", "<C-f>", "<Right>")
map("i", "<C-b>", "<Left>")
map("i", "<C-n>", "<Down>")
map("i", "<C-p>", "<Up>")
map("i", "<C-a>", "<Home>")
map("i", "<C-e>", "<End>")
map("i", "<M-f>", "<C-o>e<Right>")
map("i", "<M-b>", "<C-o>b")
map("i", "<C-h>", "<BS>")
map("i", "<C-d>", "<Del>")
map("i", "<M-d>", "<C-o>dw")
map("i", "<C-k>", "<C-o>D")
map("i", "<C-u>", "<C-g>u<C-o>d0")
map("i", "<C-y>", "<C-r>+")
