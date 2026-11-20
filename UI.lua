local ADDON, ns = ...

-- /emoji opens a small window: pick a picture to put its shortcode into the chat box, and switch
-- the parts of the addon on or off. Everything is built the first time the window opens.

local COLS, ROWS, CELL, PAD = 8, 6, 34, 12
local WIDTH = COLS * CELL + PAD * 2
local PER_PAGE = COLS * ROWS

local picker
local group, page = 1, 1
local list = {} -- emoji of the current group

local function Fill(tex, r, g, b, a)
	tex:SetColorTexture(r, g, b, a)
end

local function ActiveEditBox()
	if ChatFrameUtil and ChatFrameUtil.GetActiveWindow then
		return ChatFrameUtil.GetActiveWindow()
	end
	if ChatEdit_GetActiveWindow then
		return ChatEdit_GetActiveWindow()
	end
end

-- Only ever puts text into a chat box the player has already opened. Opening chat from here
-- (ChatFrameUtil.OpenChat) would run Blizzard's gamepad chat focus code, which writes the input
-- binding stack, in this addon's execution: that taints the stack and a later Esc / panel close is
-- then reported as ADDON_ACTION_FORBIDDEN (SetPreferredGamepadInteractTarget) against ChatEmoji.
local function Insert(text)
	local box = ActiveEditBox()
	if box then
		box:Insert(text)
	else
		ns.Print("open the chat box first (Enter), then click a picture")
	end
end

