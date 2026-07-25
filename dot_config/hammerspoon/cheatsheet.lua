local M = {}
local chooser = nil

local mod_symbols = {
    cmd = "⌘",
    alt = "⌥",
    shift = "⇧",
    ctrl = "⌃",
}

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

local function show_cheatsheet()
    if not chooser then
        return
    end

    local choices = {}
    local keys = hs.my_hotkeys or {}

    for i, hk in ipairs(keys) do
        local sub_text = format_mods(hk.mods) .. " " .. string.upper(hk.key)
        table.insert(choices, {
            text = hk.msg,
            subText = sub_text,
            uuid = i
        })
    end

    table.sort(choices, function(a, b) return a.subText < b.subText end)

    chooser:choices(choices)
    chooser:show()
end

function M.init()
    chooser = hs.chooser.new(function(choice) end)
    chooser:placeholderText("Keybinds List")
    chooser:bgDark(true)

    hs.hotkey.bind({"ctrl", "alt"}, "/", "Show Keybind List", function()
        show_cheatsheet()
    end)
end

return M
