import json
import os
from abc import ABC, abstractmethod
from collections import Counter

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

no = ["I want my partner to play as", "Other information", "Timestamp", "Email address", "Uid", "Feedback"]


class RoomMate(ABC):
    @abstractmethod
    def pairing(p, u1, u2):
        """Checks if the pairings match, if they do not match then will return a -1 to signal the loop to stop"""
        user1 = str(u1.get(p)).replace(" ", "").split(',')
        user2 = str(u2.get("I want my partner to play as")).replace(" ", "").split(',')
        sc = 0
        for u in user1:
            if u in user2:
                sc += 1
        if sc == 0:
            sc = -1
        return sc

    @abstractmethod
    def nsfw(p, u1, u2):
        """Checks if the NSFW preferences match, if they do not match then will return a -1 to signal the loop to stop.
        If they semi-match they get a +1, if its a direct match its a +2"""
        sc = 0
        if u1.get(p) == "SFW" and u2.get(p) == "NSFW" or u1.get(p) == "NSFW" and u2.get(p) == "SFW":
            sc = -1
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
        for u in user1:
            if u in user2:
                sc += 1
        for ex in userex1:
            if ex in user2:
                sc -= 1
        return sc

    @abstractmethod
    def other(p, u1, u2):
        """checks if the values match, if they match then adds +1 to score"""
        user1 = str(u1.get(p)).replace(" ", "").split(',')
        user2 = str(u2.get(p)).replace(" ", "").split(',')
        sc = 0
        for u in user1:
            if u in user2:
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
        sheet = client.open('New RR  (Responses)').sheet1
        python_sheet = sheet.get_all_records()

        with open('logs/roulette.json', 'w') as f:
            json.dump(python_sheet, f, indent=4)
        with open('roulette/rr.txt', 'w', encoding='utf-16') as f:
            f.write("Roleplay Roulette winners:")
        return python_sheet


class roulette(commands.GroupCog, name="roulette"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="results")
    @adefs.check_slash_db_roles()
    async def results(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False, thinking=False)
        python_sheet = RoomMate.api()
        for u1 in python_sheet:
            userchecked = {}
            gcount = 0
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
                for p in u2.keys():
                    if p == "Username" and u1.get(p) == u2.get(p):
                        count = -1
                        break
                    elif p == "I want to play as":
                        pc = RoomMate.pairing(p, u1, u2)
                        if pc == -1:
                            count = -1
                            break
                        else:
                            count += pc
                    elif p == "NSFW":
                        pc = RoomMate.nsfw(p, u1, u2)
                        if pc == -1:
                            count = -1
                            break
                        else:
                            count += pc

                    elif p == "Genres":
                        pc = RoomMate.genres(p, u1, u2)
                        count += pc

                    elif p in no:
                        pass
                    else:
                        pc = RoomMate.other(p, u1, u2)
                        count += pc
                # Final count checker, if -1, its skipped. otherwise its converted to percentages.
                if count == -1:
                    pass
                else:
                    percent = 100 / gcount * count
                    userchecked[u2.get('Username')] = round(percent, 2)
            delete = [key for key in userchecked if userchecked.get(key) == -1]
            for w in delete:
                userchecked.pop(w)
            k = Counter(userchecked)
            winner = []
            for i in k.most_common(3):
                winner.append(i[0])

            winner = ", ".join(winner)
            if len(winner) == 0:
                winner = "No partner matched their preferences"
            with open('roulette/rr.txt', 'a', encoding='utf-16') as f:
                f.write(f"\nUsername: {u1.get('Username')} ({u1.get('Uid')})\n"
                        f"Recommended partner(s): {winner}\n"
                        f"Extra info from user: {u1.get('Other information')}\n"
                        f"debug: {userchecked}\n")
        await interaction.channel.send("Roleplay Roulette results", file=discord.File(f.name, "RRresults.txt"))


async def setup(bot):
    await bot.add_cog(roulette(bot))
