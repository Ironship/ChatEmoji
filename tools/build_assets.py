"""Build the picture files and Data.lua of the ChatEmoji addon.

    python tools/build_assets.py

* downloads gemoji (names, MIT) and Twemoji artwork (CC-BY 4.0, jdecked/twemoji) into tools/cache
* converts every picture to a 32x32 uncompressed 32-bit TGA (what the WoW client reads) in
  Media/<hex codepoints>.tga
* writes Data.lua (name, file, UTF-8 character, shortcodes, group)

Re-running only fetches what is missing from the cache.
"""
import json
import os
import shutil
import struct
import sys
import urllib.request

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "tools", "cache")
ADDON = ROOT
MEDIA = os.path.join(ADDON, "Media")
SIZE = 32

sys.path.insert(0, os.path.join(ROOT, "tools"))
from emoji_list import BLOCKED_ALIASES, EXTRA_ALIASES, GROUPS  # noqa: E402

GEMOJI_URL = "https://raw.githubusercontent.com/github/gemoji/master/db/emoji.json"
TWEMOJI_URL = "https://raw.githubusercontent.com/jdecked/twemoji/main/assets/72x72/{}.png"
LICENSE_URL = "https://raw.githubusercontent.com/jdecked/twemoji/main/LICENSE-GRAPHICS"
EMOJI_DATA_URL = "https://www.unicode.org/Public/16.0.0/ucd/emoji/emoji-data.txt"
# Typed on its own (no variation selector) these still count as an emoji for people.
ALWAYS_EMOJI = {0x2764}


def fetch(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ChatEmoji-build"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
    except Exception:
        return False
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        f.write(data)
    return True


def codepoints(char):
    return [ord(c) for c in char]


def twemoji_name(char):
    """Twemoji names files by codepoints joined with '-', usually without the FE0F selector."""
    cps = codepoints(char)
    stripped = [c for c in cps if c != 0xFE0F]
    return ["-".join("%x" % c for c in stripped), "-".join("%x" % c for c in cps)]


def bleed_colour(rgb, alpha):
    """Spread the colour of the edge into fully transparent pixels so bilinear filtering in the
    game does not pull a dark fringe in from them."""
    have = alpha > 0
    rgb = rgb.astype(np.float32)
    for _ in range(8):
        if have.all():
            break
        acc = np.zeros_like(rgb)
        cnt = np.zeros(have.shape, np.float32)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)):
            m = np.roll(have, (dy, dx), (0, 1)) & ~have
            acc += np.roll(rgb, (dy, dx), (0, 1)) * m[..., None]
            cnt += m
        new = cnt > 0
        rgb[new] = acc[new] / cnt[new][:, None]
        have = have | new
    return rgb


def png_to_tga(png_path, tga_path):
    im = Image.open(png_path).convert("RGBA")
    arr = np.array(im)
    rgb = bleed_colour(arr[..., :3], arr[..., 3])
    rgb_img = Image.fromarray(np.clip(rgb + 0.5, 0, 255).astype(np.uint8))
    a_img = Image.fromarray(arr[..., 3])
    rgb_s = np.array(rgb_img.resize((SIZE, SIZE), Image.LANCZOS))
    a_s = np.array(a_img.resize((SIZE, SIZE), Image.LANCZOS))
    bgra = np.dstack([rgb_s[..., 2], rgb_s[..., 1], rgb_s[..., 0], a_s]).astype(np.uint8)
    bgra = bgra[::-1]  # TGA rows run bottom to top (origin bottom-left, like Photoshop writes)
    header = struct.pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, SIZE, SIZE, 32, 8)
    with open(tga_path, "wb") as f:
        f.write(header)
        f.write(bgra.tobytes())


def emoji_presentation(path):
    """Codepoints a font draws as a picture by default (Emoji_Presentation=Yes)."""
    cps = set()
    for line in open(path, encoding="utf-8"):
        if "; Emoji_Presentation" not in line:
            continue
        rng = line.split(";")[0].strip()
        lo, _, hi = rng.partition("..")
        cps.update(range(int(lo, 16), int(hi or lo, 16) + 1))
    return cps


def lua_string(s):
    return '"' + "".join("\\%d" % b if (b > 126 or b < 32 or chr(b) in '"\\') else chr(b)
                         for b in s.encode("utf-8")) + '"'


