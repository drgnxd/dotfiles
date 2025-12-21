-- ==========================================
-- Hammerspoon Configuration File
-- ==========================================

-- Prepare table to store shortcut information
hs.my_hotkeys = {}

-- Save existing bind function
local original_bind = hs.hotkey.bind

-- Overwrite (wrap) bind function to record information upon registration
hs.hotkey.bind = function(mods, key, param1, ...)
    local message = "No Description"
    
    -- If the 3rd argument (param1) is a string, use it as the description
    if type(param1) == "string" then
        message = param1
    end

    -- Save to recording table
    table.insert(hs.my_hotkeys, {
        mods = mods,
        key = key,
        msg = message
    })

    -- Execute original bind function
    return original_bind(mods, key, param1, ...)
end

-- Load modules
local reload = require("reload")
local input_switcher = require("input_switcher")
local caffeine = require("caffeine")
local window = require("window")
local cheatsheet = require("cheatsheet")
local browser_control = require("browser_control")

-- Initialize modules
reload.init()
input_switcher.init()
caffeine.init()
window.init()
cheatsheet.init()
browser_control.init()