local M = {}

function M.init()
  hs.alert.show("Config Loaded")

  hs.hotkey.bind({"ctrl", "shift"}, "r", "Reload Config", function()
    hs.reload()
  end)

  M.watcher = hs.pathwatcher.new(hs.configdir .. "/", function()
    hs.reload()
  end)
  M.watcher:start()
end

return M
