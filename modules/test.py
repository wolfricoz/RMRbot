"""This module is a test module; the code in here may be messy or incomplete. It also holds various tools I may use."""
import datetime
import json
import os
import re
import time
from time import perf_counter
import discord
from discord import Button
from discord.ext import commands
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker



class Test(commands.Cog, name="test"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=['purgetest', 'pt'])
    @commands.is_owner()
    async def purge(self, ctx: discord.Interaction):
        if ctx.author.id == 188647277181665280:
            with open('config/purge.json', 'r') as f:
                purgechannels = json.load(f)
            newchans = []
            old = discord.utils.get(ctx.guild.categories, name="Pending Removal")
            load_dotenv("../main.env")
            channels72 = os.getenv('channels72')
            spec = os.getenv('spec')
            channels24 = os.getenv('channels24')
            single = os.getenv('single')
            new72 = []
            new24 = []
            newsingle = []
            newspec = []
            for channel in purgechannels["channels"]:
                try:
                    chan = self.bot.get_channel(channel)
                    print(chan)
                    newchan = await chan.clone()
                    await chan.edit(category=old, name=f"old {chan.name}")
                    if str(channel) in channels72:
                        new72.append(newchan.id)
                    elif str(channel) in channels24:
                        new24.append(newchan.id)
                    elif str(channel) in single:
                        newsingle.append(newchan.id)
                    elif str(channel) in spec:
                        newspec.append(newchan.id)
                    else:
                        newchans.append(newchan.id)
                except:
                    print(f"{channel} failed")
            await ctx.channel.send(f"channel72: {new72}\n"
                                   f"channel24: {new24}\n"
                                   f"single: {newsingle}\n"
                                   f"spec: {newspec}\n"
                                   f"other: {newchans}")
        else:
            await ctx.send("Dev command.")

    @commands.command()
    @commands.is_owner()
    async def empty(self, ctx: discord.Interaction):
        if ctx.author.id == 188647277181665280:
            old = discord.utils.get(ctx.guild.categories, name="Pending Removal")
            for channel in old.channels:
                await channel.delete(reason=f"empty command used by {ctx.author}")
        else:
            await ctx.send("Dev command.")


    @commands.command()
    @commands.is_owner()
    async def emptyforum(self, ctx: discord.Interaction, forum: discord.ForumChannel):
        if ctx.author.id == 188647277181665280:
            for x in forum.threads:
                print(f"deleting {x}")
                await x.delete()
            async for x in forum.archived_threads(limit=1000):
                print(f"deleting {x}")
                await x.delete()
        else:
            await ctx.send("Dev command.")

    @commands.command()
    async def lookback(self, ctx: commands.Context, user: discord.Member):
        with open('config/history.json', 'r') as f:
            history = json.load(f)
        for a in history:
            if history[a]['author'] == user.id:
                await ctx.send(f"{user.mention} `{history[a]['created']}`\n"
                               f"{history[a]['content']}")

    @commands.command()
    async def lookbackid(self, ctx: commands.Context, user: discord.Member):
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
                        await ctx.send(f"[USER ID CHECK]{user.mention} `{history[a]['created']}`\n"
                                       f"{history[a]['content']}")

    @commands.command()
    @commands.is_owner()
    async def cache(self, ctx: commands.Context):
        start = perf_counter()
        count = 0
        historydict = {}
        channel = self.bot.get_channel(454425835064262657)
        await ctx.send('creating cache...')
        time = datetime.datetime.now()
        async for h in channel.history(limit=None, oldest_first=True, before=time):
            historydict[h.id] = {}
            historydict[h.id]["author"] = h.author.id
            historydict[h.id]["created"] = h.created_at.strftime('%m/%d/%Y')
            historydict[h.id]["content"] = h.content
            count += 1
        else:
            await ctx.send(f'Cached {count} message(s).')
            print(historydict)
        try:
            os.mkdir('config')
        except:
            pass
        with open('config/history.json', 'w') as f:
            json.dump(historydict, f, indent=4)
        print(perf_counter() - start)

    @commands.command()
    @commands.is_owner()
    async def update(self, ctx: commands.Context):
        from classes import jsonmaker
        await jsonmaker.guildconfiger.updateconfig(ctx.guild.id)
        await ctx.send('Guild config updated to latest version')

    @commands.command()
    @commands.is_owner()
    async def raidkick(self, ctx: commands.Context, channel: discord.TextChannel, limit=100):
        count = 0
        async for x in channel.history(limit=limit):
            for a in x.mentions:
                try:
                    await a.kick()
                    count += 1
                except:
                    print(f"unable to kick {a}")
            await x.delete()

        await ctx.send(f"Kicked {count}")

    @commands.command()
    @commands.is_owner()
    async def getlog(self, ctx: commands.Context):
        logfile = f"logs/log-{time.strftime('%m-%d-%Y')}.txt"
        with open(logfile, 'r') as file:
            await ctx.send(f"Current logfile:", file=discord.File(file.name))


async def setup(bot: commands.Bot):
    await bot.add_cog(Test(bot))
