"""Runs the real addon code against the mock client (tools/mock/wowstub.lua) under Lua 5.1.

    python tools/test_addon.py

Expected results write a picture as <shortcode> (see Mock.norm), so a line reads like the chat.
"""
import os
import re
import struct
import sys

from lupa import lua51

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADDON = ROOT
MOCK = os.path.join(ROOT, "tools", "mock", "wowstub.lua")


def new_runtime(before=""):
    """before: Lua run first, e.g. to put saved variables in place."""
    lua = lua51.LuaRuntime(unpack_returned_tuples=True)
    lua.execute(open(MOCK, encoding="utf-8").read())
    lua.execute(before)
    lua.execute('Mock.load(%r)' % ADDON.replace("\\", "/"))
    return lua


FAILS = []
COUNT = 0


def check(label, got, want):
    global COUNT
    COUNT += 1
    if got != want:
        FAILS.append((label, got, want))


def u(s):
    """Lua strings come back as bytes in lupa when they are not valid text; normalise to str."""
    return s.decode("utf-8") if isinstance(s, bytes) else s


def main():
    lua = new_runtime()
    g = lua.globals()
    ns = g.Mock.ns
    db = ns.db

    def convert(text, **flags):
        old = {k: db[k] for k in flags}
        for k, v in flags.items():
            db[k] = v
        ns.ResetMarkup()
        try:
            res = ns.Convert(text.encode("utf-8"))
            return u(g.Mock.norm(res)) if res else None
        finally:
            for k, v in old.items():
                db[k] = v
            ns.ResetMarkup()

    def same(label, text, **flags):
        check(label, convert(text, **flags), None)

    def to(label, text, want, **flags):
        check(label, convert(text, **flags), want)

    # data sanity ---------------------------------------------------------------------------
    check("emoticons that point at a missing picture", list(ns.missingEmoticons.values()), [])
    files = [u(e[2]) for e in ns.EMOJI.values()]
    check("every picture exists on disk", [f for f in files
          if not os.path.exists(os.path.join(ADDON, "Media", f + ".tga"))], [])
    check("a file per emoji, no duplicates", len(files), len(set(files)))
    for f in files[:: max(1, len(files) // 25)]:
        data = open(os.path.join(ADDON, "Media", f + ".tga"), "rb").read()
        idtype, cmap, itype, _a, _b, _c, _x, _y, w, h, bpp, desc = struct.unpack("<BBBHHBHHHHBB", data[:18])
        check("TGA header of %s" % f, (itype, w, h, bpp, desc & 0x0F, len(data)), (2, 32, 32, 32, 8, 18 + 32 * 32 * 4))
    toc = open(os.path.join(ADDON, "ChatEmoji.toc"), encoding="utf-8").read()
    for line in toc.splitlines():
        if line and not line.startswith("#"):
            check("toc file exists: " + line, os.path.exists(os.path.join(ADDON, line.strip())), True)
    seen = {}
    dupes = []
    for e in ns.EMOJI.values():
        for c in e[4].values():
            c = u(c)
            if c in seen and seen[c] != u(e[2]):
                dupes.append(c)
            seen[c] = u(e[2])
    check("a shortcode never points at two pictures", dupes, [])

    # emoticons ----------------------------------------------------------------------------
    to("plain", ":)", "<slightly_smiling_face>")
    to("sentence", "hello :) world", "hello <slightly_smiling_face> world")
    to("end", "thanks :D", "thanks <smiley>")
    to("start", ";) see you", "<wink> see you")
    to("dash nose", ":-( sad", "<slightly_frowning_face> sad")
    to("punctuation after", "nice :)!", "nice <slightly_smiling_face>!")
    to("punctuation dots", "ok :P...", "ok <stuck_out_tongue>...")
    to("repeated paren", "great :)))", "great <slightly_smiling_face>")
    to("repeated D", "lol :DDD", "lol <smiley>")
    to("double heart", "<33", "<heart>")
    to("heart", "I <3 you", "I <heart> you")
    to("broken heart", "</3", "<broken_heart>")
    to("xD", "xD XD xd", "<laughing> <laughing> <laughing>")
    to("QQ", "QQ more", "<sob> more")
    to("waves", "o/ \\o \\o/", "<wave> <wave> <raised_hands>")
    to("thumbs", "(y) (n)", "<+1> <-1>")
    to("salute", "o7", "<saluting_face>")
    to("tabs and double spaces", "a\t:)  :(", "a\t<slightly_smiling_face>  <slightly_frowning_face>")
    to("emoticon after colour code", "|cffff0000:)|r", "|cffff0000<slightly_smiling_face>|r")
    to("two in a row", ":) :(", "<slightly_smiling_face> <slightly_frowning_face>")

    # things that must stay text ------------------------------------------------------------
    same("url", "see http://example.com:) for more")
    same("url slashes", "http://x")
    same("list marker 8)", "item (8) and 8) here")
    same("list markers", "A) yes B) no 1) one")
    same("glued to a word", "thanks:)")
    same("emoticon with suffix", ":)x")
    same("xp", "xp XP xP")
    same("time", "Raid at 12:30:15 sharp")
    same("path", "C:/Games/WoW")
    same("plain text", "just a normal sentence, nothing here.")
    same("empty", "")
    same("colon words", "Note:this is fine and :notacode: stays")
    same("copyright trademark", "WoW™ © ®")
    same("arrows", "a → b ↔ c")

    # shortcodes ----------------------------------------------------------------------------
    to("shortcode", ":joy:", "<joy>")
    to("shortcode text around", "that was :joy: really", "that was <joy> really")
    to("shortcode upper case", ":JOY:", "<joy>")
    to("shortcode in brackets", "(:fire:)", "(<fire>)")
    to("two shortcodes glued", ":joy::fire:", "<joy><fire>")
    to("plus one", ":+1:", "<+1>")
    to("minus one", ":-1:", "<-1>")
    to("alias", ":thumbsup:", "<+1>")
    to("extra alias lol", ":lol:", "<joy>")
    to("shortcode after punctuation", "wow!:fire:", "wow!<fire>")
    same("shortcode glued to letters", "aaa:fire:")
    same("unknown shortcode", ":zzzunknown:")
    same("blocked word", ":end: :new: :a:")
    to("unknown then known", ":nope: :fire:", ":nope: <fire>")

    # links and escapes --------------------------------------------------------------------
    item = "|cff1eff00|Hitem:19019::::::::60:::::|h[Thunderfury :) :joy:]|h|r"
    same("item link", item)
    to("link then emoticon", item + " :)", item + " <slightly_smiling_face>")
    to("emoticon then link", ":) " + item, "<slightly_smiling_face> " + item)
    to("shortcode glued after link", item + ":fire:", item + "<fire>")
    same("battle net name", "|Kg12|k :ignored: |k")
    tex = "|TInterface\\Icons\\Foo:16|t"
    same("existing texture", tex + " text")
    same("escaped pipe", "a || b ||:) c")
    same("lone pipe at end", "abc |")
    same("unterminated link", "|Hitem:1|h[broken :)")
    same("short colour code", "|cff")
    to("pipe r then text", "|cff00ff00ok|r :)", "|cff00ff00ok|r <slightly_smiling_face>")

    # real emoji characters ----------------------------------------------------------------
    to("unicode smile", "🙂", "<slightly_smiling_face>")
    to("unicode with text", "hi 🙂 there", "hi <slightly_smiling_face> there")
    to("unicode glued", "yes🔥no", "yes<fire>no")
    to("unicode two", "🙂🙂", "<slightly_smiling_face><slightly_smiling_face>")
    to("heart with selector", "❤️", "<heart>")
    to("heart bare", "❤", "<heart>")
    to("text-style char with selector", "☺️", "<relaxed>")
    same("text-style char alone", "☺")
    to("skin tone", "👍🏽", "<+1>")
    to("sparkles bare", "✨", "<sparkles>")
    same("unknown emoji", "🦄🦄".replace("🦄", "\U0001F9EC"))  # 🧬 is not in the set
    check("unicode switched off", convert("🙂", unicode=False), None)

    # switches -----------------------------------------------------------------------------
    check("emoticons off", convert(":) :joy:", emoticons=False), ":) <joy>")
    check("shortcodes off", convert(":) :joy:", shortcodes=False), "<slightly_smiling_face> :joy:")
    check("size 20", convert(":)", size=20), "<slightly_smiling_face:20>")
    raw = u(ns.Convert(b":)"))
    check("markup uses the media path", raw, "|TInterface\\AddOns\\ChatEmoji\\Media\\1f642.tga:0|t")

    # idempotent: our own output is never converted again
    once = ns.Convert(b":) :joy: \xf0\x9f\x99\x82")
    check("no double conversion", ns.Convert(once), None)

    # cap per message
    many = ns.Convert((":) " * 40).encode())
    check("cap of 30 pictures", (u(many).count("|T"), u(many).endswith(":) " * 10)), (30, True))

    # long message stays fast ------------------------------------------------------------------
    import time
    text = ("lorem ipsum dolor sit amet :) " * 12).encode()
    t = time.perf_counter()
    for _ in range(2000):
        ns.Convert(text)
    per = (time.perf_counter() - t) / 2000 * 1000
    check("a 350 character line converts in under 1 ms", per < 1.0, True)

    # chat filter pipeline ------------------------------------------------------------------
    for ev in ("CHAT_MSG_SAY", "CHAT_MSG_WHISPER", "CHAT_MSG_CHANNEL", "CHAT_MSG_GUILD", "CHAT_MSG_PARTY"):
        discarded, msg, author, *rest = g.Mock.deliver(ev, b"hi :)", b"Bob", b"extra", 7)
        check(ev + " keeps the other arguments", (discarded, u(g.Mock.norm(msg)), u(author), [u(x) if isinstance(x, bytes) else x for x in rest]),
              (False, "hi <slightly_smiling_face>", "Bob", ["extra", 7]))
    discarded, msg, author = g.Mock.deliver("CHAT_MSG_SAY", b"nothing here", b"Bob")
    check("unchanged line passes through", (discarded, u(msg), u(author)), (False, "nothing here", "Bob"))
    check("filters registered", g.Mock.filterCount("CHAT_MSG_SAY"), 1)
    # registering the same callback again never stacks a second filter
    lua.execute('ChatFrameUtil.AddMessageEventFilter("CHAT_MSG_SAY", Mock.ns.Filter)')
    check("no duplicate filter", g.Mock.filterCount("CHAT_MSG_SAY"), 1)
    # switched off
    db.enabled = False
    discarded, msg, author = g.Mock.deliver("CHAT_MSG_SAY", b"x :)", b"Bob")
    check("disabled leaves text alone", u(msg), "x :)")
    db.enabled = True
    # secret strings are left alone and never raise
    g.Mock.secret[b"s :)"] = True
    discarded, msg, author = g.Mock.deliver("CHAT_MSG_SAY", b"s :)", b"Bob")
    check("secret value passes", u(msg), "s :)")
    # non-string message
    check("nil message", ns.Filter(None, "CHAT_MSG_SAY", None), False)
    check("no error recorded", ns.lastError, None)

    # picker window -------------------------------------------------------------------------
    lua.execute('SlashCmdList.CHATEMOJI("")')
    picker = g.ChatEmojiPicker
    check("picker created and shown", picker is not None and picker._shown, True)
    cells = [c for c in picker.cells.values()]
    check("picker has 48 cells", len(cells), 48)
    check("first page is full", all(c._shown for c in cells), True)
    first = cells[0]
    check("cell shows a texture of the addon", u(first.icon._texture).startswith("Interface\\AddOns\\ChatEmoji\\Media\\"), True)
    g.Mock.editBoxActive = False
    first._scripts["OnClick"](first)
    check("click with chat closed does not open chat (gamepad binding taint)", g.Mock.openChatCalls, None)
    check("click with chat closed inserts nothing and says so", (g.Mock.editBox._inserted, "open the chat box first" in u(g.Mock.lines[len(g.Mock.lines)])), (None, True))
    g.Mock.editBoxActive = True
    first._scripts["OnClick"](first)
    check("click with chat open inserts the shortcode", u(g.Mock.editBox._inserted), ":grinning: ")
    check("still no OpenChat call", g.Mock.openChatCalls, None)
    first._scripts["OnEnter"](first)
    check("tooltip names the shortcode", u(g.Mock.tooltip.title), ":grinning:")
    # next page, last page, tabs
    for i in range(1, 6):
        picker.tabs[i]._scripts["OnClick"](picker.tabs[i])
    check("last tab selected", picker.tabs[5].text is not None, True)
    check("page label", u(picker.pageText._text).startswith("1 / "), True)
    # toggle options
    for chk in picker.checks.values():
        key = u(chk.key)
        before = db[key]
        chk._scripts["OnClick"](chk)
        check("checkbox flips " + key, db[key], not before)
        chk._scripts["OnClick"](chk)
        check("checkbox restores " + key, db[key], before)
    # size steps
    g.Mock.editBox._text = ""
    lua.execute('SlashCmdList.CHATEMOJI("size 24")')
    check("/emoji size 24", db.size, 24)
    check("preview uses the new size", b"|T" in g.ChatEmojiPicker.preview._text.encode() if isinstance(g.ChatEmojiPicker.preview._text, str) else b"|T" in g.ChatEmojiPicker.preview._text, True)
    lua.execute('SlashCmdList.CHATEMOJI("size 3")')
    check("/emoji size 3 rejected", db.size, 24)
    lua.execute('SlashCmdList.CHATEMOJI("size 0")')
    check("/emoji size 0 is auto", db.size, 0)
    lua.execute('SlashCmdList.CHATEMOJI("off")')
    check("/emoji off", db.enabled, False)
    lua.execute('SlashCmdList.CHATEMOJI("on")')
    check("/emoji on", db.enabled, True)
    lua.execute('SlashCmdList.CHATEMOJI("test")')
    lua.execute('SlashCmdList.CHATEMOJI("debug")')
    lua.execute('SlashCmdList.CHATEMOJI("help")')
    last = u(g.Mock.lines[len(g.Mock.lines)])
    check("slash commands print", "emoji" in last.lower(), True)
    lua.execute('SlashCmdList.CHATEMOJI("")')
    check("second /emoji hides the window", picker._shown, False)

    # a different load order: saved settings from an older version are completed
    lua2 = new_runtime("ChatEmojiDB = { size = 18 }")
    ns2 = lua2.globals().Mock.ns
    check("saved size kept", ns2.db.size, 18)
    check("missing settings filled in", (ns2.db.enabled, ns2.db.emoticons, ns2.db.shortcodes, ns2.db.unicode), (True, True, True, True))

    # older clients (Classic Era, TBC, Wrath, Cata, Mists) have the global chat functions and no ChatFrameUtil
    lua3 = new_runtime("""
        ChatFrame_AddMessageEventFilter = ChatFrameUtil.AddMessageEventFilter
        ChatEdit_GetActiveWindow = ChatFrameUtil.GetActiveWindow
        ChatFrame_OpenChat = ChatFrameUtil.OpenChat
        ChatFrameUtil = nil
        issecretvalue = nil
        SetShownMissing = nil
    """)
    g3 = lua3.globals()
    check("old client: filter registered through the global function", g3.Mock.filterCount("CHAT_MSG_SAY"), 1)
    discarded, msg, author = g3.Mock.deliver("CHAT_MSG_SAY", b"hi :joy:", b"Bob")
    check("old client: converts", u(g3.Mock.norm(msg)), "hi <joy>")
    lua3.execute('SlashCmdList.CHATEMOJI("")')
    cell = g3.ChatEmojiPicker.cells[1]
    g3.Mock.editBoxActive = True
    cell._scripts["OnClick"](cell)
    check("old client: picker inserts through ChatEdit_GetActiveWindow", u(g3.Mock.editBox._inserted), ":grinning: ")

    print("%d checks, %d failed" % (COUNT, len(FAILS)))
    for label, got, want in FAILS:
        print("FAIL %s\n   got  %r\n   want %r" % (label, got, want))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
