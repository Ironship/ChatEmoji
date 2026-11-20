"""Draws what the addon does as an HTML page, using the REAL addon code on the mock client.

    python tools/render_mock.py            writes tools/mock/chat-mock.html

Chat lines go through the same filter registry the game uses, the picker window is read back from
the mock frames after /emoji ran, so the page shows behaviour, not a separate re-implementation.
"""
import html
import os
import re
import sys

from lupa import lua51

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADDON = ROOT
PNG = os.path.join(ROOT, "tools", "cache", "png").replace("\\", "/")
OUT = os.path.join(ROOT, "tools", "mock", "chat-mock.html")

lua = lua51.LuaRuntime(unpack_returned_tuples=True)
lua.execute(open(os.path.join(ROOT, "tools", "mock", "wowstub.lua"), encoding="utf-8").read())
lua.execute("Mock.load(%r)" % ADDON.replace("\\", "/"))
g = lua.globals()
ns = g.Mock.ns


def s(x):
    return x.decode("utf-8") if isinstance(x, bytes) else x


TOKEN = re.compile(r"\|c([0-9a-fA-F]{8})|\|r|\|H[^|]*\|h|\|h|\|T([^:|]*):(\d+)[^|]*\|t|\|\|")


def wow_html(text, font=14):
    """WoW escape codes -> HTML. Handles colour, hyperlinks, textures and the escaped pipe."""
    out, pos, colours, links = [], 0, 0, 0
    for m in TOKEN.finditer(text):
        out.append(html.escape(text[pos:m.start()]))
        pos = m.end()
        tok = m.group(0)
        if tok.startswith("|c"):
            out.append('<span style="color:#%s">' % m.group(1)[2:])
            colours += 1
        elif tok == "|r":
            out.append("</span>" * colours)
            colours = 0
        elif tok.startswith("|H"):
            out.append('<span class="lnk">')
            links += 1
        elif tok == "|h":
            if links:
                out.append("</span>")
                links -= 1
        elif tok.startswith("|T"):
            name = os.path.splitext(os.path.basename(m.group(2).replace("\\", "/")))[0]
            size = int(m.group(3)) or font
            out.append('<img class="e" src="%s/%s.png" height="%d">' % (PNG, name, size))
        elif tok == "||":
            out.append("|")
    out.append(html.escape(text[pos:]))
    out.append("</span>" * (colours + links))
    return "".join(out)


FORMATS = {
    "CHAT_MSG_SAY": ("#ffffff", "{a} says: {m}"),
    "CHAT_MSG_YELL": ("#ff4040", "{a} yells: {m}"),
    "CHAT_MSG_PARTY": ("#aaaaff", "[Party] [{a}]: {m}"),
    "CHAT_MSG_RAID": ("#ff7f00", "[Raid] [{a}]: {m}"),
    "CHAT_MSG_GUILD": ("#40ff40", "[Guild] [{a}]: {m}"),
    "CHAT_MSG_WHISPER": ("#ff80ff", "[{a}] whispers: {m}"),
    "CHAT_MSG_CHANNEL": ("#ffc0c0", "[2. Trade] [{a}]: {m}"),
}

THUNDER = "|cffff8000|Hitem:19019::::::::60:::::|h[Thunderfury, Blessed Blade of the Windseeker]|h|r"
CHAT = [
    ("CHAT_MSG_GUILD", "Thrall", "gg everyone :D that boss was easy <3"),
    ("CHAT_MSG_PARTY", "Jaina", "brb 2 min :) need a coffee :coffee:"),
    ("CHAT_MSG_RAID", "Arthas", THUNDER + " dropped!! :fire: :fire: :tada:"),
    ("CHAT_MSG_WHISPER", "Sylvanas", "thanks for the carry :pray: o7"),
    ("CHAT_MSG_SAY", "Baine", "o/ hello everybody ^_^"),
    ("CHAT_MSG_YELL", "Garrosh", ">:( wipe again?? QQ"),
    ("CHAT_MSG_CHANNEL", "Rexxar", "WTS " + THUNDER + " 500g :moneybag:"),
    ("CHAT_MSG_GUILD", "Thrall", "xD that was close :sweat_smile: \U0001F642 \u2764\ufe0f"),
    ("CHAT_MSG_PARTY", "Jaina", "dps check :skull: :+1: :eyes:"),
]
CHAT_HTML = []
for ev, author, text in CHAT:
    color, fmt = FORMATS[ev]
    discarded, msg, who = g.Mock.deliver(ev, text.encode("utf-8"), author.encode("utf-8"))
    CHAT_HTML.append('<div style="color:%s">%s</div>' % (color, wow_html(fmt.format(a=s(who), m=s(msg)))))

RULES = [
    (":)  :-)  =)  :]", "smile"),
    (":D  xD  :'D  :')", "grin, laugh, joy, tear"),
    (";)  :P  ;P", "wink / tongue"),
    (":(  :'(  T_T  QQ", "sad / cry / sob"),
    ("<3  </3  :*  B-)", "heart, kiss, cool"),
    ("o/  \\o/  o7  (y)", "wave, salute, thumbs up"),
    (":joy:  :fire:  :+1:  :skull:", "shortcodes"),
    ("\U0001F642 \u2764\ufe0f \U0001F44D\U0001F3FD", "real emoji characters"),
]
NEGATIVE = [
    "http://example.com:)",
    "item (8) and A) B)",
    "xp XP thanks:)",
    "WoW\u2122 \u00a9 a \u2192 b",
    ":notacode: :end:",
    "|Hitem:1|h[Sword :)]|h link",
]


