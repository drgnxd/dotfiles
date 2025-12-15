-- ==========================================
-- 設定リロード機能
-- ==========================================

local M = {}

function M.init()
  -- リロード完了時に通知
  hs.alert.show("Config Loaded")

  -- 手動リロード (Ctrl + Shift + R)
  hs.hotkey.bind({"ctrl", "shift"}, "r", "設定をリロード", function()
    hs.reload()
  end)

  -- 自動リロード (設定ファイルの変更を監視)
  hs.pathwatcher.new(os.getenv("HOME") .. "/.hammerspoon/", function()
    hs.reload()
  end):start()
end

return M
