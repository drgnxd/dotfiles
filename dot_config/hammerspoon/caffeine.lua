local M = {}

local caffeine = nil

local function set_caffeine_display(state)
  if state then
    caffeine:setTitle("☕️")
  else
    caffeine:setTitle("💤")
  end
end

local function caffeine_clicked()
  set_caffeine_display(hs.caffeinate.toggle("displayIdle"))
end

function M.init()
  caffeine = hs.menubar.new()
   if caffeine then
    caffeine:setClickCallback(caffeine_clicked)
    set_caffeine_display(hs.caffeinate.get("displayIdle"))
  end
end

return M
