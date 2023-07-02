import datetime
import json
import os
import re
from abc import ABC, abstractmethod
from random import shuffle
from time import sleep

import discord
import gspread
from discord import app_commands
from discord.ext import commands
from oauth2client.service_account import ServiceAccountCredentials

import adefs

if os.path.exists('roulette'):
    pass
else:
    os.mkdir('roulette')

no = ["I want my partner to play as", "Other information", "Timestamp", "Email address", "Uid", "Feedback",
      "Participate?", "age", "Rematch"]


# Future:
# - double check point accuracy, maybe add breaks to the loops


class RoomMate(ABC):
    @abstractmethod
    def genders(p, u1, u2):
        """Checks if the genders match, if they do not match then will return a -1 to signal the loop to stop"""
        user1pref = str(u1.get("I want my partner to play as")).replace(" ", "").split(',')
        user1 = str(u1.get(p)).replace(" ", "").split(',')
        user2pref = str(u2.get("I want my partner to play as")).replace(" ", "").split(',')
        user2 = str(u2.get(p)).replace(" ", "").split(',')
        sc = 0
        psc = 0
        for up in user1pref:
            for u in user2:
                up = up.lower()
                u = u.lower()
                if up == "" or u == "":
                    pass
                elif up == u:
                    sc += 1
                elif u == "any" or up == "any":
                    sc += 1
        for up in user2pref:
            for u in user1:
                up = up.lower()
                u = u.lower()
                if up == "" or u == "":
                    pass
                elif up == u:
                    psc += 1
                elif u == "any" or up == "any":
                    psc += 1
        if sc == 0:
            print(f"{u2['Username']} was not a match for {u1['Username']}(pairing)")
            sc = -1
            psc = 0

        if psc == 0:
            print(f"{u2['Username']} was not a match for {u1['Username']}(pairing)")
            sc = -1
            psc = 0
        return sc + psc

    def pairings(p, u1, u2):
        """Checks if the pairings match, if they do not match then will return a -1 to signal the loop to stop"""
        user1 = str(u1.get("Pairings")).lower().replace(" ", "").split(',')
        user2 = str(u2.get("Pairings")).lower().replace(" ", "").split(',')
        sc = 0
        psc = 0
        for up in user1:
            if up == "anyxany":
                sc += 5
                break
            for u in user2:
                if up == "" or u == "":
                    pass
                elif up == "malexfemale" and "femalexmale" in user2 or up == "femalexmale" and "malexfemale" in user2:
                    sc += 1
                    break
                elif up == u:
                    sc += 1

                    break
        for up in user2:
            if up == "anyxany":
                psc += 5
                break
            for u in user1:
                if up == "" or u == "":
                    pass
                elif u == "malexfemale" and "femalexmale" in user1 or up == "femalexmale" and "malexfemale" in user1:
                    psc += 1
                    break
                elif up == u:
                    psc += 1
                    break
        if sc == 0:
            print(f"{u2['Username']} was not a match for {u1['Username']}(pairing)")
            sc = -1
            psc = 0

        if psc == 0:
            print(f"{u2['Username']} was not a match for {u1['Username']}(pairing)")
            sc = -1
            psc = 0
        return sc + psc

    @abstractmethod
    def nsfw(p, u1, u2):
        """Checks if the NSFW preferences match, if they do not match then will return a -1 to signal the loop to stop.
        If they semi-match they get a +1, if its a direct match its a +2"""
        sc = 0
        if u1.get(p) == "SFW" and u2.get(p) == "NSFW" or u1.get(p) == "NSFW" and u2.get(p) == "SFW":
            sc = -1
            print(f"{u2['Username']} was not a match for {u1['Username']}(nsfw)")
        elif u1.get(p) == u2.get(p):
            sc += 2
        else:
            sc += 1
        return sc

    @abstractmethod
    def genres(p, u1, u2):
        """Checks the genre preferences, if user2 has preferences which are in user1's then it will deduct a point"""
        user1 = str(u1.get(p)).replace(" ", "").split(',')
        userex1 = str(u1.get("Excluded Genres")).replace(" ", "").split(',')
        user2 = str(u2.get(p)).replace(" ", "").split(',')
        sc = 0
        for up in user1:
            for u in user2:
                if up == "" or u == "":
                    pass
                elif up.lower() in u.lower():
                    sc += 1
        for up in userex1:
            for u in user2:
                if up == "" or u == "":
                    pass
                elif up.lower() in u.lower():
                    sc -= 1
        return sc

    @abstractmethod
    def other(p, u1, u2):
        """checks if the values match, if they match then adds +1 to score"""
        user1 = str(u1.get(p)).replace(" ", "").split(',')
        user2 = str(u2.get(p)).replace(" ", "").split(',')
        sc = 0
        for up in user1:
            for u in user2:
                if up == "" or u == "":
                    pass
                elif up.lower() == u.lower():
                    sc += 1
        return sc

    @abstractmethod
    def api():
        # Authorize the API
        scope = [
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/drive.file'
        ]
        file_name = 'client_key.json'
        creds = ServiceAccountCredentials.from_json_keyfile_name(file_name, scope)
        client = gspread.authorize(creds)
        # sheet = client.open('RR TEST SHEET 11423').sheet1
        sheet = client.open('New RR  (Responses)').sheet1
        python_sheet = sheet.get_all_records()
        shuffle(python_sheet)
        with open('roulette.json', 'w') as f:
            json.dump(python_sheet, f, indent=4)

        return python_sheet, sheet

    @abstractmethod
    def agecheck(p, u1, u2):
        if isinstance(u1['Age'], int):
            age1 = u1['Age']
        else:
            age1 = int(re.sub(r'\D', '', u1['Age']))
        if isinstance(u2['Age'], int):
            age2 = u2['Age']
        else:
            age2 = int(re.sub(r'\D', '', u2['Age']))
        u1pref = int(u1['Minimal partner age'])
        u2pref = int(u2['Minimal partner age'])
        sc = 0
        if age2 >= u1pref:
            sc += 1
        else:
            sc = -1
        if age1 >= u2pref:
            sc += 1
        else:
            sc = -1
        return sc

    @abstractmethod
    def prevmatch(p, u1, u2):
        count = 0
        prevmatch = str(u1.get('101Matches101')).split(",")
        prevmatch2 = str(u2.get('101Matches101')).split(",")
        if str(u1.get('Uid')) in prevmatch2:
            count = -1
        elif str(u2.get('Uid')) in prevmatch:
            count = -1
        return count


