-- ==========================================
-- Keybind List Display (CheatSheet) - Fixed Version
-- ==========================================

local M = {}
local chooser = nil

-- Display symbols for modifier keys
local mod_symbols = {
    cmd = "⌘",
    alt = "⌥",
    shift = "⇧",
    ctrl = "⌃",
}

-- Function to format modifiers
local function format_mods(mods)
    if type(mods) ~= "table" then return "" end
    local order = {"ctrl", "alt", "shift", "cmd"}
    local result = ""
    for _, key in ipairs(order) do
        for _, mod in ipairs(mods) do
            if mod == key then
                result = result .. (mod_symbols[key] or key)
            end
        end
    end
    return result
end

-- Function to display list
local function show_cheatsheet()
    if not chooser then
        return
    end

    local choices = {}
    
    -- Use hs.my_hotkeys recorded in init.lua
    -- (Add guard in case hs.my_hotkeys is missing)
    local keys = hs.my_hotkeys or {}

    for i, hk in ipairs(keys) do
        local sub_text = format_mods(hk.mods) .. " " .. string.upper(hk.key)
        
        table.insert(choices, {
            text = hk.msg,       -- Description
            subText = sub_text,   -- Key (e.g., ⌃⌥ C)
            uuid = i
        })
    end

    -- Sort by key for better readability
    table.sort(choices, function(a, b) return a.subText < b.subText end)

    chooser:choices(choices)
    chooser:show()
end

function M.init()
    -- Setting to do nothing on selection
    chooser = hs.chooser.new(function(choice) end)
    chooser:placeholderText("Keybinds List")
    chooser:bgDark(true) -- Dark mode support
    
    -- Call key setting (Remove message in 3rd argument to prevent auto alert)
    hs.hotkey.bind({"ctrl", "alt"}, "/", "Show Keybind List", function()
        show_cheatsheet()
    end)
end

return M
