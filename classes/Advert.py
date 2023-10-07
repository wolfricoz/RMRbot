from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import discord
import pytz

from classes import jsonmaker


class Advert(ABC):

    @staticmethod
    @abstractmethod
    async def get_message(thread, interaction):
        if interaction.channel.type != discord.ChannelType.public_thread and thread is not None:
            thread_channel = thread
            thread = await thread.fetch_message(thread.id)
            return thread, thread_channel
        thread_channel = interaction.guild.get_thread(interaction.channel.id)
        thread = await thread_channel.fetch_message(thread_channel.id)
        return thread, thread_channel

    @staticmethod
    @abstractmethod
    async def logadvert(msg, lc):
        user = msg.author
        await lc.send(
                f"{user.mention}\'s advert was removed at {datetime.now().strftime('%m/%d/%Y, %H:%M:%S')}. Contents:")
        if len(msg.content) < 2000:
            await lc.send(msg.content)
        if len(msg.content) > 2000:
            await lc.send(msg.content[0:2000])
            await lc.send(msg.content[2000:4000])
        if msg.channel.type is discord.ChannelType.text:
            print(f"This is a Text channel {msg.channel.id}")
            await msg.delete()
        elif msg.channel.type is discord.ChannelType.public_thread:
            print(f"This is a Thread channel {msg.channel.id}")
            await msg.channel.delete()
        else:
            print("Channel was neither")
            await msg.delete()

    @staticmethod
    @abstractmethod
    async def sendadvertuser(ctx, msg, warning):
        user = msg.author
        try:
            await user.send(warning)
            await user.send("**__The removed advert: (Please make the required changes before reposting.)__**")
            if len(msg.content) < 2000:
                await user.send(msg.content)
            if len(msg.content) > 2000:
                await user.send(msg.content[0:2000])
                await user.send(msg.content[2000:4000])
        except discord.Forbidden:
            await ctx.followup.send("Can't DM user")
            pass

    @staticmethod
    @abstractmethod
    async def resetcooldown(self, message, timeincrement):
        tz = pytz.timezone('US/Eastern')
        now = datetime.now(tz)
        cd = now + timedelta(days=timeincrement)
        jsonmaker.Cooldown.add(self, message.author.id, message.channel.id, cd)

# Deprecated
    @abstractmethod
    async def addreason(self, value):
        warn = ""
        match value:
            case "age":
                warn = "Your advert failed to include character ages. We require both ages of your characters and your partner. It is recommended to add a general disclaimer."
            case "e72":
                warn = "You have posted too early in the channel, this channel has a 72 hour cooldown."
            case "e24":
                warn = "You have posted too early in the channel, this channel has a 24 hour cooldown."
            case "form":
                warn = "Your advert's format is incorrect. Potential causes: Double spacing, spacing between list items, more than 10 list items, using a font that is not Discord's default font."
            case "temp":
                warn = "Your advert did not follow the template."
            case "dup":
                warn = "Your advert was posted in other channels, we only allow unique adverts to be posted in multiple channels."
            case "pic":
                warn = "You have too many pictures within your advert. We allow up to 5 (FORUMS ONLY)."
            case _:
                pass
        return warn