local function GroupList(id)
	local result = {}
	for _, e in ipairs(ns.EMOJI) do
		if e[1] == id then
			result[#result + 1] = e
		end
	end
	return result
end

local function Preview()
	local text = ns.Convert(":) :D <3 :joy: :fire: o/") or ""
	picker.preview:SetText(text)
end

local function SizeText()
	local size = ns.db.size
	return size == 0 and "auto" or (size .. " px")
end

local function Refresh()
	if not picker then
		return
	end
	local pages = math.max(1, math.ceil(#list / PER_PAGE))
	if page > pages then
		page = pages
	end
	picker.pageText:SetText(page .. " / " .. pages)
	for i, cell in ipairs(picker.cells) do
		local e = list[(page - 1) * PER_PAGE + i]
		cell.emoji = e
		if e then
			cell.icon:SetTexture(ns.PATH .. e[2] .. ".tga")
			cell:Show()
		else
			cell:Hide()
		end
	end
	for i, tab in ipairs(picker.tabs) do
		if i == group then
			tab.text:SetTextColor(1, 0.82, 0)
		else
			tab.text:SetTextColor(0.75, 0.75, 0.75)
		end
	end
	for _, check in ipairs(picker.checks) do
		check.mark:SetShown(ns.db[check.key])
	end
	picker.sizeText:SetText(SizeText())
	Preview()
end

local function SelectGroup(i)
	group, page = i, 1
	list = GroupList(ns.GROUPS[i].id)
	Refresh()
end

local function Button(parent, width, height, label)
	local b = CreateFrame("Button", nil, parent)
	b:SetSize(width, height)
	b.bg = b:CreateTexture(nil, "BACKGROUND")
	b.bg:SetAllPoints()
	Fill(b.bg, 0.16, 0.16, 0.2, 1)
	b.text = b:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
	b.text:SetPoint("CENTER")
	b.text:SetText(label or "")
	b:SetScript("OnEnter", function(self)
		Fill(self.bg, 0.26, 0.26, 0.32, 1)
	end)
	b:SetScript("OnLeave", function(self)
		Fill(self.bg, 0.16, 0.16, 0.2, 1)
	end)
	return b
end

local function Check(parent, key, label, x, y)
	local b = CreateFrame("Button", nil, parent)
	b:SetSize(150, 18)
	b:SetPoint("TOPLEFT", parent, "TOPLEFT", x, y)
	b.key = key
	b.box = b:CreateTexture(nil, "BACKGROUND")
	b.box:SetSize(14, 14)
	b.box:SetPoint("LEFT")
	Fill(b.box, 0.3, 0.3, 0.36, 1)
	b.mark = b:CreateTexture(nil, "ARTWORK")
	b.mark:SetSize(8, 8)
	b.mark:SetPoint("CENTER", b.box, "CENTER")
	Fill(b.mark, 1, 0.82, 0, 1)
	b.label = b:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
	b.label:SetPoint("LEFT", b.box, "RIGHT", 6, 0)
	b.label:SetText(label)
	b:SetScript("OnClick", function(self)
		ns.db[self.key] = not ns.db[self.key]
		Refresh()
	end)
	return b
end

local function ChangeSize(step)
	local sizes, index = ns.SIZES, 1
	for i, v in ipairs(sizes) do
		if v == ns.db.size then
			index = i
		end
	end
	index = math.min(#sizes, math.max(1, index + step))
	ns.db.size = sizes[index]
	ns.ResetMarkup()
	Refresh()
end

local function Build()
	local height = PAD + 24 + 24 + ROWS * CELL + 28 + 4 * 22 + 36 + PAD
	local f = CreateFrame("Frame", "ChatEmojiPicker", UIParent)
	picker = f
	f:SetSize(WIDTH, height)
	f:SetPoint("CENTER")
	f:SetFrameStrata("DIALOG")
	f:SetClampedToScreen(true)
	f:SetMovable(true)
	f:EnableMouse(true)
	f:RegisterForDrag("LeftButton")
	f:SetScript("OnDragStart", f.StartMoving)
	f:SetScript("OnDragStop", f.StopMovingOrSizing)

	f.bg = f:CreateTexture(nil, "BACKGROUND")
	f.bg:SetAllPoints()
	Fill(f.bg, 0.05, 0.05, 0.07, 0.96)
	for _, edge in ipairs({ { "TOPLEFT", "TOPRIGHT", true }, { "BOTTOMLEFT", "BOTTOMRIGHT", true },
		{ "TOPLEFT", "BOTTOMLEFT", false }, { "TOPRIGHT", "BOTTOMRIGHT", false } }) do
		local line = f:CreateTexture(nil, "BORDER")
		Fill(line, 0.4, 0.4, 0.46, 1)
		line:SetPoint(edge[1])
		line:SetPoint(edge[2])
		if edge[3] then
			line:SetHeight(1)
		else
			line:SetWidth(1)
		end
	end

	f.title = f:CreateFontString(nil, "OVERLAY", "GameFontNormal")
	f.title:SetPoint("TOPLEFT", PAD, -PAD)
	f.title:SetText("ChatEmoji")

	local close = Button(f, 20, 20, "x")
	close:SetPoint("TOPRIGHT", -PAD + 4, -PAD + 4)
	close:SetScript("OnClick", function()
		f:Hide()
	end)

	f.tabs = {}
	local x = PAD
	for i, g in ipairs(ns.GROUPS) do
		local tab = Button(f, 52, 20, g.label)
		tab:SetPoint("TOPLEFT", f, "TOPLEFT", x, -PAD - 24)
		tab:SetScript("OnClick", function()
			SelectGroup(i)
		end)
		f.tabs[i] = tab
		x = x + 54
	end

	f.cells = {}
	local top = -(PAD + 24 + 24)
	for i = 1, PER_PAGE do
		local cell = CreateFrame("Button", nil, f)
		cell:SetSize(CELL, CELL)
		local col, row = (i - 1) % COLS, math.floor((i - 1) / COLS)
		cell:SetPoint("TOPLEFT", f, "TOPLEFT", PAD + col * CELL, top - row * CELL)
		cell.icon = cell:CreateTexture(nil, "ARTWORK")
		cell.icon:SetSize(CELL - 8, CELL - 8)
		cell.icon:SetPoint("CENTER")
		cell.hl = cell:CreateTexture(nil, "HIGHLIGHT")
		cell.hl:SetAllPoints()
		Fill(cell.hl, 1, 1, 1, 0.15)
		cell:SetScript("OnClick", function(self)
			local e = self.emoji
			if e then
				Insert(":" .. e[4][1] .. ": ")
			end
		end)
		cell:SetScript("OnEnter", function(self)
			local e = self.emoji
			if not e then
				return
			end
			GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
			GameTooltip:SetText(":" .. e[4][1] .. ":", 1, 1, 1)
			for i2 = 2, #e[4] do
				GameTooltip:AddLine(":" .. e[4][i2] .. ":", 0.7, 0.7, 0.7)
			end
			local words = ns.EMOTICON_WORDS[e[4][1]]
			if words then
				GameTooltip:AddLine(table.concat(words, "   "), 0.4, 0.8, 1)
			end
			GameTooltip:Show()
		end)
		cell:SetScript("OnLeave", function()
			GameTooltip:Hide()
		end)
		f.cells[i] = cell
	end

	local gridBottom = top - ROWS * CELL
	local prev = Button(f, 24, 20, "<")
	prev:SetPoint("TOPLEFT", f, "TOPLEFT", PAD, gridBottom - 4)
	prev:SetScript("OnClick", function()
		page = math.max(1, page - 1)
		Refresh()
	end)
	local nxt = Button(f, 24, 20, ">")
	nxt:SetPoint("TOPRIGHT", f, "TOPRIGHT", -PAD, gridBottom - 4)
	nxt:SetScript("OnClick", function()
		page = page + 1
		Refresh()
	end)
	f.pageText = f:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
	f.pageText:SetPoint("TOP", f, "TOP", 0, gridBottom - 8)

	local y = gridBottom - 36
	f.checks = {
		Check(f, "enabled", "Convert chat", PAD, y),
		Check(f, "emoticons", "Emoticons  :)", PAD + 150, y),
		Check(f, "shortcodes", "Shortcodes  :joy:", PAD, y - 22),
		Check(f, "unicode", "Emoji characters", PAD + 150, y - 22),
	}

	local sizeLabel = f:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
	sizeLabel:SetPoint("TOPLEFT", f, "TOPLEFT", PAD, y - 50)
	sizeLabel:SetText("Size in chat")
	local minus = Button(f, 20, 18, "-")
	minus:SetPoint("TOPLEFT", f, "TOPLEFT", PAD + 90, y - 48)
	minus:SetScript("OnClick", function()
		ChangeSize(-1)
	end)
	f.sizeText = f:CreateFontString(nil, "OVERLAY", "GameFontHighlightSmall")
	f.sizeText:SetPoint("LEFT", minus, "RIGHT", 6, 0)
	f.sizeText:SetWidth(44)
	local plus = Button(f, 20, 18, "+")
	plus:SetPoint("LEFT", minus, "RIGHT", 54, 0)
	plus:SetScript("OnClick", function()
		ChangeSize(1)
	end)

	f.preview = f:CreateFontString(nil, "OVERLAY", "ChatFontNormal")
	f.preview:SetPoint("TOPLEFT", f, "TOPLEFT", PAD, y - 78)
	f.preview:SetPoint("RIGHT", f, "RIGHT", -PAD, 0)
	f.preview:SetJustifyH("LEFT")

	if UISpecialFrames then
		table.insert(UISpecialFrames, "ChatEmojiPicker")
	end
	f:Hide()
	SelectGroup(1)
end

function ns.TogglePicker()
	if not picker then
		Build()
	end
	if picker:IsShown() then
		picker:Hide()
	else
		Refresh()
		picker:Show()
	end
end

---------------------------------------------------------------------------------------------------
-- Slash command
---------------------------------------------------------------------------------------------------

local function Say(text)
	ns.Print(text)
end

local function SetFlag(key, label, value)
	ns.db[key] = value
	Say(label .. (value and " on" or " off"))
	Refresh()
end

local function Slash(input)
	local cmd, arg = (input or ""):match("^%s*(%S*)%s*(.-)%s*$")
	cmd = cmd:lower()
	if cmd == "" or cmd == "show" or cmd == "list" then
		ns.TogglePicker()
	elseif cmd == "on" or cmd == "off" then
		SetFlag("enabled", "conversion", cmd == "on")
	elseif cmd == "size" then
		local n = tonumber(arg)
		if n and (n == 0 or (n >= 8 and n <= 64)) then
			ns.db.size = math.floor(n)
			ns.ResetMarkup()
			Say("size " .. (n == 0 and "auto" or (n .. " px")))
			Refresh()
		else
			Say("usage: /emoji size <0 for auto, or 8-64>")
		end
	elseif cmd == "test" then
		local sample = ":) :D ;) :P :( :'( <3 </3 xD QQ o/ o7 :joy: :fire: :+1: :skull:"
		Say(ns.Convert(sample) or sample)
	elseif cmd == "debug" then
		Say("enabled " .. tostring(ns.db.enabled) .. ", size " .. SizeText() .. ", last error " .. tostring(ns.lastError))
		if #ns.missingEmoticons > 0 then
			Say("emoticons without a picture: " .. table.concat(ns.missingEmoticons, ", "))
		end
	else
		Say("/emoji - picker and settings; /emoji on|off; /emoji size <0|8-64>; /emoji test")
	end
end

SLASH_CHATEMOJI1 = "/emoji"
SLASH_CHATEMOJI2 = "/emojis"
SlashCmdList["CHATEMOJI"] = Slash
