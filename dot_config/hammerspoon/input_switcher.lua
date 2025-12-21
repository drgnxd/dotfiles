-- ==========================================
-- Auto English Input Switching Function
-- ==========================================

local M = {}

-- English Input Source ID (Update this according to your environment)
local english_input_id = "com.apple.keylayout.ABC"

-- List of target apps
local target_apps = {
  "Alacritty",
  "Sol",
}

function M.init()
  -- Create window filter for each app
  for _, appName in ipairs(target_apps) do
    local wf = hs.window.filter.new(appName)
    
    wf:subscribe(hs.window.filter.windowFocused, function()
      if hs.keycodes.currentSourceID() ~= english_input_id then
        hs.keycodes.currentSourceID(english_input_id)
      end
    end)
  end
end

return M