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


class Automod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # Enforces lobby format
        bot = self.bot
        modchannel = bot.get_channel(763058339088957548)
        user = message.author
        ad = message.channel
        messlength = len(message.content)
        listcount = 0
        if message.author.bot:
            return
        # length counters
        if str(message.channel.id) in channels24:
            if messlength > 650:
                await message.author.send(f"""**Roleplay Meets AUTOMOD**: Your advert is too long for that channel. quick search channels are a maximum of 600 characters. Your character count is {len(message.content)}.

Please repost in the appropriate channel or shorten your advert.""")
                await message.remove()
            if messlength < 650:
                await message.add_reaction("🤖")
        elif str(message.channel.id) in channels72:
            if messlength < 600:
                await message.author.send(
                    f"""**Roleplay Meets AUTOMOD**: Your advert is too short for that channel. general search channels are a minimum of 600 characters. Your character count is {len(message.content)}.

                Please repost in the appropriate channel or shorten your advert.""")
                await message.remove()
            if messlength > 600:
                await message.add_reaction("🤖")
            for i in message.content:
                if i == "-" or i == "•" or i == "»":
                    listcount += 1
            if listcount >= 10:
                await modchannel.send(
                    f"{user.mention} in {ad.mention} has potentially posted a list with too many options. \n list Count: {listcount}")
            else:
                pass
        elif str(message.channel.id) in spec:
            for i in message.content:
                if i == "-" or i == "•" or i == "»":
                    listcount += 1
            if listcount >= 10:
                await modchannel.send(
                    f"{user.mention} in {ad.mention} has potentially posted a list with too many options. \n list Count: {listcount}")
            else:
                pass

async def setup(bot):
    await bot.add_cog(Automod(bot))
