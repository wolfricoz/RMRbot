import os
import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import discord.utils
import pytz
from discord.ext import commands
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
import db
import jsonmaker

Session = sessionmaker(bind=db.engine)
session = Session()
load_dotenv('main.env')
channels72 = os.getenv('channels72')
spec = os.getenv('spec')
channels24 = os.getenv('channels24')
single = os.getenv('single')
test = os.getenv('test')


class AutoModeration(ABC):

    async def list(self, message, modchannel):
        check = re.findall(r"-.{0,52}|\*.{0,52}|•.{0,52}|>.{0,52}|★.{0,52}|☆.{0,52}|♡.{0,52}", message.content)
        listcount = 0
        for x in check:
            if len(x) <= 50:
                listcount += 1
            else:
                pass
        if listcount >= 10:
            await modchannel.send(
                f"{message.author.mention} in {message.channel.mention} has potentially posted a list with too many options. \n list Count: {listcount}")
            await message.add_reaction("❌")
        else:
            await message.add_reaction("🤖")
        print("list checked")

    async def spacing(self, message, modchannel):
        check = re.search(r"\n{3}|\n{4}|\n{5}|\n{6}", message.content)
        if check is not None:
            await message.author.send(f"[automod] {message.author.mention} your advert in {message.channel.mention} has double spaces, and has been removed. \n\n"
                                      f"You may repost once these double spaces have been removed. You do not have to open a ticket.")
            await message.delete()
        else:
            pass
        print("spacing checked")

    async def age(self, message):
        check = re.search(r"\b(all character(s|'s) ([2-9][0-9]|18|19)|all character(s|'s) are ([2-9][0-9]|18|19)|([2-9][0-9]|18|19)\+ character(s|'s))\b", message.content, flags=re.IGNORECASE)
        if check is None:
            await message.add_reaction("❓")
        else:
            await message.add_reaction("🆗")
        print("age checked")
    async def cooldown(self, message, timeincrement, modchannel):
        # check = datetime.utcnow() + timedelta(days=timeincrement)
        bcheck = datetime.utcnow() + timedelta(hours=-timeincrement)
        messages = message.channel.history(limit=300, after=bcheck, oldest_first=False)
        count = 0
        async for m in messages:
            if m.author.id == message.author.id:
                count += 1
                if count == 2:
                    lm = m.jump_url
                    pm = m.created_at

                    await modchannel.send(
                        f"{message.author.mention} has posted too early in {message.channel.mention}. \n"
                        f"Last post: {discord.utils.format_dt(pm, style='f')}, Current post: {discord.utils.format_dt(message.created_at, style='f')} timediff: {discord.utils.format_dt(pm, style='R')}\n"
                        f"previous message: {lm}")
                    await message.add_reaction("⛔")
                    break
        print("cooldown checked")
        if count < 2:
            await message.add_reaction("⏲")
            return

    async def repost(self, message):
        status = True
        tz = pytz.timezone("US/Eastern")
        from datetime import datetime, timedelta
        if message.author.bot:
            return
        # 72h Version
        if str(message.channel.id) in channels72 and status == True:
            current = datetime.now(tz)
            cooldown = current + timedelta(hours=72)
            await message.author.send(
                f"{message.author.mention}: You can repost in {message.channel.mention} at: {discord.utils.format_dt(cooldown)} ({discord.utils.format_dt(cooldown, 'R')})"
                f"\nBy posting in this channel, you are agreeing to our search rules")
        if str(message.channel.id) in spec and status == True:
            current = datetime.now(tz)
            cooldown = current + timedelta(hours=72)
            await message.author.send(
                f"{message.author.mention}: You can repost in {message.channel.mention} at: {discord.utils.format_dt(cooldown)} ({discord.utils.format_dt(cooldown, 'R')})"
                f"\nBy posting in this channel, you are agreeing to our search rules")
        # 24h Version
        if str(message.channel.id) in channels24 and status == True:
            current = datetime.now(tz)
            cooldown = current + timedelta(hours=24)
            await message.author.send(
                f"{message.author.mention}: You can repost in {message.channel.mention} at: {discord.utils.format_dt(cooldown)} ({discord.utils.format_dt(cooldown, 'R')})"
                f"\nBy posting in this channel, you are agreeing to our search rules")
        # single post version
        if str(message.channel.id) in single and status == True:
            current = datetime.now(tz)
            await message.author.send(
                "{}: You can repost in {} after the next purge.".format(message.author.mention,
                                                                        message.channel.mention) + "\nBy posting in this channel, you are agreeing to our search rules")
class Automod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # Enforces lobby format
        bot = self.bot
        modchannel = bot.get_channel(763058339088957548)
        messlength = len(message.content)
        if message.author.bot:
            return
        # length counters
        # quick-search
        if str(message.channel.id) in channels24:
            if messlength > 650:
                await message.author.send(f"""**Roleplay Meets AUTOMOD**: Your advert is too long for that channel. quick search channels are a maximum of 600 characters. Your character count is {len(message.content)}.

Please repost in the appropriate channel or shorten your advert.""")
                await message.delete()
            if messlength < 650:
                # list checker
                try:
                    await AutoModeration().list(message, modchannel)
                    await AutoModeration().spacing(message, modchannel)
                    await AutoModeration().age(message)
                    await AutoModeration().cooldown(message, 22, modchannel)
                    await AutoModeration().repost(message)
                except discord.NotFound:
                    pass
        # regular search
        elif str(message.channel.id) in channels72:
            if messlength < 600:
                await message.author.send(
                    f"""**Roleplay Meets AUTOMOD**: Your advert is too short for that channel. general search channels are a minimum of 600 characters. Your character count is {len(message.content)}.

Please repost in the appropriate channel or shorten your advert.""")
                await message.delete()
            if messlength > 600:
                # list checker
                try:
                    await AutoModeration().list(message, modchannel)
                    await AutoModeration().spacing(message, modchannel)
                    await AutoModeration().age(message)
                    await AutoModeration().cooldown(message, 70, modchannel)
                    await AutoModeration().repost(message)
                except discord.NotFound:
                    pass
        # other channels
        elif str(message.channel.id) in spec:
                try:
                    await AutoModeration().list(message, modchannel)
                    await AutoModeration().spacing(message, modchannel)
                    await AutoModeration().age(message)
                    await AutoModeration().cooldown(message, 70, modchannel)
                    await AutoModeration().repost(message)
                except discord.NotFound:
                    pass
        elif str(message.channel.id) in test:
                try:
                    await AutoModeration().list(message, modchannel)
                    await AutoModeration().spacing(message, modchannel)
                    await AutoModeration().age(message)
                    await AutoModeration().cooldown(message, 70, modchannel)
                    await AutoModeration().repost(message)
                except discord.NotFound:
                    pass
        else:
            return


async def setup(bot):
    await bot.add_cog(Automod(bot))
