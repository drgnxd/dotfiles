-- ==========================================
-- Window Management (Rectangle Alternative)
-- ==========================================

local M = {}

-- Set animation duration to 0 (instant move)
hs.window.animationDuration = 0

local window_bindings = {
  {key = "Left", desc = "Move Window to Left Half", rect = {0, 0, 0.5, 1}},
  {key = "Right", desc = "Move Window to Right Half", rect = {0.5, 0, 0.5, 1}},
  {key = "Return", desc = "Maximize Window", rect = {0, 0, 1, 1}},
  {key = "Up", desc = "Move Window to Top Half", rect = {0, 0, 1, 0.5}},
  {key = "Down", desc = "Move Window to Bottom Half", rect = {0, 0.5, 1, 0.5}},
  {key = "U", desc = "Move Window to Top-Left 1/4", rect = {0, 0, 0.5, 0.5}},
  {key = "I", desc = "Move Window to Top-Right 1/4", rect = {0.5, 0, 0.5, 0.5}},
  {key = "J", desc = "Move Window to Bottom-Left 1/4", rect = {0, 0.5, 0.5, 0.5}},
  {key = "K", desc = "Move Window to Bottom-Right 1/4", rect = {0.5, 0.5, 0.5, 0.5}},
  {key = "C", desc = "Move Window to Center (80%)", rect = {0.1, 0.1, 0.8, 0.8}},
}

-- Function to calculate position and move window
-- 
-- Window Position Calculation:
-- x, y, w, h are fractional values (0.0-1.0) relative to screen dimensions
-- 
-- Examples (1920x1080 screen):
--   Left Half:   x=0,    y=0,   w=0.5, h=1   → (0, 0, 960, 1080)
--   Right Half:  x=0.5,  y=0,   w=0.5, h=1   → (960, 0, 960, 1080)
--   Top Half:    x=0,    y=0,   w=1,   h=0.5 → (0, 0, 1920, 540)
--   Bottom Half: x=0,    y=0.5, w=1,   h=0.5 → (0, 540, 1920, 540)
--   Centered 80%: x=0.1, y=0.1, w=0.8, h=0.8 → (192, 108, 1536, 864)
--   Top Left:    x=0,    y=0,   w=0.5, h=0.5 → (0, 0, 960, 540)
local function move_window(x, y, w, h)
  -- Validate parameters are in range [0, 1]
  if x < 0 or x > 1 or y < 0 or y > 1 or w < 0 or w > 1 or h < 0 or h > 1 then
    hs.alert.show("Window position parameters must be between 0 and 1")
    return
  end
  
  -- Validate position + size doesn't exceed screen bounds
  if x + w > 1 or y + h > 1 then
    hs.alert.show("Window position + size exceeds screen bounds")
    return
  end
  
  local win = hs.window.focusedWindow()
  if not win then
    hs.alert.show("No focused window")
    return
  end

  local f = win:frame()
  local screen = win:screen()
  local max = screen:frame()

  f.x = max.x + (max.w * x)  -- Absolute X = screen.x + (screen.width * fraction)
  f.y = max.y + (max.h * y)  -- Absolute Y = screen.y + (screen.height * fraction)
  f.w = max.w * w            -- Width = screen.width * fraction
  f.h = max.h * h            -- Height = screen.height * fraction
  win:setFrame(f)
end

function M.init()
  -- Modifier keys (Ctrl + Alt)
  -- Mimics Rectangle defaults, change to {"cmd", "alt"} etc. if needed
  local mash = {"ctrl", "alt"}
  for _, binding in ipairs(window_bindings) do
    hs.hotkey.bind(mash, binding.key, binding.desc, function()
      local x, y, w, h = table.unpack(binding.rect)
      move_window(x, y, w, h)
    end)
  end
end

return M
