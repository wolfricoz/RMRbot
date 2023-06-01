import datetime
import json
import logging
import os
import re
from abc import ABC, abstractmethod

from discord.ext import commands, tasks
from sqlalchemy.orm import sessionmaker

import db

Session = sessionmaker(bind=db.engine)
session = Session()


class Lobby(ABC):
    @abstractmethod
    async def check(user, channel):
        count = 0
        hf = []
        with open('config/history.json', 'r') as f:
            history = json.load(f)
        for a in history:
            if count > 5:
                await channel.send(f"{user.mention} More than 5 messages, search the user for the rest.")
                break
            if history[a]['author'] == user.id:
                hf.append(f"{user.mention}({user.id}) `{history[a]['created']}`\n"
                          f"{history[a]['content']}")
                count += 1
        if count > 0:
            lh = "\n".join(hf)
            await channel.send(f"[Lobby History] {lh}")

    @abstractmethod
    async def idcheck(user, channel):
        count = 0
        print("checking")
        verification = re.compile(r"\*\*USER ID VERIFICATION\*\*", flags=re.IGNORECASE)
        uuid = re.compile(fr"\b{user.id}\b", flags=re.MULTILINE)
        with open('config/history.json', 'r') as f:
            history = json.load(f)
        for a in history:
            if history[a]['author'] == 987662623187288094:
                vmatch = bool(verification.search(history[a]['content']))
                umatch = bool(uuid.search(history[a]['content']))
                if vmatch is True:
                    if umatch is True:
                        await channel.send(f"[USER ID CHECK]{user.mention} `{history[a]['created']}`\n"
                                           f"{history[a]['content']}")


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.index = 0
        self.printer.start()

    def cog_unload(self):
        self.printer.cancel()

    @commands.Cog.listener()
    async def on_message(self, message):
        # Enforces lobby format
        bot = self.bot
        dobreg = re.compile(r"([0-9][0-9]) (1[0-2]|0?[0-9]|1)/([0-3]?[0-9])/([0-2][0-9][0-9][0-9])")
        match = dobreg.search(message.content)
        if message.guild is None:
            return
        if message.author.bot:
            return
        # Searches the config for the lobby for a specific guild
        p = session.query(db.permissions).filter_by(guild=message.guild.id).first()
        c = session.query(db.config).filter_by(guild=message.guild.id).first()
        # Checks if user is a staff member.
        if message.author.get_role(p.mod) is None and message.author.get_role(
                p.admin) is None and message.author.get_role(p.trial) is None:
            # Checks if channel is the lobby
            if message.channel.id == c.lobby:
                # Checks if message matches the regex
                if match:
                    waitmessage = f"{message.author.mention} Thank you for submitting your age! " \
                                  f"One of our staff members will let you through into the main server once they are available. " \
                                  f"Please be patient, as our lobby is handled manually."
                    channel = bot.get_channel(c.modlobby)
                    lobby = bot.get_channel(c.lobby)
                    await message.add_reaction("🤖")
                    # Checks the ages in the message, and acts based upon it.
                    if int(match.group(1)) < 18:
                        await channel.send(
                            f"<@&{p.lobbystaff}> {message.author.mention} has given an age under the age of 18: {message.content} (User has been added to ID list)")
                        idchecker = session.query(db.idcheck).filter_by(uid=message.author.id).first()
                        if idchecker is not None:
                            idchecker.check = True
                            session.commit()
                        else:
                            try:
                                idcheck = db.idcheck(message.author.id, True)
                                session.add(idcheck)
                                session.commit()
                            except:
                                session.rollback()
                                session.close()
                                logging.exception("failed to  log to database")
                    if int(match.group(1)) >= 18 and not int(match.group(1)) > 20:
                        await channel.send(
                            f"<@&{p.lobbystaff}> {message.author.mention} has given age. You can let them through with `?18a {message.author.mention} {message.content}`")
                        await lobby.send(waitmessage)
                        await Lobby.check(message.author, channel)
                        await Lobby.idcheck(message.author, channel)
                    elif int(match.group(1)) >= 21 and not int(match.group(1)) > 24:
                        await channel.send(
                            f"<@&{p.lobbystaff}> {message.author.mention} has given age. You can let them through with `?21a {message.author.mention} {message.content}`")
                        await lobby.send(waitmessage)
                        await Lobby.check(message.author, channel)
                        await Lobby.idcheck(message.author, channel)
                    elif int(match.group(1)) >= 25:
                        await channel.send(
                            f"<@&{p.lobbystaff}> {message.author.mention} has given age. You can let them through with `?25a {message.author.mention} {message.content}`")
                        await lobby.send(waitmessage)
                        await Lobby.check(message.author, channel)
                        await Lobby.idcheck(message.author, channel)
                    return
                else:
                    channel = bot.get_channel(c.modlobby)
                    await channel.send(f"{message.author.mention} failed to follow the format: {message.content}")
                    await message.channel.send(
                        f"{message.author.mention} Please use format age mm/dd/yyyy "
                        f"\n Example: `122 01/01/1900` "
                        f"\n __**Do not round up your age**__ ")
                    await message.delete()
                    return
        else:
            pass

    @tasks.loop(hours=4)
    async def printer(self):
        """Updates banlist when user is unbanned"""
        count = 0
        historydict = {}
        channel = self.bot.get_channel(454425835064262657)
        print(channel)
        print('creating cache...')
        time = datetime.datetime.now()
        async for h in channel.history(limit=None, oldest_first=True, before=time):
            historydict[h.id] = {}
            historydict[h.id]["author"] = h.author.id
            historydict[h.id]["created"] = h.created_at.strftime('%m/%d/%Y')
            historydict[h.id]["content"] = h.content
            count += 1
        else:
            print(f'Cached {count} message(s).')
        try:
            os.mkdir('config')
        except:
            pass
        with open('config/history.json', 'w') as f:
            json.dump(historydict, f, indent=4)
        print("[auto refresh]List updated")

    @printer.before_loop  # it's called before the actual task runs
    async def before_checkactiv(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(Events(bot))
