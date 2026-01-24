-- ==========================================
-- Auto English Input Switching Function
-- ==========================================

local M = {}
local filters = {}

-- English Input Source ID (Update this according to your environment)
local english_input_id = "com.apple.keylayout.ABC"

-- List of target apps
local target_apps = {
  "Alacritty",
  "Sol",
}

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

function M.init()
  -- Create window filter for each app
  for index, app_name in ipairs(target_apps) do
    filters[index] = attach_filter(app_name)
  end
end

return M