def conv(text):
    r = ns.Convert(text.encode("utf-8"))
    return s(r) if r else text


rules_html = "".join(
    "<tr><td class=t>%s</td><td>%s</td><td class=n>%s</td></tr>"
    % (html.escape(t), wow_html(conv(t)), html.escape(n)) for t, n in RULES)
neg_html = "".join(
    "<tr><td class=t>%s</td><td>%s</td></tr>"
    % (html.escape(t), wow_html(conv(t))) for t in NEGATIVE)

# picker window, read back from the mock frames ---------------------------------------------------
lua.execute('SlashCmdList.CHATEMOJI("")')
p = g.ChatEmojiPicker
cells = []
for i in sorted(p.cells.keys()):
    c = p.cells[i]
    if c._shown:
        name = os.path.splitext(os.path.basename(s(c.icon._texture).replace("\\", "/")))[0]
        cells.append('<img src="%s/%s.png">' % (PNG, name))
tabs = "".join('<span class="tab%s">%s</span>' % (" on" if i == 1 else "", html.escape(s(p.tabs[i].text._text)))
               for i in sorted(p.tabs.keys()))
checks = "".join(
    '<div class="ck"><i class="%s"></i>%s</div>' % ("on" if p.checks[i].mark._shown else "", html.escape(s(p.checks[i].label._text)))
    for i in sorted(p.checks.keys()))
picker_html = (
    '<div class="pk"><div class="pt">ChatEmoji</div><div class="tabs">%s</div><div class="grid">%s</div>'
    '<div class="pg">&lt;&nbsp;&nbsp;%s&nbsp;&nbsp;&gt;</div><div class="cks">%s</div>'
    '<div class="sz">Size in chat &nbsp;[-] %s [+]</div><div class="pv">%s</div></div>'
    % (tabs, "".join(cells), html.escape(s(p.pageText._text)), checks, html.escape(s(p.sizeText._text)),
       wow_html(s(p.preview._text))))

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
:root{color-scheme:dark light}
html,body{margin:0}
body{font-family:var(--font-sans);font-size:13px;color:var(--foreground)}
h2{font-size:13px;margin:18px 0 6px;font-weight:600}
.chat{background:#0c0c10;border:1px solid #333;border-radius:var(--radius);padding:12px 16px;font:14px/1.45 Arial,sans-serif;color:#fff}
.chat img.e{vertical-align:-3px}
.lnk{text-decoration:none}
.cols{display:grid;grid-template-columns:minmax(0,1fr) 298px;gap:12px;align-items:start}
table{border-collapse:collapse;font-size:13px}
td{padding:3px 12px 3px 0;vertical-align:middle;white-space:nowrap}
td.t{font-family:var(--font-mono);color:var(--muted-foreground,#999);white-space:nowrap}
td.n{color:var(--muted-foreground,#999);font-size:12px}
td img.e{vertical-align:-3px}
.box{background:#0c0c10;border-radius:var(--radius);padding:10px 14px;color:#fff;font:14px Arial,sans-serif}
.box td.t{color:#aaa}
.pk{width:272px;background:#0d0d12;border:1px solid #66666f;padding:12px;color:#ddd;font:12px Arial,sans-serif}
.pt{color:#ffd100;font-size:14px;margin-bottom:6px}
.tabs{display:flex;gap:2px;margin-bottom:4px}
.tab{background:#292933;padding:3px 0;width:52px;text-align:center;color:#bbb}
.tab.on{color:#ffd100}
.grid{display:grid;grid-template-columns:repeat(8,34px);width:272px}
.grid img{width:26px;height:26px;margin:4px}
.pg{text-align:center;margin:4px 0 8px}
.cks{display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-bottom:6px}
.ck{display:flex;align-items:center;gap:6px}
.ck i{width:14px;height:14px;background:#4d4d5c;display:inline-block;position:relative}
.ck i.on::after{content:"";position:absolute;inset:3px;background:#ffd100}
.sz{margin-bottom:8px}
.pv{font-size:14px;line-height:20px}
.pv img.e{vertical-align:-3px}
</style></head><body>
<h2>In the chat window</h2>
<div class="chat">%(chat)s</div>
<div class="cols">
<div>
<h2>You type, the chat shows</h2>
<div class="box"><table>%(rules)s</table></div>
<h2>Left as text on purpose</h2>
<div class="box"><table>%(neg)s</table></div>
</div>
<div><h2>/emoji</h2>%(picker)s</div>
</div></body></html>"""

doc = PAGE % dict(chat="".join(CHAT_HTML), rules=rules_html, neg=neg_html, picker=picker_html)
open(OUT, "w", encoding="utf-8").write(doc)
print("wrote", OUT, len(doc), "bytes")
