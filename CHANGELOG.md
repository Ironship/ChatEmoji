# Changelog

## 0.2.0

- Chat bubbles above characters show the pictures too. A short time after a say, yell, emote, party or NPC chat event the visible bubbles are read and their text goes through the same converter as the chat lines. Switch: "Chat bubbles" in `/emoji` or `/emoji bubbles on|off`.

State: checked on the mock client only. It has not been tried in the game: whether the bubble of the client resizes around the picture, and whether the bubbles of WoW: Forever are reachable through `C_ChatBubbles.GetAllChatBubbles` at all, is still to be seen.

## 0.1.1

- Fixed: the `/emoji` picker no longer opens the chat box itself. With the gamepad interface that ran Blizzard's chat focus code in this addon's execution and could later be reported as `ADDON_ACTION_FORBIDDEN` for `SetPreferredGamepadInteractTarget()` when a panel (for example the game menu) was closed. A click now only puts the code into a chat box that is already open, otherwise it asks you to open chat first.

State: the cause was found by reading Blizzard's code and the mock client checks that the picker never opens chat; it has not been confirmed in the game yet.

## 0.1.0

First release.

- Emoticons in chat become pictures: `:)` `:D` `;)` `:P` `:(` `:'(` `<3` `</3` `xD` `QQ` `o/` `o7` and about 130 more. A repeated last character is fine (`:)))`), and so is punctuation after it (`:)!`).
- `:shortcodes:` such as `:joy:`, `:fire:`, `:+1:`, 446 pictures in all (Twemoji, CC-BY 4.0).
- Real emoji characters that arrive in chat are shown as pictures as well.
- Hyperlinks, colours and ordinary text are left alone: `http://x.com:)`, `(8)`, `A)` and `xp` stay as typed.
- `/emoji` opens a picker (click a picture to put its code in the chat box), switches for emoticons, shortcodes and emoji characters, and the picture size (`/emoji size 20`, 0 = height of the chat font).
- Works for say, yell, emote, party, raid, instance, guild, officer, whisper, Battle.net whisper, channels and communities.
- The TOC lists Interface numbers for Classic Era, TBC Anniversary, Wrath (Titan), Cataclysm, Mists, Retail and WoW: Forever.

State: the chat conversion was seen working in WoW: Forever. The `/emoji` window and the other game versions have not been tried yet; they run the same code (a fallback is used where an API differs).
