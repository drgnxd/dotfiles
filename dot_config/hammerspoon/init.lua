hs.my_hotkeys = {}

local original_bind = hs.hotkey.bind

hs.hotkey.bind = function(mods, key, param1, ...)
    local message = "No Description"
    if type(param1) == "string" then
        message = param1
    end

    table.insert(hs.my_hotkeys, {
        mods = mods,
        key = key,
        msg = message
    })

    return original_bind(mods, key, param1, ...)
end

local modules = {
  {name = "reload", required = true},
  {name = "input_switcher", required = false},
  {name = "caffeine", required = false},
  {name = "window", required = true},
  {name = "cheatsheet", required = false},
  {name = "browser_control", required = false},
}

for _, mod_info in ipairs(modules) do
  local ok, module = pcall(require, mod_info.name)
  if ok and module and module.init then
    module.init()
  elseif mod_info.required then
    hs.alert.show("Failed to load required module: " .. mod_info.name)
  elseif not mod_info.required then
    print("Optional module not loaded: " .. mod_info.name)
  end
end

local hyper = {"cmd", "alt", "ctrl", "shift"}

hs.hotkey.bind(hyper, "A", "Launch Alacritty", function()
    hs.application.launchOrFocus("Alacritty")
end)
