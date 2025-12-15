-- ==========================================
-- スリープ防止機能 (Caffeine)
-- ==========================================

local M = {}

local caffeine = nil

-- アイコンの表示を切り替える関数
local function set_caffeine_display(state)
  if state then
    caffeine:setTitle("☕️") -- ON: スリープしない
  else
    caffeine:setTitle("💤") -- OFF: 通常通りスリープする
  end
end

-- クリック時の動作
local function caffeine_clicked()
  -- displayIdle（ディスプレイのスリープ）を防ぐ設定をトグルする
  set_caffeine_display(hs.caffeinate.toggle("displayIdle"))
end

function M.init()
  caffeine = hs.menubar.new()
  
  if caffeine then
    caffeine:setClickCallback(caffeine_clicked)
    -- 起動時の状態を取得して表示
    set_caffeine_display(hs.caffeinate.get("displayIdle"))
  end
end

return M