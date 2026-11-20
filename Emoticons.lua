local _, ns = ...

-- Text emoticons. Each line is: shortcode of the picture = { the words people type }.
-- A word only counts when it stands alone (space or message edge on both sides), so ":)" inside
-- "http://x.com:)" or "(8)" is left alone. Sentence punctuation after it is fine (":) ." ":)!"),
-- and a repeated last character is fine too (":)))" ":DDD" "<33").
local GROUPS = {
	slightly_smiling_face = { ":)", ":-)", "(:", "=)", ":]", ":^)" },
	smiley = { ":D", ":-D", "=D", ":d", ":-d" },
	laughing = { "xD", "XD", "xd", "Xd", "x-D", "X-D" },
	joy = { ":'D", ":'-D" },
	smiling_face_with_tear = { ":')", ":'-)" },
	wink = { ";)", ";-)", ";]" },
	stuck_out_tongue = { ":P", ":p", ":-P", ":-p", "=P", "=p" },
	stuck_out_tongue_winking_eye = { ";P", ";p", ";-P", ";-p" },
	slightly_frowning_face = { ":(", ":-(", "=(", ":[" },
	cry = { ":'(", ":'-(", ";(", ";-(", ";_;" },
	sob = { "T_T", "T.T", "T-T", "QQ", "Q_Q", "Q.Q" },
	open_mouth = { ":O", ":o", ":-O", ":-o", "=O", ":0" },
	flushed = { "O_O", "o_o", "O.O", "o.o", ":$", ":-$" },
	raised_eyebrow = { "o_O", "O_o", "o.O", "O.o" },
	kissing_heart = { ":*", ":-*", ";*", "=*" },
	heart = { "<3" },
	broken_heart = { "</3" },
	sunglasses = { "B-)", "8-)" },
	innocent = { "O:)", "O:-)", "0:)", "0:-)" },
	smiling_imp = { ">:)", ">:-)", "3:)", "3:-)", ">:D" },
	angry = { ">:(", ">:-(", ">:[" },
	rage = { ":@", ">:O" },
	anguished = { "D:", "D-:" },
	neutral_face = { ":|", ":-|", "=|" },
	confused = { ":/", ":-/", ":\\", ":-\\", "=/", "=\\" },
	smiley_cat = { ":3", ":-3", "=3" },
	blush = { "^_^", "^^", "^.^", "^-^", "^o^" },
	expressionless = { "-_-", "-.-", "-__-", "=_=" },
	persevere = { ">_<", ">.<", ">__<" },
	zipper_mouth_face = { ":x", ":X", ":-x", ":-X", ":#", ":-#" },
	eyes = { "<_<", ">_>", "<.<", ">.>" },
	saluting_face = { "o7" },
	wave = { "o/", "\\o" },
	raised_hands = { "\\o/", "\\O/" },
	["+1"] = { "(y)", "(Y)" },
	["-1"] = { "(n)", "(N)" },
}

-- word -> shortcode
ns.EMOTICONS = {}
for name, words in pairs(GROUPS) do
	for _, word in ipairs(words) do
		ns.EMOTICONS[word] = name
	end
end

-- same list, one sample per picture, for the picker tooltip: shortcode -> { words }
ns.EMOTICON_WORDS = GROUPS
