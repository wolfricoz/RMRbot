import re
#
# text = """[M p A 4 F] I have compiled a list of characters from various series and franchises that, I'll admit, - have my attention, and are seldom seen on the face of anywhere here. If any of the following ring a bell, hit me up. Bonus if you are in for wholesome shit. I'll let you know more in the DMs after.
#
# Note: my definition of rare in this context are characters and franchises that are either rarely seen or I barely get anyone who knows or plays said characters and franchises. All are 18+, of course. Pedophilia is gross
#
#
# all characters are 25+
#
# Characters
# - Takarada Rikka from SSSS Gridman
# - Tsukimi Eiko from Ya Boy Kongming
# - Faith Connors from Mirror's Edge 2
# - Lara Croft from Tomb Raider
# - Gates from Titanfall 2
# - Millia Rage from Guilty Gear
# - Yorha 2B from Neir Automata
# - Bayonetta from- oh you already know
#
# Franchises
# * Street Fighter (Those women can crush my skull with those tree logs for thighs)
# * Resident Evil Remake (Infected excluded as sexual partners)
# * DMC5 (The lore is insane; on par for Japanese story writers)
# * Metal Gear Solid (Ah yes; 80s action movies with Mecha anime and bewbs)
# * Grishaverse books (it's surprisingly good but the story of the Crows is peak)
# ☆ Hell verse (Hazbin Hotel and Helluva Boss)
# ♡ Xenoblade Chronicles 2 (Surprising I haven't seen much of it)
# Azur Lane (teehee)
# > Arknights (The music is fucking legendary. The waifus are also neato)
# • Blue Archive (it's fairly obvious, isn't it?)
#
# Artists with OCs
# - [Ratatat47](https://twitter.com/ratatatat74)
# - [KFR](https://twitter.com/kfrworks)
# - [Sciamano240](https://twitter.com/sciamano240)
# - [Tsuaii](https://twitter.com/tsuaii)
# - [03_Bara](https://twitter.com/03_Bara_)
# - [Icomochi](https://twitter.com/rswxx)
# - [Chaesu](https://twitter.com/chaesuart)
# - [Expulse](https://twitter.com/nana0957)
# - [Chowbie](https://twitter.com/Chowbie)
# - [Kkamja](https://twitter.com/__Ja__ga__imo__ )
# - [Telepurte](https://twitter.com/Telepeturtle )"""
#
# class automod:
#     def dashcheck(text):
#         agecheck = re.search(r"\b(all character(s|'s) ([2-9][0-9]|18|19)|all character(s|'s) are ([2-9][0-9]|18|19)|([2-9][0-9]|18|19)\+ character(s|'s))\b", text, flags=re.IGNORECASE)
#         print(agecheck)
#         results = re.findall(r"-.{0,52}|\*.{0,52}|•.{0,52}|>.{0,52}|★.{0,52}|☆.{0,52}|♡.{0,52}", text)
#         results2 = re.findall(r"\n{3}", text)
#         print(results2)
#         print(results)
#         count = 0
#         for x in results:
#             if len(x) >= 51:
#                 pass
#             else:
#                 print(x)
#                 count += 1
#         else:
#             print(count)
#         if len(results2) > 0:
#             print("advert had double space")
#         else:
#             print("advert is okay (no double spaces)")
#         if agecheck is None:
#             print("user failed to declare ages")
#         else:
#             print("user added ages to their advert")
# automod.dashcheck(text)
r = "fantasy"
limitreg = re.compile(fr"(limit|limit.|no|dont|don't|)(.*?)({r})", flags=re.I)
match = limitreg.search("limit: nsfw ,fantasy")

print(match.group(3))