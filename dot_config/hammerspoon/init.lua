-- ==========================================
-- Hammerspoon 設定ファイル
-- ==========================================

-- ショートカット情報を保存するテーブルを準備
hs.my_hotkeys = {}

-- 既存の bind 関数を保存
local original_bind = hs.hotkey.bind

-- bind 関数を上書き（ラップ）して、登録時に情報を記録するようにする
hs.hotkey.bind = function(mods, key, param1, ...)
    local message = "No Description"
    
    -- 第3引数(param1)が文字列なら、それを説明文とする
    if type(param1) == "string" then
        message = param1
    end

    -- 記録テーブルに保存
    table.insert(hs.my_hotkeys, {
        mods = mods,
        key = key,
        msg = message
    })

    -- 本来の bind 関数を実行
    return original_bind(mods, key, param1, ...)
end

-- モジュールの読み込み
local reload = require("reload")
local input_switcher = require("input_switcher")
local caffeine = require("caffeine")
local window = require("window")
local cheatsheet = require("cheatsheet")
local browser_control = require("browser_control")

-- 各モジュールの初期化
reload.init()
input_switcher.init()
caffeine.init()
window.init()
cheatsheet.init()
browser_control.init()