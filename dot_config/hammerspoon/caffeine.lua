-- ==========================================
-- Prevent Sleep Function (Caffeine)
-- ==========================================

local M = {}

local caffeine = nil

-- Function to toggle icon display
local function set_caffeine_display(state)
  if state then
    caffeine:setTitle("☕️") -- ON: Do not sleep
  else
    caffeine:setTitle("💤") -- OFF: Sleep normally
  end
end

-- Action on click
local function caffeine_clicked()
  -- Toggle setting to prevent displayIdle (display sleep)
  set_caffeine_display(hs.caffeinate.toggle("displayIdle"))
end

function M.init()
  caffeine = hs.menubar.new()
  
  if caffeine then
    caffeine:setClickCallback(caffeine_clicked)
    -- Get and display state on startup
    set_caffeine_display(hs.caffeinate.get("displayIdle"))
  end
end

return M