def pick_aliases(aliases):
    ok = [a for a in aliases if a.isascii() and a.replace("_", "").replace("-", "").isalnum()
          or a in ("+1", "-1")]
    return [a for a in ok if a not in BLOCKED_ALIASES]


def main():
    gem_path = os.path.join(CACHE, "gemoji.json")
    if not fetch(GEMOJI_URL, gem_path):
        sys.exit("cannot download gemoji")
    fetch(LICENSE_URL, os.path.join(CACHE, "LICENSE-GRAPHICS"))
    gem = json.load(open(gem_path, encoding="utf-8"))
    by_alias = {}
    for e in gem:
        for a in e["aliases"]:
            by_alias[a] = e

    ep_path = os.path.join(CACHE, "emoji-data.txt")
    if not fetch(EMOJI_DATA_URL, ep_path):
        sys.exit("cannot download emoji-data.txt")
    presentation = emoji_presentation(ep_path)

    os.makedirs(MEDIA, exist_ok=True)
    chosen, seen = [], set()
    missing = []
    for gid, _label, spec in GROUPS:
        if isinstance(spec, str):
            cat = spec.split(":", 1)[1]
            entries = [e for e in gem if e["category"] == cat]
        else:
            entries = []
            for name in spec:
                if name in by_alias:
                    entries.append(by_alias[name])
                else:
                    missing.append(name)
        for e in entries:
            if e["emoji"] in seen:
                continue
            seen.add(e["emoji"])
            chosen.append((gid, e))

    rows, skipped = [], []
    for gid, e in chosen:
        names = twemoji_name(e["emoji"])
        png = None
        for n in names:
            p = os.path.join(CACHE, "png", n + ".png")
            if fetch(TWEMOJI_URL.format(n), p):
                png, fname = p, names[0]
                break
        if not png:
            skipped.append(e["aliases"][0])
            continue
        canonical = os.path.join(CACHE, "png", fname + ".png")
        if png != canonical:  # Twemoji kept the FE0F in this file name; the mock looks up ours
            shutil.copyfile(png, canonical)
        png_to_tga(png, os.path.join(MEDIA, fname + ".tga"))
        aliases = pick_aliases(e["aliases"])
        if not aliases:
            aliases = [e["aliases"][0]]
        for primary, extra in EXTRA_ALIASES.items():
            if primary in e["aliases"]:
                aliases += [x for x in extra if x not in aliases]
        key = e["emoji"].replace("️", "")
        first = ord(key[0])
        # a sequence (ZWJ ...) is unambiguous; a single character needs a picture-by-default
        # codepoint, otherwise the client only converts it when a variation selector follows.
        bare = len(key) > 1 or first in presentation or first in ALWAYS_EMOJI
        rows.append((gid, aliases, fname, key, e["description"], bare))

    labels = [(gid, label) for gid, label, _ in GROUPS]
    out = ["-- Generated by tools/build_assets.py, do not edit by hand.",
           "-- Pictures: Twemoji (c) Twitter, Inc. and other contributors, CC-BY 4.0.",
           "local _, ns = ...", "", "ns.GROUPS = {"]
    for gid, label in labels:
        out.append('\t{ id = "%s", label = "%s" },' % (gid, label))
    out += ["}", "",
            "-- { group, file, character (no FE0F), { shortcodes... }, picture-by-default }",
            "ns.EMOJI = {"]
    for gid, aliases, fname, char, desc, bare in rows:
        codes = ", ".join('"%s"' % a for a in aliases)
        out.append('\t{ "%s", "%s", %s, { %s }, %s }, -- %s' % (
            gid, fname, lua_string(char), codes, "true" if bare else "false",
            desc.replace("\n", " ")))
    out += ["}", ""]
    with open(os.path.join(ADDON, "Data.lua"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out))

    size = sum(os.path.getsize(os.path.join(MEDIA, f)) for f in os.listdir(MEDIA))
    print("%d emoji written, %d KB of TGA" % (len(rows), size // 1024))
    if missing:
        print("names not in gemoji:", ", ".join(missing))
    if skipped:
        print("no Twemoji file for:", ", ".join(skipped))


if __name__ == "__main__":
    main()
