-- ==========================================
-- バックグラウンドブラウザ操作 (Direct Key Event Mode)
-- ==========================================

local M = {}
local target_browser = "Floorp"

-- キーイベントを作成して特定のアプリに送信する関数
local function send_key_to_app(key, mods)
    local app = hs.application.get(target_browser)
    if not app then
        hs.alert.show(target_browser .. " not running")
        return
    end

    -- PageUp/PageDown 等のキーコードを取得
    local key_code = hs.keycodes.map[key]
    
    -- keyStroke はアクティブウィンドウに影響されやすいため、
    -- event.newKeyEvent を使用してターゲットプロセスへ直接 post する
    
    -- 1. Key Down
    local event_down = hs.eventtap.event.newKeyEvent(mods or {}, key_code, true)
    event_down:post(app)
    
    -- 2. Key Up
    local event_up = hs.eventtap.event.newKeyEvent(mods or {}, key_code, false)
    event_up:post(app)
end

function M.init()
    local mods = {"ctrl", "cmd"}

    -- Scroll Down (J) -> PageDown
    hs.hotkey.bind(mods, "j", "Browser Scroll Down", function()
        send_key_to_app("pagedown", {})
    end)

    -- Scroll Up (K) -> PageUp
    hs.hotkey.bind(mods, "k", "Browser Scroll Up", function()
        send_key_to_app("pageup", {})
    end)

    -- History Back (H) -> Cmd + [
    hs.hotkey.bind(mods, "h", "Browser Back", function()
        send_key_to_app("[", {"cmd"})
    end)

    -- History Forward (L) -> Cmd + ]
    hs.hotkey.bind(mods, "l", "Browser Forward", function()
        send_key_to_app("]", {"cmd"})
    end)
end

return M
