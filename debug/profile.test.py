import re


def check(text):
    items = [
        r"\*?\*?Name:?\*?\*?:?(?:.*)",
        r"\*?\*?Pronouns:?\*?\*?:?(?:.*)",
        r"\*?\*?Timezone:?\*?\*?:?(?:.*)",
        r"\*?\*?Availability:?\*?\*?:?(?:.*)",
        r"\*?\*?Preferred Genres:?\*?\*?:?(?:(?:\n\*? .*)*)",
        r"\*?\*?Preferred Character Gender Pairings:?\*?\*?:?(?:.*)",
        r"\*?\*?Preferred Writer Gender:?\*?\*?:?(?:.*)",
        r"\*?\*?Preferred Point of View:?\*?\*?:?(?:.*)",
        r"\*?\*?Average writing length:?\*?\*?:?(?:.*)",
        r"\*?\*?NSFW or SFW\??\*?\*?:?(?:.*)"
    ]
    ages = [
        r"\*?\*?Preferred Character Age:?\*?\*?:?\s*(\d+).{,3}?\n",
        r"\*?\*?Preferred Writer Age:?\*?\*?:?\s*(\d+).{,3}?\n",
    ]
    items = items + ages
    for item in items:
        match = re.search(item, text)
        if match is None:
            return f"no match at {item}"
    character_age = int(re.search(ages[0], text, re.DOTALL).group(1))
    writer_age = int(re.search(ages[1], text, re.DOTALL).group(1))
    if not character_age or not writer_age:
        return "no match at age"
    if character_age < 18 or writer_age < 18:
        return "under 18"

    return "match"


def run_test(test, testname, expected_result="match"):
    result = check(test)
    try:
        assert result == expected_result
        print(f"{testname} passed")
    except AssertionError:
        print(f"{testname} failed: {result}")


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
run_test(test1, "test1")

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
run_test(test2, "test2")

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
run_test(test3, "test3")
test4 = """**Name:** Miss Undutchable
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
"""
run_test(test4, "test4", "no match at \*?\*?NSFW or SFW\??\*?\*?:?(?:.*)")
test5 = """**Name:** Miss Undutchable
**Pronouns:** She/her
**Timezone:** CET
**Availability:** Flexible, check my status
**Preferred Character Age:** 12+
**Preferred Writer Age:** 30+
**Preferred Genres:** Romance, Angst, Supernatural, (Medieval) Fantasy, Modern Fantasy, Slice of Life, Mafia, Darker themes
**Fandoms:** TWD, Twilight, LotR, Cyberpunk (only OCxOC)
**Preferred Character Gender Pairings:**F x M (myself as F)
**Preferred Writer Gender:** No preference
**Preferred Point of View:** 3rd person, past tense
**Average writing length:** At least one good paragraph (can do multi on openers and depending on how motivated and inspired I am)
**NSFW or SFW?** NSFW but only with good story and not dragged out over multiple posts. If you make me write multiple posts doing the same thing in one encounter, I will quickly lose interest.
"""
run_test(test5, "test5", "under 18")

test6 = """**Name**: Angelina 
**Pronouns**: she/her
**Timezone**: eastern daylight time
**Availability**: pretty much 24/7 
**Preferred Character Age**:  18+
**Preferred Writer Age**: 18 but no older then 30
**Preferred Genres**: Fantasy (medieval or modern), slice of life, supernatural 
• Genre - Pairings: N/A
**Fandoms**: dont really have any 
• Fandom - Pairings: N/A
**Preferred Character Gender Pairings**: male and female 
**Preferred Writer Gender**: M
**Preferred Point of View**: first person
**Average writing length**: at least 7-10 sentences long- i like very detailed rp 
**NSFW or SFW**?- both depending on how the story goes"""

run_test(test6, "test6", r"no match at \*?\*?Preferred Writer Age:?\*?\*?:?\s*(\d+).{,3}?\n")

test7 = """**Name:** dëamon
**Pronouns:** he/him
**Timezone:** cet/cest
**Availability:**
**Preferred Character Age:** around 20-23
**Preferred Writer Age:** 18-27
**Preferred Genres:** slice of life, modern, comedy, romance 

**Fandoms:** not any in particular 
**Preferred Character Gender Pairings:** m/a
**Preferred Writer Gender:** doesn’t matter
**Preferred Point of View:** 3rd person, present 
**Average writing length**: I’m more of a short writer 
**NSFW or SFW?**
both is okay
"""

run_test(test7, "test7", r"no match at \*?\*?Preferred Character Age:?\*?\*?:?\s*(\d+).{,3}?\n")

test8 = """**Name:** tony chestnut
**Pronouns:** she/they/he
**Timezone:** pst
**Availability:** never, go away 
**Preferred Character Age:** 20+
**Preferred Writer Age:** 20+
**Preferred Genres:** fantasy, furry, drama, etc.
**Fandoms:** marvel, trigun, hades, some other things
**Preferred Character Gender Pairings:** m/m and f/f please
**Preferred Writer Gender:** who cares
**Preferred Point of View:** 3rd person present or past 
**Average writing length**: 3 - 10 paragraphs, depending
**NSFW or SFW?** either or
"""

run_test(test8, "test8")

