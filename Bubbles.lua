local ADDON, ns = ...

-- Chat bubbles above characters. The bubble frames are made by the client, so the filter that
-- converts chat lines never sees them. Instead, shortly after a chat event that can produce a
-- bubble, the visible bubbles are read and the text of each one goes through the same converter.
-- Nothing here touches Blizzard's secure code: it runs from this addon's own frame and only calls
-- SetText on the bubble's string.

local CB = C_ChatBubbles
if not (CB and CB.GetAllChatBubbles) then
	return
end

local EVENTS = {
	"CHAT_MSG_SAY", "CHAT_MSG_YELL", "CHAT_MSG_EMOTE",
	"CHAT_MSG_PARTY", "CHAT_MSG_PARTY_LEADER",
	"CHAT_MSG_MONSTER_SAY", "CHAT_MSG_MONSTER_YELL", "CHAT_MSG_MONSTER_EMOTE", "CHAT_MSG_MONSTER_PARTY",
}

local WATCH_SECONDS = 0.6 -- how long after a chat event the bubbles are looked at
local STEP = 0.05 -- seconds between looks

local function FindString(bubble)
	local s = bubble.String
	if s and s.GetText then
		return s
	end
	for i = 1, bubble:GetNumChildren() do
		local child = select(i, bubble:GetChildren())
		s = child and child.String
		if s and s.GetText then
			return s
		end
	end
	for i = 1, bubble:GetNumRegions() do
		local region = select(i, bubble:GetRegions())
		if region and region.GetObjectType and region:GetObjectType() == "FontString" then
			return region
		end
	end
end

local function ScanOne(bubble)
	local fs = FindString(bubble)
	if not fs then
		return
	end
	local text = fs:GetText()
	if type(text) ~= "string" or (issecretvalue and issecretvalue(text)) then
		return
	end
	local converted = ns.Convert(text)
	if converted then
		fs:SetText(converted)
	end
end

function ns.ScanBubbles()
	local db = ns.db
	if not db.enabled or not db.bubbles then
		return
	end
	local ok, list = pcall(CB.GetAllChatBubbles)
	if not ok or type(list) ~= "table" then
		return
	end
	for _, bubble in ipairs(list) do
		local fine, err = pcall(ScanOne, bubble)
		if not fine then
			ns.lastError = err
		end
	end
end

local watcher = CreateFrame("Frame")
local untilTime, elapsed = 0, 0

local function OnUpdate(self, dt)
	elapsed = elapsed + dt
	if elapsed < STEP then
		return
	end
	elapsed = 0
	ns.ScanBubbles()
	if GetTime() >= untilTime then
		self:SetScript("OnUpdate", nil)
	end
end

watcher:SetScript("OnEvent", function(self)
	if not (ns.db.enabled and ns.db.bubbles) then
		return
	end
	untilTime = GetTime() + WATCH_SECONDS
	elapsed = STEP -- first look on the next frame
	self:SetScript("OnUpdate", OnUpdate)
end)

for _, event in ipairs(EVENTS) do
	watcher:RegisterEvent(event)
end