class RouletteUser(ABC):
    @abstractmethod
    async def check(interaction: discord.Interaction, u1):
        user = interaction.guild.get_member(u1["Uid"])
        err = []
        if user is None:
            err.append(f"{u1['Username']} has invalid user ID or has left: {u1['Uid']}")
            return err
        return err

    @abstractmethod
    async def send(userinfo, user, interaction):
        with open("match.txt", 'w', encoding='utf-16') as f:
            f.write(f"{userinfo.get('Username')}'s preferences"
                    f"\n\n----Genres----\n"
                    f"\nLikes: {userinfo.get('Genres')}"
                    f"\ndislikes: {userinfo.get('Excluded Genres')}"
                    f"\n\n----Pairings----"
                    f"\nI want to play as: {userinfo.get('I want to play as')}"
                    f"\nI want my partner to play as: {userinfo.get('I want my partner to play as')}"
                    f"\nPairings: {userinfo.get('Pairings')}"
                    f"\n\n----fandoms----"
                    f"\n{userinfo.get('fandom')}"
                    f"\n\n----Roleplay Info----"
                    f"\nPost Frequency: {userinfo.get('Post frequency')}"
                    f"\nPost Length: {userinfo.get('Post Length')}"
                    f"\nPoint of view: {userinfo.get('Writing Point of view')}"
                    f"\nFaceclaims: {userinfo.get('Faceclaims')}"
                    f"\nOther information: {userinfo.get('Other information')}"
                    f"\n\n----NSFW----"
                    f"\nNSFW: {userinfo.get('NSFW')}"
                    f"\nKinks: {userinfo.get('Kinks')}")
        embed = discord.Embed(title=f"**__Roleplay Roulette {datetime.datetime.now().strftime('%m/%m/%Y')}__**",
                              description=f"If you wish to no longer be matched, please visit https://forms.gle/xFwY79vD6iMryFhcA and turn off participation"
                                          f"\nYou have been matched with <@{userinfo.get('Uid')}>, here are their preferences:")
        try:
            await user.send(embed=embed,
                            file=discord.File(f.name, 'result.txt'))
        except discord.Forbidden:
            await interaction.channel.send(f"{userinfo.get('Username')} Couldn't DM.")
        os.remove(f.name)


