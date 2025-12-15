-- ==========================================
-- キーバインド一覧表示 (CheatSheet) - 修正版
-- ==========================================

local M = {}
local chooser = nil

-- モディファイアキーの表示用記号
local mod_symbols = {
    cmd = "⌘",
    alt = "⌥",
    shift = "⇧",
    ctrl = "⌃",
}

-- モディファイアを整形する関数
local function format_mods(mods)
    if type(mods) ~= "table" then return "" end
    local order = {"ctrl", "alt", "shift", "cmd"}
    local result = ""
    for _, key in ipairs(order) do
        for _, mod in ipairs(mods) do
            if mod == key then
                result = result .. (mod_symbols[key] or key)
            end
        end
    end
    return result
end

-- 一覧を表示する関数
local function show_cheatsheet()
    local choices = {}
    
    -- init.lua で記録した hs.my_hotkeys を使用
    -- (hs.my_hotkeys が無い場合のガードも追加)
    local keys = hs.my_hotkeys or {}

    for i, hk in ipairs(keys) do
        local sub_text = format_mods(hk.mods) .. " " .. string.upper(hk.key)
        
        table.insert(choices, {
            text = hk.msg,       -- 説明文
            subText = sub_text,   -- キー (例: ⌃⌥ C)
            uuid = i
        })
    end

    -- キー順で見やすくソート
    table.sort(choices, function(a, b) return a.subText < b.subText end)

    chooser:choices(choices)
    chooser:show()
end

function M.init()
    -- 選択時は何もしない設定
    chooser = hs.chooser.new(function(choice) end)
    chooser:placeholderText("Keybinds List")
    chooser:bgDark(true) -- ダークモード対応
    
    -- 呼び出しキー設定 (第3引数のメッセージを削除して、自動アラートが出ないようにする)
    hs.hotkey.bind({"ctrl", "alt"}, "/", "キーバインド一覧を表示", function()
        show_cheatsheet()
    end)
end

return M