local ADDON, ns = ...

local find, sub, byte, lower, match, concat = string.find, string.sub, string.byte, string.lower, string.match, table.concat

ns.PATH = "Interface\\AddOns\\" .. ADDON .. "\\Media\\"

local DEFAULTS = {
	enabled = true,
	emoticons = true, -- ":)" "<3" "xD" ...
	shortcodes = true, -- ":joy:"
	unicode = true, -- pictures typed or pasted as real emoji characters
	size = 0, -- height in pixels, 0 = the height of the chat font
}
ns.DEFAULTS = DEFAULTS
ns.SIZES = { 0, 12, 14, 16, 18, 20, 24, 28, 32 }

local MAX_PER_MESSAGE = 30

-- The chat events that carry text typed by players.
local EVENTS = {
	"CHAT_MSG_SAY", "CHAT_MSG_YELL", "CHAT_MSG_EMOTE",
	"CHAT_MSG_PARTY", "CHAT_MSG_PARTY_LEADER",
	"CHAT_MSG_RAID", "CHAT_MSG_RAID_LEADER", "CHAT_MSG_RAID_WARNING",
	"CHAT_MSG_INSTANCE_CHAT", "CHAT_MSG_INSTANCE_CHAT_LEADER",
	"CHAT_MSG_GUILD", "CHAT_MSG_OFFICER",
	"CHAT_MSG_WHISPER", "CHAT_MSG_WHISPER_INFORM",
	"CHAT_MSG_BN_WHISPER", "CHAT_MSG_BN_WHISPER_INFORM",
	"CHAT_MSG_CHANNEL", "CHAT_MSG_COMMUNITIES_CHANNEL",
	"CHAT_MSG_AFK", "CHAT_MSG_DND",
}

---------------------------------------------------------------------------------------------------
-- Lookup tables, built once from Data.lua and Emoticons.lua
---------------------------------------------------------------------------------------------------

local VS16 = "\239\184\143" -- U+FE0F, asks for the picture form of the character before it
local ZWJ = "\226\128\141" -- U+200D, glues several emoji into one
local KEYCAP = "\226\131\163" -- U+20E3

local codes = {} -- shortcode -> file
local bare = {} -- character or sequence -> file, converted wherever it appears
local withVS = {} -- character -> file, only converted when VS16 follows
local primary = {} -- file -> first shortcode (picker, tooltips, tests)
ns.codes, ns.primary = codes, primary

for _, e in ipairs(ns.EMOJI) do
	local file, char, names = e[2], e[3], e[4]
	if e[5] then
		bare[char] = file
	else
		withVS[char] = file
	end
	primary[file] = primary[file] or names[1]
	for _, name in ipairs(names) do
		codes[name] = file
	end
end

