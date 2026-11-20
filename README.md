# ChatEmoji

Turns emoticons, `:shortcodes:` and real emoji characters in chat into pictures.
For WoW: Forever, Classic Era, TBC Anniversary, Wrath (Titan), Cataclysm, Mists and Retail.

- `:)` becomes 🙂, `<3` a heart, `xD`, `QQ`, `o/`, `o7` and about 140 text emoticons in all
- `:joy:`, `:fire:`, `:+1:` ... 446 pictures from Twemoji
- emoji characters (🙂 ❤️ 👍🏽) that arrive in chat are shown as pictures too
- links, colours and normal text are left alone (`http://x.com:)`, `(8)`, `A)` stay as typed)
- `/emoji` opens a picker: click a picture to put its code in the chat box; switches and picture size

Players without the addon see the plain text you typed. Pictures show in the chat frame, not in
chat bubbles.

Install: extract the ZIP into `Interface/AddOns` (the folder must be called `ChatEmoji`).

Pictures: [Twemoji](https://github.com/jdecked/twemoji), CC-BY 4.0 (see CREDITS.txt). Code: GPL-3.0.

## Development

- `python tools/build_assets.py` downloads the artwork and writes `Media/*.tga` and `Data.lua`
- `python tools/test_addon.py` runs the addon on a mock client (needs `pip install lupa`)
- `python tools/render_mock.py` draws an HTML preview of chat and picker from the real code
- `python tools/package.py --check | --zip dist | --install <AddOns\ChatEmoji>`
- CurseForge builds from this repository through a push webhook; `.pkgmeta` says what is left out
