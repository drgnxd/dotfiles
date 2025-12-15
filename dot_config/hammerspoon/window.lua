-- ==========================================
-- ウィンドウ管理 (Rectangle代替機能)
-- ==========================================

local M = {}

-- アニメーション時間を0に設定（瞬時に移動）
hs.window.animationDuration = 0

-- 画面上の位置を計算して移動させる関数
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
  -- モディファイアキー設定 (Ctrl + Alt)
  -- Rectangleのデフォルトに寄せていますが、必要に応じて {"cmd", "alt"} などに変更してください
  local mash = {"ctrl", "alt"}

  -- 左半分 (Left Arrow)
  hs.hotkey.bind(mash, "Left", "ウィンドウを左半分に配置", function()
    move_window(0, 0, 0.5, 1)
  end)

  -- 右半分 (Right Arrow)
  hs.hotkey.bind(mash, "Right", "ウィンドウを右半分に配置", function()
    move_window(0.5, 0, 0.5, 1)
  end)

  -- 最大化 (Enter)
  hs.hotkey.bind(mash, "Return", "ウィンドウを最大化", function()
    move_window(0, 0, 1, 1)
  end)

  -- 上半分 (Up Arrow)
  hs.hotkey.bind(mash, "Up", "ウィンドウを上半分に配置", function()
    move_window(0, 0, 1, 0.5)
  end)

  -- 下半分 (Down Arrow)
  hs.hotkey.bind(mash, "Down", "ウィンドウを下半分に配置", function()
    move_window(0, 0.5, 1, 0.5)
  end)

  -- 左上 1/4 (U)
  hs.hotkey.bind(mash, "U", "ウィンドウを左上1/4に配置", function()
    move_window(0, 0, 0.5, 0.5)
  end)

  -- 右上 1/4 (I)
  hs.hotkey.bind(mash, "I", "ウィンドウを右上1/4に配置", function()
    move_window(0.5, 0, 0.5, 0.5)
  end)

  -- 左下 1/4 (J)
  hs.hotkey.bind(mash, "J", "ウィンドウを左下1/4に配置", function()
    move_window(0, 0.5, 0.5, 0.5)
  end)

  -- 右下 1/4 (K)
  hs.hotkey.bind(mash, "K", "ウィンドウを右下1/4に配置", function()
    move_window(0.5, 0.5, 0.5, 0.5)
  end)

  -- 中央配置 (C) - 幅80%, 高さ80%
  hs.hotkey.bind(mash, "C", "ウィンドウを中央に配置 (80%)", function()
    move_window(0.1, 0.1, 0.8, 0.8)
  end)
end

return M