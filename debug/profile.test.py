import re

def check(text):
    items = [
        r"\*?\*?Name:\*?\*?:? (?:.*)",
        r"\*?\*?Pronouns:\*?\*?:? (?:.*)",
        r"\*?\*?Timezone:\*?\*?:? (?:.*)",
        r"\*?\*?Availability:\*?\*?:? (?:.*)",
        r"\*?\*?Preferred Character Age:\*?\*?:? (\d+)\+?!?",
        r"\*?\*?Preferred Writer Age:\*?\*?:? (\d+)\+?!?",
        r"\*?\*?Preferred Genres:\*?\*?:? (?:(?:\n\*? .*)*)",
        r"\*?\*?Preferred Character Gender Pairings:\*?\*?:? (?:.*)",
        r"\*?\*?Preferred Writer Gender:\*?\*?:? (?:.*)",
        r"\*?\*?Preferred Point of View:\*?\*?:? (?:.*)",
        r"\*?\*?Average writing length\*?\*?:? (?:.*)",
        r"\*?\*?NSFW or SFW\?\*?\*?:? (?:.*)"
    ]

    for item in items:
        match = re.search(item, text)
        if match is None:
            return f"no match at {item}"
    character_age = int(re.search(r"\*?\*?Preferred Character Age:\*?\*?:? (\d+)\+?!?", text, re.DOTALL).group(1))
    writer_age = int(re.search(r"\*?\*?Preferred Writer Age:\*?\*?:? (\d+)\+?!?", text, re.DOTALL).group(1))

    if character_age < 18 or writer_age < 18:
        return "under 18"

    return "match"

test1 = """Name: Kate
Pronouns: She/Her
Timezone: PST
Availability: Flexible do to life, but mostly free
Preferred Character Age: 18+
Preferred Writer Age: 18+
Preferred Genres: Romance, Adventure, Post-Apocalyptic, Modern, Alternate Universes,Fantasy, Supernatural, Horror, Scifi, and Action. But I generally love to try out anything as long as the plot is interesting! 
Fandoms: I can’t exactly list them all correctly since usually with cases like this, I like to RP with a certain number of canon males from the fandoms I like. I even have a list of them I could share and such if requested. Some with even AU options.
Preferred Character Gender Pairings: MxF
Preferred Writer Gender: Female
Preferred Point of View: Third person
Average writing length: Multi Paragraph
NSFW or SFW? Both (60/40)"""
try:
    assert check(test1) == "match"
    print("test1 passed")
except AssertionError:
    print(f"test1 failed: {test1}")

test2 = """**Name:** Noor!
**Pronouns:** She/Her. 
**Timezone:** GMT+1.
**Availability:** Available most days. Will let you know when I’m free. 
**Preferred Character Age:** 21+!
**Preferred Writer Age:** 21+!
**Preferred Genres:** Mainly Romance! Don’t mind other genres added in, such as sci-fi, fantasy, and apocalyptic. 
**Preferred Character Gender Pairings:** FxM. 
**Preferred Writer Gender:** Male. 
**Preferred Point of View:** 1st Person. 
**Average writing length**: At least one paragraph or more.
**NSFW or SFW?** Mainly sfw! Don’t mind nsfw added in, but that depends and will have to be discussed."""
try:
    assert check(test2) == "match"
    print("test2 passed")
except AssertionError:
    print(f"test2 failed: {test2}")

test3 = """**Name:** Miss Undutchable
**Pronouns:** She/her
**Timezone:** CET
**Availability:** Flexible, check my status
**Preferred Character Age:** 18+
**Preferred Writer Age:** 30+
**Preferred Genres:** Romance, Angst, Supernatural, (Medieval) Fantasy, Modern Fantasy, Slice of Life, Mafia, Darker themes
**Fandoms:** TWD, Twilight, LotR, Cyberpunk (only OCxOC)
**Preferred Character Gender Pairings:**F x M (myself as F)
**Preferred Writer Gender:** No preference
**Preferred Point of View:** 3rd person, past tense
**Average writing length:** At least one good paragraph (can do multi on openers and depending on how motivated and inspired I am)
**NSFW or SFW?** NSFW but only with good story and not dragged out over multiple posts. If you make me write multiple posts doing the same thing in one encounter, I will quickly lose interest.
"""
try:
    result = check(test3)
    assert result == "match"
    print("test3 passed")
except AssertionError:
    print(f"test3 failed: {result}")
