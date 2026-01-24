-- ==========================================
-- Config Reload Function
-- ==========================================

local M = {}

function M.init()
  -- Notify when reload completes
  hs.alert.show("Config Loaded")

  -- Manual Reload (Ctrl + Shift + R)
  hs.hotkey.bind({"ctrl", "shift"}, "r", "Reload Config", function()
    hs.reload()
  end)

  -- Auto Reload (Watch for changes in config files)
  M.watcher = hs.pathwatcher.new(os.getenv("HOME") .. "/.hammerspoon/", function()
    hs.reload()
  end)
  M.watcher:start()
end

return M