local emoticons = {} -- word -> file
ns.missingEmoticons = {}
for word, name in pairs(ns.EMOTICONS) do
	if codes[name] then
		emoticons[word] = codes[name]
	else
		ns.missingEmoticons[#ns.missingEmoticons + 1] = name
	end
end

---------------------------------------------------------------------------------------------------
-- Markup
---------------------------------------------------------------------------------------------------

local markup = {}

-- The text that shows one picture: |Tpath:height|t. Height 0 makes the client use the font height,
-- the same trick Blizzard uses for raid markers in chat.
local function Markup(file)
	local m = markup[file]
	if not m then
		m = "|T" .. ns.PATH .. file .. ".tga:" .. (ns.db and ns.db.size or 0) .. "|t"
		markup[file] = m
	end
	return m
end
ns.Markup = Markup

function ns.ResetMarkup()
	markup = {}
end

---------------------------------------------------------------------------------------------------
-- Parsing
---------------------------------------------------------------------------------------------------

-- A word that is a text emoticon, optionally followed by sentence punctuation or by a repeat of its
-- last character. Returns the file and the text to put after the picture.
local function Emoticon(w)
	local file = emoticons[w]
	if file then
		return file, ""
	end
	local base, tail = match(w, "^(.-)([%.,!%?]+)$")
	if base and base ~= "" then
		file = emoticons[base]
		if file then
			return file, tail
		end
	else
		base, tail = w, ""
	end
	-- ":)))" -> ":)": cut the run of the last character down to one
	local j, last = #base, sub(base, -1)
	while j > 1 and sub(base, j - 1, j - 1) == last do
		j = j - 1
	end
	if j > 1 and j < #base then
		file = emoticons[sub(base, 1, j)]
		if file then
			return file, tail
		end
	end
end

local function CharLength(lead)
	if lead >= 240 then
		return 4
	elseif lead >= 224 then
		return 3
	end
	return 2
end

-- Real emoji characters at position p of w (lead byte 226 or higher). Reads the character, the
-- variation selector, skin tone modifiers and ZWJ sequences. Returns file and next position.
local function ReadEmoji(w, p)
	local len = CharLength(byte(w, p))
	local first = sub(w, p, p + len - 1)
	local key, q, vs = first, p + len, false
	while true do
		local nxt = sub(w, q, q + 2)
		if nxt == VS16 then
			vs = true
			q = q + 3
		elseif nxt == ZWJ then
			local lead = byte(w, q + 3)
			if not lead or lead < 226 then
				break
			end
			local l2 = CharLength(lead)
			key = key .. ZWJ .. sub(w, q + 3, q + 2 + l2)
			q = q + 3 + l2
		elseif nxt == KEYCAP then
			key = key .. nxt
			q = q + 3
		elseif nxt == "\240\159\143" and byte(w, q + 3) and byte(w, q + 3) >= 187 and byte(w, q + 3) <= 191 then
			q = q + 4 -- skin tone: the plain picture is shown
		else
			break
		end
	end
	local file = bare[key] or (vs and withVS[key])
	if file then
		return file, q
	end
	-- Not a known sequence: fall back to the first character on its own.
	if key ~= first then
		file = bare[first] or (vs and withVS[first])
		if file then
			local q2 = p + len
			if sub(w, q2, q2 + 2) == VS16 then
				q2 = q2 + 3
			end
			return file, q2
		end
	end
end

-- Shortcodes (":joy:") and real emoji characters inside one word. Returns the new word and the
-- number of pictures put in.
local function ScanWord(w, useCodes, useChars, budget)
	if not find(w, "[:\226-\244]") then
		return w, 0
	end
	local out, k, p, n, count = {}, 0, 1, #w, 0
	local mark = 1 -- start of the text not yet copied
	while p <= n and count < budget do
		local c = byte(w, p)
		local file, nextp
		if c == 58 and useCodes then -- ":"
			local _, e, name = find(w, "^:([%w_%+%-]+):", p)
			if e and (p == 1 or not find(sub(w, p - 1, p - 1), "%w")) then
				file = codes[lower(name)]
				nextp = e + 1
			end
		elseif c >= 226 and c <= 244 and useChars then
			file, nextp = ReadEmoji(w, p)
		end
		if file then
			if mark < p then
				k = k + 1
				out[k] = sub(w, mark, p - 1)
			end
			k = k + 1
			out[k] = Markup(file)
			count = count + 1
			p = nextp
			mark = p
		else
			p = p + 1
		end
	end
	if count == 0 then
		return w, 0
	end
	if mark <= n then
		k = k + 1
		out[k] = sub(w, mark)
	end
	return concat(out), count
end

-- Turns the emoticons, shortcodes and emoji characters of a chat line into pictures. Hyperlinks,
-- colour codes and other escape sequences are copied as they are. Returns nil when nothing changed.
function ns.Convert(msg)
	local db = ns.db
	local useEmoticons, useCodes, useChars = db.emoticons, db.shortcodes, db.unicode
	local n = #msg
	local out, k = {}, 0
	local i, count = 1, 0
	local atBoundary = true -- start of the line or just after white space

	while i <= n do
		local c = byte(msg, i)
		if c == 124 then -- "|": escape sequence
			local nx = byte(msg, i + 1)
			local stop
			if nx == 72 then -- |Hlink|htext|h
				local a = find(msg, "|h", i + 2, true)
				local b = a and find(msg, "|h", a + 2, true)
				stop = b and b + 1
			elseif nx == 84 then -- |Ttexture|t
				local a = find(msg, "|t", i + 2, true)
				stop = a and a + 1
			elseif nx == 65 then -- |Aatlas|a
				local a = find(msg, "|a", i + 2, true)
				stop = a and a + 1
			elseif nx == 75 then -- |Kprotected|k
				local a = find(msg, "|k", i + 2, true)
				stop = a and a + 1
			elseif nx == 99 then -- |cAARRGGBB
				stop = i + 9
			else -- |r, ||, |n, ...
				stop = i + 1
			end
			if not stop or stop > n then
				stop = n
			end
			k = k + 1
			out[k] = sub(msg, i, stop)
			if nx ~= 99 and nx ~= 114 then -- colour codes do not break a word boundary
				atBoundary = false
			end
			i = stop + 1
		else
			local _, e = find(msg, "^%s+", i)
			if e then
				k = k + 1
				out[k] = sub(msg, i, e)
				i = e + 1
				atBoundary = true
			else
				_, e = find(msg, "^[^%s|]+", i)
				local w = sub(msg, i, e)
				local budget = MAX_PER_MESSAGE - count
				if budget > 0 then
					local file, tail
					if useEmoticons and atBoundary then
						file, tail = Emoticon(w)
					end
					if file then
						w = Markup(file) .. tail
						count = count + 1
					elseif useCodes or useChars then
						local added
						w, added = ScanWord(w, useCodes, useChars, budget)
						count = count + added
					end
				end
				k = k + 1
				out[k] = w
				i = e + 1
				atBoundary = false
			end
		end
	end

	if count > 0 then
		return concat(out)
	end
end

---------------------------------------------------------------------------------------------------
-- Chat filter
---------------------------------------------------------------------------------------------------

local function Filter(_, _, msg, ...)
	if not ns.db.enabled or type(msg) ~= "string" then
		return false
	end
	if issecretvalue and issecretvalue(msg) then
		return false
	end
	local ok, result = pcall(ns.Convert, msg)
	if not ok then
		ns.lastError = result
		return false
	end
	if result then
		return false, result, ...
	end
	return false
end
ns.Filter = Filter

local function AddFilter(event)
	if ChatFrameUtil and ChatFrameUtil.AddMessageEventFilter then
		ChatFrameUtil.AddMessageEventFilter(event, Filter)
	elseif ChatFrame_AddMessageEventFilter then
		ChatFrame_AddMessageEventFilter(event, Filter)
	end
end

---------------------------------------------------------------------------------------------------
-- Saved settings and start-up
---------------------------------------------------------------------------------------------------

local function InitDB()
	ChatEmojiDB = type(ChatEmojiDB) == "table" and ChatEmojiDB or {}
	for key, value in pairs(DEFAULTS) do
		if ChatEmojiDB[key] == nil then
			ChatEmojiDB[key] = value
		end
	end
	ns.db = ChatEmojiDB
end

-- Made before the first message can arrive, so the filter always has a table to read.
ns.db = {}
for key, value in pairs(DEFAULTS) do
	ns.db[key] = value
end

function ns.Print(text)
	local frame = DEFAULT_CHAT_FRAME
	if frame then
		frame:AddMessage("|cff66ccffChatEmoji|r: " .. text)
	end
end

local frame = CreateFrame("Frame")
frame:RegisterEvent("ADDON_LOADED")
frame:SetScript("OnEvent", function(self, event, name)
	if name ~= ADDON then
		return
	end
	self:UnregisterEvent("ADDON_LOADED")
	InitDB()
	ns.ResetMarkup()
	for _, ev in ipairs(EVENTS) do
		AddFilter(ev)
	end
	if ns.OnLoaded then
		ns.OnLoaded()
	end
end)
