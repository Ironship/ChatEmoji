# Copies the shipped files into the WoW Forever game folder (only the ChatEmoji folder is touched).
$root = Split-Path $PSScriptRoot -Parent
$dst = 'C:\Program Files (x86)\World of Warcraft\_forever_\Interface\AddOns\ChatEmoji'
python -I (Join-Path $root 'tools\package.py') --install $dst
