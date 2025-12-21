-- ==========================================
-- Window Management (Rectangle Alternative)
-- ==========================================

local M = {}

-- Set animation duration to 0 (instant move)
hs.window.animationDuration = 0

-- Function to calculate position and move window
local function move_window(x, y, w, h)
  local win = hs.window.focusedWindow()
  if not win then return end

  local f = win:frame()
  local screen = win:screen()
  local max = screen:frame()

  f.x = max.x + (max.w * x)
  f.y = max.y + (max.h * y)
  f.w = max.w * w
  f.h = max.h * h
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