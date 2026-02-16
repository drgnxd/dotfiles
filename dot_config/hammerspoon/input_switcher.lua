-- ==========================================
-- Auto English Input Switching Function
-- ==========================================

local M = {}
local filters = {}
local app_watcher = nil
local sol_hotkey_tap = nil

-- English Input Source ID (Update this according to your environment)
local english_input_id = "com.apple.keylayout.ABC"

-- Apps that should switch to English when one of their windows is focused
local window_focus_apps = {
  "Alacritty",
  "Sol",
}

-- Apps that should switch to English when activated
local activation_apps = {
  Sol = true,
}

local key_down_event = hs.eventtap.event.types.keyDown
local space_key_code = hs.keycodes.map.space

local function switch_to_english()
  if hs.keycodes.currentSourceID() ~= english_input_id then
    hs.keycodes.currentSourceID(english_input_id)
  end
end

local function attach_filter(app_name)
  local wf = hs.window.filter.new(app_name)
  wf:subscribe(hs.window.filter.windowFocused, switch_to_english)
  return wf
end

local function watch_app_activation()
  app_watcher = hs.application.watcher.new(function(app_name, event_type)
    if event_type == hs.application.watcher.activated and activation_apps[app_name] then
      switch_to_english()
    end
  end)
  app_watcher:start()
end

local function watch_sol_hotkey()
  if not space_key_code then
    return
  end

  -- Sol is triggered with Cmd+Space. Switch input source before typing.
  sol_hotkey_tap = hs.eventtap.new({ key_down_event }, function(event)
    if event:getKeyCode() ~= space_key_code then
      return false
    end

    local flags = event:getFlags()
    if flags.cmd and not flags.alt and not flags.ctrl and not flags.shift and not flags.fn then
      switch_to_english()
    end

    return false
  end)

  sol_hotkey_tap:start()
end

function M.init()
  -- Create window filter for each app
  for index, app_name in ipairs(window_focus_apps) do
    filters[index] = attach_filter(app_name)
  end

  watch_app_activation()
  watch_sol_hotkey()
end

return M
