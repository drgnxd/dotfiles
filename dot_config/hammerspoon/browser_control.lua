-- ==========================================
-- Background Browser Control (Direct Key Event Mode)
-- ==========================================

local M = {}
local target_browser = "Floorp"

-- Function to create key event and send to specific app
local function send_key_to_app(key, mods)
    local app = hs.application.get(target_browser)
    if not app then
        hs.alert.show(target_browser .. " not running")
        return
    end

    -- Get keycode for PageUp/PageDown etc.
    local key_code = hs.keycodes.map[key]
    
    -- keyStroke is easily affected by active window, so
    -- use event.newKeyEvent to post directly to target process
    
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
