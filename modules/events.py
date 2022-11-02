import logging

import discord
from discord.ext import commands
from abc import ABC, abstractmethod
import db
import adefs
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, column
from datetime import datetime, timedelta
import re
import typing

Session = sessionmaker(bind=db.engine)
session = Session()


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # Enforces lobby format
        bot = self.bot
        dobreg = re.compile("([0-9][0-9]) (1[0-2]|[0]?[0-9]|1)\/([0-3]?[0-9])\/([0-2][0-9][0-9][0-9])")
        match = dobreg.search(message.content)
        if message.guild is None:
            return
        if message.author.bot:
            return
        # Searches the config for the lobby for a specific guild
        p = session.query(db.permissions).filter_by(guild=message.guild.id).first()
        c = session.query(db.config).filter_by(guild=message.guild.id).first()
        staff = [p.mod, p.admin, p.trial]
        # reminder: change back to c.lobby
        if message.author.get_role(p.mod) is None and message.author.get_role(
                p.admin) is None and message.author.get_role(p.trial) is None:
            if message.channel.id == c.lobby:
                if match:
                    channel = bot.get_channel(c.modlobby)
                    await message.add_reaction("🤖")
                    if int(match.group(1)) < 18:
                        await channel.send(
                            f"<@&{p.lobbystaff}> {message.author.mention} has given an age under the age of 18: {message.content}")
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
                            f"<@&{p.lobbystaff}> user has given age. You can let them through with `?18a {message.author.mention} {message.content}`")
                    elif int(match.group(1)) >= 21 and not int(match.group(1)) > 24:
                        await channel.send(
                            f"<@&{p.lobbystaff}> user has given age. You can let them through with `?21a {message.author.mention} {message.content}`")
                    elif int(match.group(1)) >= 25:
                        await channel.send(
                            f"<@&{p.lobbystaff}> user has given age. You can let them through with `?25a {message.author.mention} {message.content}`")
                    return
                else:
                    try:
                        await message.author.send(
                            f"Please use format age mm/dd/yyyy \n Example: `122 01/01/1900` \n __**Do not round up your age**__ \n You can input your age and dob at: <#{c.lobby}>")
                    except:
                        await message.channel.send(
                            f"Couldn't message {message.author.mention}! Please use format age mm/dd/yyyy \n Example: `122 01/01/1900")
                    await message.delete()
                    return
        else:
            pass

async def setup(bot):
    await bot.add_cog(Events(bot))