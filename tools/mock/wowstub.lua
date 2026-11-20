-- A small stand-in for the WoW client, enough to load and drive ChatEmoji outside the game.
--
--   * the chat filter registry follows Blizzard_ChatFrameBase/Shared/ChatFrameFilters.lua (1.60.1):
--     callbacks only run for values the addon may read, the first return value discards the
--     message, the second and later return values replace the arguments
--   * frames are plain tables: CamelCase fields are methods (state kept only for the ones the
--     addon reads back), lower-case fields are real data, so `frame.emoji` is nil when unset
--
-- Mock.load(dir)        run Data.lua, Emoticons.lua, Core.lua, UI.lua like the client does
-- Mock.fire(event, ...) call every OnEvent script registered for the event
-- Mock.deliver(event, text, author)  run a chat line through the filters, returns shown text, author
os.setlocale("C") -- the game runs in the C locale; the host's would change %s / %w on UTF-8 bytes

Mock = { lines = {}, frames = {}, tooltip = {}, secret = {} }

local function noop(self)
	return self
end

local state = {} -- per method: how a stateful method behaves

local function newObject(kind, name, parent)
	local obj = { _kind = kind, _name = name, _parent = parent, _scripts = {}, _events = {}, _shown = true,
		_text = "", _children = {} }
	return setmetatable(obj, {
		__index = function(t, key)
			if type(key) == "string" and key:match("^%u") then
				return state[key] or noop
			end
		end,
	})
end

function state.SetText(self, text)
	self._text = text
end
function state.GetText(self)
	return self._text
end
function state.SetTexture(self, path)
	self._texture = path
end
function state.GetTexture(self)
	return self._texture
end
function state.SetScript(self, which, fn)
	self._scripts[which] = fn
end
function state.GetScript(self, which)
	return self._scripts[which]
end
function state.RegisterEvent(self, event)
	self._events[event] = true
end
function state.UnregisterEvent(self, event)
	self._events[event] = nil
end
function state.Show(self)
	self._shown = true
end
function state.Hide(self)
	self._shown = false
end
function state.SetShown(self, shown)
	self._shown = shown and true or false
end
function state.IsShown(self)
	return self._shown
end
function state.CreateTexture(self, name)
	local t = newObject("Texture", name, self)
	self._children[#self._children + 1] = t
	return t
end
function state.CreateFontString(self, name)
	local t = newObject("FontString", name, self)
	self._children[#self._children + 1] = t
	return t
end
function state.SetColorTexture(self, r, g, b, a)
	self._color = { r, g, b, a }
end
function state.Insert(self, text)
	self._text = self._text .. text
	self._inserted = (self._inserted or "") .. text
end

function CreateFrame(kind, name, parent)
	local f = newObject(kind, name, parent)
	if name then
		_G[name] = f
	end
	Mock.frames[#Mock.frames + 1] = f
	return f
end

function Mock.fire(event, ...)
	for _, f in ipairs(Mock.frames) do
		local fn = f._scripts.OnEvent
		if f._events[event] and fn then
			fn(f, event, ...)
		end
	end
end

UIParent = CreateFrame("Frame", "UIParent")
UISpecialFrames = {}
SlashCmdList = {}

GameTooltip = newObject("GameTooltip", "GameTooltip")
function GameTooltip:SetOwner(owner)
	Mock.tooltip = { owner = owner }
end
function GameTooltip:SetText(text)
	Mock.tooltip.title = text
end
function GameTooltip:AddLine(text)
	Mock.tooltip[#Mock.tooltip + 1] = text
end

DEFAULT_CHAT_FRAME = { AddMessage = function(_, text) Mock.lines[#Mock.lines + 1] = text end }

-- Secret values: Mock.secret[str] = true marks a string as unreadable (retail 12 combat chat).
function issecretvalue(v)
	return Mock.secret[v] == true
end
local function canaccessvalue(...)
	for i = 1, select("#", ...) do
		if Mock.secret[(select(i, ...))] == true then
			return false
		end
	end
	return true
end

-- Chat edit box and chat helpers ---------------------------------------------------------------
Mock.editBox = newObject("EditBox", "ChatFrame1EditBox")
Mock.editBoxActive = false

ChatFrameUtil = {}
local filters = {}
function ChatFrameUtil.AddMessageEventFilter(event, callback)
	filters[event] = filters[event] or {}
	for _, cb in ipairs(filters[event]) do
		if cb == callback then
			return
		end
	end
	table.insert(filters[event], callback)
end
function ChatFrameUtil.GetActiveWindow()
	return Mock.editBoxActive and Mock.editBox or nil
end
function ChatFrameUtil.OpenChat()
	Mock.editBoxActive = true
end

function Mock.filterCount(event)
	return filters[event] and #filters[event] or 0
end

local function pack(...)
	return { n = select("#", ...), ... }
end

-- Returns discarded (bool) followed by the arguments the chat frame would show.
function Mock.deliver(event, ...)
	local args = pack(...)
	for _, cb in ipairs(filters[event] or {}) do
		if canaccessvalue(unpack(args, 1, args.n)) then
			local res = pack(pcall(cb, nil, event, unpack(args, 1, args.n)))
			assert(res[1], "filter raised: " .. tostring(res[2]))
			-- res[2] is the discard flag, res[3] and later replace the arguments
			if res[2] then
				return true
			end
			if res[3] then
				args = pack(unpack(res, 3, res.n))
			end
		end
	end
	return false, unpack(args, 1, args.n)
end

-- Loading ---------------------------------------------------------------------------------------
function Mock.load(dir)
	Mock.ns = {}
	for _, file in ipairs({ "Data.lua", "Emoticons.lua", "Core.lua", "UI.lua" }) do
		local chunk, err = loadfile(dir .. "/" .. file)
		assert(chunk, err)
		chunk("ChatEmoji", Mock.ns)
	end
	Mock.fire("ADDON_LOADED", "ChatEmoji")
	return Mock.ns
end

-- Test helper: turns the picture markup back into <shortcode> so results read like text.
function Mock.norm(text)
	if not text then
		return nil
	end
	return (text:gsub("|TInterface\\AddOns\\ChatEmoji\\Media\\([%w%-]+)%.tga:(%d+)|t", function(file, size)
		local name = Mock.ns.primary[file] or ("?" .. file)
		return "<" .. name .. (size ~= "0" and (":" .. size) or "") .. ">"
	end))
end
