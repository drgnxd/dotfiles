-- ==========================================
-- Window Management (Rectangle Alternative)
-- ==========================================

local M = {}

-- Set animation duration to 0 (instant move)
hs.window.animationDuration = 0

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
  if not win then return end

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

  -- Left Half (Left Arrow)
  hs.hotkey.bind(mash, "Left", "Move Window to Left Half", function()
    move_window(0, 0, 0.5, 1)
  end)

  -- Right Half (Right Arrow)
  hs.hotkey.bind(mash, "Right", "Move Window to Right Half", function()
    move_window(0.5, 0, 0.5, 1)
  end)

  -- Maximize (Enter)
  hs.hotkey.bind(mash, "Return", "Maximize Window", function()
    move_window(0, 0, 1, 1)
  end)

  -- Top Half (Up Arrow)
  hs.hotkey.bind(mash, "Up", "Move Window to Top Half", function()
    move_window(0, 0, 1, 0.5)
  end)

  -- Bottom Half (Down Arrow)
  hs.hotkey.bind(mash, "Down", "Move Window to Bottom Half", function()
    move_window(0, 0.5, 1, 0.5)
  end)

  -- Top Left 1/4 (U)
  hs.hotkey.bind(mash, "U", "Move Window to Top-Left 1/4", function()
    move_window(0, 0, 0.5, 0.5)
  end)

  -- Top Right 1/4 (I)
  hs.hotkey.bind(mash, "I", "Move Window to Top-Right 1/4", function()
    move_window(0.5, 0, 0.5, 0.5)
  end)

  -- Bottom Left 1/4 (J)
  hs.hotkey.bind(mash, "J", "Move Window to Bottom-Left 1/4", function()
    move_window(0, 0.5, 0.5, 0.5)
  end)

  -- Bottom Right 1/4 (K)
  hs.hotkey.bind(mash, "K", "Move Window to Bottom-Right 1/4", function()
    move_window(0.5, 0.5, 0.5, 0.5)
  end)

  -- Center (C) - 80% width/height
  hs.hotkey.bind(mash, "C", "Move Window to Center (80%)", function()
    move_window(0.1, 0.1, 0.8, 0.8)
  end)
end

return M