class roulette(commands.GroupCog, name="roulette"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="check")
    @adefs.check_slash_db_roles()
    async def rrcheck(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False, thinking=False)
        python_sheet, sheet = RoomMate.api()
        fails = []
        for u1 in python_sheet:
            f = list(await RouletteUser.check(interaction, u1))
            fails.extend(f)
        fails = list(filter(None, fails))
        print(fails)
        failed = "\n".join(fails)
        await interaction.followup.send(f"User checks failed:\n{failed}")

    @app_commands.command(name="id")
    async def rrid(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"Your username is {interaction.user} and your user is is {interaction.user.id}", ephemeral=True)

    @app_commands.command(name="results")
    @adefs.check_slash_db_roles()
    async def results(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False, thinking=False)
        python_sheet, sheet = RoomMate.api()
        try:
            os.remove("rr.txt")
        except FileNotFoundError:
            pass
        matched = {}
        matchedid = {}
        matchcounter = {}
        matchresultid = {}
        matchresult = {}
        for mc in python_sheet:
            matchcounter[mc.get('Username')] = 0
        for u1 in python_sheet:
            print(u1['Username'], " being matched")
            userchecked = {}
            gcount = 0
            oldcount = 0
            if matchcounter[u1.get('Username')] >= 2:
                print(f"{u1.get('Username')} already has the max amount of matches")
                continue
            for p in u1.keys():
                sk = ['Username']
                if p in no or p in sk:
                    pass
                else:
                    user1 = str(u1.get(p)).replace(" ", "").split(',')
                    for _ in user1:
                        gcount += 1
            for u2 in python_sheet:
                count = 0
                if matchcounter[u2.get('Username')] >= 2:
                    print(f"{u2.get('Username')} is already matched")
                    continue
                for p in u2.keys():

                    if p == "Uid":
                        pc = RoomMate.prevmatch(p, u1, u2)
                        if pc == -1:
                            count = -1
                            break
                    if p == "Username" and u1.get(p) == u2.get(p):
                        count = -1
                        break
                    elif p == "I want to play as":
                        pc = RoomMate.genders(p, u1, u2)
                        if pc == -1:
                            count = -1
                            break
                        else:
                            oldcount = count
                            count += pc

                    elif p == "Pairings":
                        pc = RoomMate.pairings(p, u1, u2)
                        if pc == -1:
                            count = -1
                            break
                        else:
                            oldcount = count
                            count += pc
                    elif p == "NSFW":
                        pc = RoomMate.nsfw(p, u1, u2)
                        if pc == -1:
                            count = -1
                            break
                        else:
                            oldcount = count
                            count += pc

                    elif p == "Genres":
                        pc = RoomMate.genres(p, u1, u2)
                        oldcount = count
                        count += pc

                    elif p == "Minimal partner age":
                        pc = RoomMate.agecheck(p, u1, u2)
                        oldcount = count
                        count += pc

                    elif p in no:
                        continue
                    else:
                        pc = RoomMate.other(p, u1, u2)
                        oldcount = count
                        count += pc
                    print(f"{u1['Username']} + {u2['Username']}: {p}: {count}/{gcount} ({count - oldcount})")
                # Final count checker, if -1, its skipped. otherwise its converted to percentages.
                if count == -1:
                    pass
                else:
                    percent = 100 / gcount * count
                    userchecked[u2.get('Username')] = round(percent, 2)
            delete = [key for key in userchecked if userchecked.get(key) == -1]
            for w in delete:
                userchecked.pop(w)
            if len(userchecked) == 0:
                winner = "No partner matched their preferences"
                matchresultid[u1.get('Uid')] = None
                matchresult[u1.get('Username')] = None
            else:
                winner = max(userchecked, key=userchecked.get)
                matchcounter[winner] += 1
                matchcounter[u1.get('Username')] += 1
                matchresultid[u1.get('Uid')] = max(userchecked.values())
                matchresult[u1.get('Username')] = max(userchecked.values())
            matched[u1.get('Username')] = winner
            for i in python_sheet:
                if i.get('Username') == winner:
                    winnerid = i.get('Uid')
            try:
                matchedid[u1.get('Uid')] = winnerid
            except UnboundLocalError:
                pass
            with open('roulette/rr.txt', 'a', encoding='utf-16') as f:
                f.write(f"\nUsername: {u1.get('Username')} ({u1.get('Uid')})\n"
                        f"Recommended partner(s): {winner}\n"
                        f"feedback from user: {u1.get('Feedback')}\n"
                        f"\ndebug: {userchecked}\n")

        with open('roulette/rr.txt', 'a', encoding='utf-16') as file:
            text = "Recommended matches:"
            file.write(f"{text:=^100}\n")
            for m, ma in matched.items():
                file.write(f"{m} and {ma}. match rating: {matchresult[m]}\n")
        await interaction.channel.send("Roleplay Roulette results", file=discord.File(f.name, "RRresults.txt"))

        os.remove("roulette/rr.txt")

        def check(m):
            return m.content is not None and m.channel == interaction.channel

        confirm = True
        desc = "To send the results to all members and publish to channel, please type **'confirm'**\n After 10m this prompt is invalid"
        embed = discord.Embed(title=f"Roleplay Roulette", description=desc)
        conf = await interaction.channel.send(embed=embed)
        while confirm is True:
            msg = await self.bot.wait_for('message', check=check, timeout=600)
            if "confirm" in msg.content.lower():
                desc = "Confirmation given."
                embed = discord.Embed(title=f"Roleplay Roulette", description=desc)
                confirm = False
                await conf.edit(embed=embed)
                await msg.delete()
        with open(f'jsons/{interaction.guild.id}.json', 'r') as file:
            data = json.load(file)
        roulschannel = self.bot.get_channel(data['roulette'])

        # Sends users their results, and sends it into the roulette channel.
        await roulschannel.send(f"<@&686535572000473089>\n"
                                f"**__Roleplay Roulette {datetime.datetime.now().strftime('%m/%m/%Y')}__**\n\n")
        for m, ma in matchedid.items():
            sleep(1)
            user1 = interaction.guild.get_member(m)
            user2 = interaction.guild.get_member(ma)
            row = sheet.find(f"{m}")
            column = sheet.find(f"101Matches101")
            oldcell = sheet.cell(row.row, column.col)
            sheet.update_cell(row.row, column.col, value=f"{ma},{oldcell.value}")

            userinfo1 = next(item for item in python_sheet if item["Uid"] == m)
            userinfo2 = next(item for item in python_sheet if item["Uid"] == ma)
            if user1 is not None:
                await RouletteUser.send(userinfo2, user1, interaction)
            else:
                await user2.send("No match")
            if user2 is not None:
                await RouletteUser.send(userinfo1, user2, interaction)
            else:
                await user1.send("No match")
            await roulschannel.send(f"<@{m}> and <@{ma}>. matching rate: {matchresultid[m]}")
        await roulschannel.send(f"\n\nYou have been messaged with your partners information, if you have any questions, feedback, or run into issues please open a ticket <#992127400664109106>")


async def setup(bot):
    await bot.add_cog(roulette(bot))
