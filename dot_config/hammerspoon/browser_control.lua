local M = {}
local target_browser = "Floorp"

local function send_key_to_app(key, mods)
    local app = hs.application.get(target_browser)
    if not app then
        hs.alert.show(target_browser .. " not running")
        return
    end

    local key_code = hs.keycodes.map[key]
    if not key_code then
        hs.alert.show("Unknown key: " .. key)
        return
    end

    mods = mods or {}
    -- keyStroke is easily affected by active window, so
    -- use event.newKeyEvent to post directly to target process
    local event_down = hs.eventtap.event.newKeyEvent(mods, key_code, true)
    event_down:post(app)
    local event_up = hs.eventtap.event.newKeyEvent(mods, key_code, false)
    event_up:post(app)
end

local function bind_browser_hotkey(mods, key, desc, target_key, target_mods)
    hs.hotkey.bind(mods, key, desc, function()
        send_key_to_app(target_key, target_mods)
    end)
end

function M.init()
    local mods = {"ctrl", "cmd"}

    bind_browser_hotkey(mods, "j", "Browser Scroll Down", "pagedown")

    bind_browser_hotkey(mods, "k", "Browser Scroll Up", "pageup")

    bind_browser_hotkey(mods, "h", "Browser Back", "[", {"cmd"})

    bind_browser_hotkey(mods, "l", "Browser Forward", "]", {"cmd"})
end

return M
