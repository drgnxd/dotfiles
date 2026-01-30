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

-- Module registry for organized initialization
local modules = {
  {name = "reload", required = true},
  {name = "input_switcher", required = false},
  {name = "caffeine", required = false},
  {name = "window", required = true},
  {name = "cheatsheet", required = false},
  {name = "browser_control", required = false},
}

-- Load and initialize all modules
for _, mod_info in ipairs(modules) do
  local ok, module = pcall(require, mod_info.name)
  if ok and module and module.init then
    module.init()
  elseif mod_info.required then
    hs.alert.show("Failed to load required module: " .. mod_info.name)
  end
end

-- Hyper key (Cmd+Alt+Ctrl+Shift) for conflict-free bindings
local hyper = {"cmd", "alt", "ctrl", "shift"}

-- Example: quick launcher using Hyper
hs.hotkey.bind(hyper, "A", "Launch Alacritty", function()
    hs.application.launchOrFocus("Alacritty")
end)
