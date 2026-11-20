"""Which emoji ChatEmoji ships.

Every name is a gemoji alias (https://github.com/github/gemoji). The "faces" group takes the whole
"Smileys & Emotion" category from gemoji, the other groups are hand picked for what people type in
game chat. Add a name here and run `python tools/build_assets.py` to ship one more picture.
"""

# group id -> (picker label, list of aliases or "ALL:<gemoji category>")
GROUPS = [
    ("faces", "Faces", "ALL:Smileys & Emotion"),
    ("hands", "Hands", [
        "wave", "raised_hand", "ok_hand", "v", "crossed_fingers", "metal", "call_me_hand",
        "point_left", "point_right", "point_up_2", "point_down", "+1", "-1", "fist_raised",
        "fist_oncoming", "clap", "raised_hands", "open_hands", "handshake", "pray", "muscle",
        "eyes", "brain", "facepalm", "shrug", "bow", "no_good", "ok_woman", "raising_hand",
        "speaking_head", "ninja", "mage", "vampire", "zombie", "angel", "santa", "fairy",
        "dancers", "runner", "man_dancing", "woman_dancing", "footprints", "bone", "tooth",
    ]),
    ("nature", "Nature", [
        "dog", "cat", "mouse", "hamster", "rabbit", "fox_face", "bear", "panda_face", "koala",
        "tiger", "lion", "cow", "pig", "frog", "monkey", "chicken", "penguin", "bird", "duck",
        "eagle", "owl", "bat", "wolf", "boar", "horse", "unicorn", "bee", "bug", "butterfly",
        "snail", "turtle", "snake", "dragon_face", "dragon", "t-rex", "sauropod", "whale",
        "dolphin", "fish", "tropical_fish", "octopus", "crab", "shark", "spider", "scorpion",
        "four_leaf_clover", "cactus", "mushroom", "rose", "sunflower", "cherry_blossom",
        "maple_leaf", "fallen_leaf", "evergreen_tree", "deciduous_tree", "palm_tree",
        "seedling", "herb", "sunny", "cloud", "umbrella", "snowflake", "zap", "fire",
        "rainbow", "ocean", "earth_africa", "full_moon", "crescent_moon", "star", "star2",
        "sparkles", "comet", "dizzy",
    ]),
    ("food", "Food", [
        "apple", "green_apple", "banana", "grapes", "strawberry", "cherries", "peach",
        "watermelon", "lemon", "avocado", "tomato", "carrot", "corn", "hot_pepper", "bread",
        "cheese", "egg", "bacon", "hamburger", "fries", "pizza", "hotdog", "taco", "burrito",
        "sushi", "ramen", "spaghetti", "cake", "birthday", "cookie", "chocolate_bar", "candy",
        "lollipop", "doughnut", "ice_cream", "popcorn", "coffee", "tea", "beer", "beers",
        "wine_glass", "cocktail", "tropical_drink", "champagne", "milk_glass", "meat_on_bone",
        "poultry_leg", "cut_of_meat", "pretzel", "croissant", "bowl_with_spoon", "stew",
    ]),
    ("things", "Things", [
        "tada", "confetti_ball", "balloon", "gift", "trophy", "medal_sports", "crown", "gem",
        "moneybag", "dollar", "key", "lock", "unlock", "bell", "bomb", "dagger", "crossed_swords",
        "shield", "bow_and_arrow", "hammer", "wrench", "gear", "pick", "axe", "crystal_ball",
        "scroll", "book", "books", "memo", "pencil2", "bulb", "mag", "hourglass", "watch",
        "alarm_clock", "rocket", "airplane", "car", "bike", "ship", "anchor", "house", "european_castle",
        "tent", "joystick", "video_game", "game_die", "dart", "bowling", "soccer", "basketball",
        "football", "tennis", "8ball", "guitar", "microphone", "headphones", "musical_note",
        "notes", "drum", "trumpet", "computer", "keyboard", "iphone", "camera", "tv",
        "movie_camera", "phone", "email", "package", "checkered_flag", "triangular_flag_on_post",
        "white_flag", "pirate_flag", "skull_and_crossbones", "test_tube", "pill", "syringe",
        "100", "warning", "no_entry_sign", "x", "white_check_mark", "heavy_check_mark",
        "question", "exclamation", "bangbang", "interrobang", "sos", "ok", "cool", "infinity",
        "recycle", "arrow_up", "arrow_down", "arrow_left", "arrow_right", "red_circle",
        "large_blue_circle", "green_circle", "yellow_circle", "orange_circle", "purple_circle",
        "black_circle", "white_circle", "red_square", "blue_square", "green_square",
        "heavy_plus_sign", "heavy_minus_sign", "copyright", "tm", "registered",
    ]),
]

# Shortcodes that would turn ordinary words into pictures (":end:", ":new:" ...) are left out.
# They are dropped from the alias list of every emoji before the data file is written.
BLOCKED_ALIASES = {
    "a", "b", "o", "m", "o2", "ab", "id", "on", "end", "up", "new", "top", "free", "soon",
    "back", "cl", "ng", "vs", "sa", "wc", "atm", "abc", "abcd", "tm", "sos",
}

# Shortcodes that are not in gemoji but people type (Discord, Slack, WoW chat).
EXTRA_ALIASES = {
    "joy": ["lol"],
    "sob": ["qq"],
    "skull": ["dead"],
    "clap": ["applause"],
}