test9 = """**Name:** tony chestnut
**Pronouns:** she/they/he
**Timezone:** pst
**Availability:** never, go away 
**Preferred Character Age:** immortal or adults
**Preferred Writer Age:** 20+
**Preferred Genres:** fantasy, furry, drama, etc.
**Fandoms:** marvel, trigun, hades, some other things
**Preferred Character Gender Pairings:** m/m and f/f please
**Preferred Writer Gender:** who cares
**Preferred Point of View:** 3rd person present or past 
**Average writing length**: 3 - 10 paragraphs, depending
**NSFW or SFW?** either or"""

run_test(test9, "test9", r"no match at \*?\*?Preferred Character Age:?\*?\*?:?\s*(\d+).{,3}?\n")

test10 = """**Name:** tony chestnut
**Pronouns:** she/they/he
**Timezone:** pst
**Availability:** never, go away 
**Preferred Character Age:** 20+ except for when someone's peegnat
**Preferred Writer Age:** 20+
**Preferred Genres:** fantasy, furry, drama, etc.
**Fandoms:** marvel, trigun, hades, some other things
**Preferred Character Gender Pairings:** m/m and f/f please
**Preferred Writer Gender:** who cares
**Preferred Point of View:** 3rd person present or past 
**Average writing length**: 3 - 10 paragraphs, depending
**NSFW or SFW?** either or"""

run_test(test10, "test10", r"no match at \*?\*?Preferred Character Age:?\*?\*?:?\s*(\d+).{,3}?\n")

test11 = """**Name:** tony chestnut
**Pronouns:** she/they/he
**Timezone:** pst
**Availability:** never, go away 
**Preferred Character Age:** 20+
**Preferred Writer Age:** who cares
**Preferred Genres:** fantasy, furry, drama, etc.
**Fandoms:** marvel, trigun, hades, some other things
**Preferred Character Gender Pairings:** m/m and f/f please
**Preferred Writer Gender:** who cares
**Preferred Point of View:** 3rd person present or past 
**Average writing length**: 3 - 10 paragraphs, depending
**NSFW or SFW?** either or"""

run_test(test11, "test11", r"no match at \*?\*?Preferred Writer Age:?\*?\*?:?\s*(\d+).{,3}?\n")

test12 = """**Name:** tony chestnut
**Pronouns:** she/they/he
**Timezone:** pst
**Availability:** never, go away 
**Preferred Character Age:** usually 19+
**Preferred Writer Age:** 20+
**Preferred Genres:** fantasy, furry, drama, etc.
**Fandoms:** marvel, trigun, hades, some other things
**Preferred Character Gender Pairings:** m/m and f/f please
**Preferred Writer Gender:** who cares
**Preferred Point of View:** 3rd person present or past 
**Average writing length**: 3 - 10 paragraphs, depending
**NSFW or SFW?** either or"""

run_test(test12, "test12", r"no match at \*?\*?Preferred Character Age:?\*?\*?:?\s*(\d+).{,3}?\n")

test13 = """**Name:** tony chestnut
**Pronouns:** she/they/he
**Timezone:** pst
**Availability:** never, go away 
**Preferred Character Age:** 19+ depending on the setting
**Preferred Writer Age:** 20+
**Preferred Genres:** fantasy, furry, drama, etc.
**Fandoms:** marvel, trigun, hades, some other things
**Preferred Character Gender Pairings:** m/m and f/f please
**Preferred Writer Gender:** who cares
**Preferred Point of View:** 3rd person present or past 
**Average writing length**: 3 - 10 paragraphs, depending
**NSFW or SFW?** either or"""

run_test(test13, "test13", r"no match at \*?\*?Preferred Character Age:?\*?\*?:?\s*(\d+).{,3}?\n")

test14 = """**Name:** tony chestnut
**Pronouns:** she/they/he
**Timezone:** pst
**Availability:** never, go away 
**Preferred Character Age:** 20+ but not in school settings
**Preferred Writer Age:** 20+
**Preferred Genres:** fantasy, furry, drama, etc.
**Fandoms:** marvel, trigun, hades, some other things
**Preferred Character Gender Pairings:** m/m and f/f please
**Preferred Writer Gender:** who cares
**Preferred Point of View:** 3rd person present or past 
**Average writing length**: 3 - 10 paragraphs, depending
**NSFW or SFW?** either or"""

run_test(test14, "test14", r"no match at \*?\*?Preferred Character Age:?\*?\*?:?\s*(\d+).{,3}?\n")

test15 = """**Name:** tony chestnut
**Pronouns:** she/they/he
**Timezone:** pst
**Availability:** never, go away 
**Preferred Character Age:** 20-30 ish
**Preferred Writer Age:** 20+
**Preferred Genres:** fantasy, furry, drama, etc.
**Fandoms:** marvel, trigun, hades, some other things
**Preferred Character Gender Pairings:** m/m and f/f please
**Preferred Writer Gender:** who cares
**Preferred Point of View:** 3rd person present or past 
**Average writing length**: 3 - 10 paragraphs, depending
**NSFW or SFW?** either or"""

run_test(test15, "test15", r"no match at \*?\*?Preferred Character Age:?\*?\*?:?\s*(\d+).{,3}?\n")
