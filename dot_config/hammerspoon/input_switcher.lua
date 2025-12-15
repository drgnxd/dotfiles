-- ==========================================
-- 自動英語切り替え機能
-- ==========================================

local M = {}

-- 英語入力ソースのID (環境に合わせて書き換えてください)
local english_input_id = "com.apple.keylayout.ABC"

-- 対象アプリ名リスト
local target_apps = {
  "Alacritty",
  "Sol",
}

function M.init()
  -- 各アプリに対してウィンドウフィルターを作成
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