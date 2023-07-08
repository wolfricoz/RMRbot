import json
import os
import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from time import sleep

import discord
from Levenshtein import ratio
from discord import app_commands
from discord.ext import commands

import adefs
from classes import jsonmaker
from classes.automod import ForumAutoMod


# from main import channels24




class forum(commands.GroupCog, name="forum"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        with open(f'jsons/{thread.guild.id}.json') as f:
            data = json.load(f)
        forums = data['forums']
        bot = self.bot
        await ForumAutoMod().checktags(thread)
        msg: discord.Message = await thread.fetch_message(thread.id)
        forum = bot.get_channel(thread.parent_id)
        if forum.id not in forums:
            return
        duplicate = await ForumAutoMod().duplicate(thread, bot)
        if duplicate is True:
            return
        await ForumAutoMod().reminder(thread, thread.guild.id)
        botmsg = await ForumAutoMod().info(forum, thread, msg)
        await ForumAutoMod().age(msg, botmsg)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.channel.type is discord.ChannelType.text:
            return
        with open(f'jsons/{message.guild.id}.json') as f:
            data = json.load(f)
        forums = data['forums']
        content = message.content
        dobreg = re.compile(r"bump|bumping", flags=re.IGNORECASE)
        match = dobreg.search(message.content)
        try:
            thread: discord.Thread = message.guild.get_thread(message.channel.id)
            forum: discord.ForumChannel = self.bot.get_channel(thread.parent_id)
        except:
            return

        if message.channel.type is discord.ChannelType.public_thread:
            if forum.id in forums:
                if match:
                    bot = self.bot
                    modchannel = bot.get_channel(763058339088957548)
                    thread: discord.Thread = message.channel
                    bcheck = datetime.utcnow() + timedelta(hours=-70)
                    messages = thread.history(limit=300, after=bcheck, oldest_first=False)
                    forum = bot.get_channel(thread.parent_id)
                    count = 0
                    await ForumAutoMod().checktags(thread)
                    if thread.owner_id == message.author.id:
                        async for m in messages:
                            if m.author.id == bot.application_id:
                                count += 1
                                if count == 2:
                                    lm = m.jump_url
                                    pm = m.created_at
                                    await message.author.send(
                                        f"Your last bump was within the 72 hours cooldown period in {message.channel.mention} and was removed."
                                        f"\nLast bump: {discord.utils.format_dt(pm, style='f')}timediff: {discord.utils.format_dt(pm, style='R')}"
                                        f"\nRepeated early bumps will result in your advert being taken down.")
                                    await message.delete()
                                    await modchannel.send(
                                        f"{message.author.mention} tried to bump within the 72 hours cooldown period in {message.channel.mention}."
                                        f"\nLast bump: {discord.utils.format_dt(pm, style='f')}timediff: {discord.utils.format_dt(pm, style='R')}")
                                    return

                        if message.channel.type == discord.ChannelType.public_thread:
                            for a in forum.available_tags:
                                if a.name == "Bump":
                                    await thread.add_tags(a)
                                    await message.channel.send("Post successfully bumped")
                                if a.name == "Approved":
                                    await thread.remove_tags(a)

                    else:
                        await message.channel.send(f"{message.author} You can't bump another's post.")

    @app_commands.command(name="bump", description="Bumps your post!")
    async def bump(self, interaction: discord.Interaction):
        with open(f'jsons/{interaction.guild.id}.json') as f:
            data = json.load(f)
        forums = data['forums']
        thread: discord.Thread = interaction.guild.get_thread(interaction.channel.id)
        forum: discord.ForumChannel = self.bot.get_channel(thread.parent_id)
        await ForumAutoMod().checktags(thread)
        if forum.id in forums:
            await interaction.response.defer(ephemeral=True)
            await ForumAutoMod.bump(self, interaction)
        else:
            print('not in list')


    @app_commands.command(name="close", description="Removes your post from the forum and sends you a copy.")
    async def close(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        thread: discord.Thread = interaction.channel
        if interaction.channel.type != discord.ChannelType.public_thread:
            await interaction.followup.send("[ERROR] This channel is not a thread.")
            return
        if thread.owner_id != interaction.user.id:
            await interaction.followup.send("[ERROR] You do not own this thread.")
            return

        async for m in thread.history(limit=1, oldest_first=True):
            with open('advert.txt', 'w', encoding='utf-16') as f:
                f.write(m.content)
            await interaction.user.send(f"Your post `{m.channel}` has successfully been closed. The contents of your adverts:", file=discord.File(f.name, f"{m.channel}.txt"))
        await thread.delete()
        os.remove(f.name)




    @app_commands.command(name="add", description="ADMIN: adds forum to the list to be moderated")
    @adefs.check_slash_admin_roles()
    async def add(self, interaction: discord.Interaction, forum: discord.ForumChannel) -> None:
        await interaction.response.defer(ephemeral=True)
        await jsonmaker.guildconfiger.addforum(interaction.guild.id, interaction, forum.id, 'forums')

    @app_commands.command(name="remove", description="ADMIN: removes forum to the list to be moderated")
    @adefs.check_slash_admin_roles()
    async def remove(self, interaction: discord.Interaction, forum: discord.ForumChannel) -> None:
        await interaction.response.defer(ephemeral=True)
        await jsonmaker.guildconfiger.remforum(interaction.guild.id, forum.id, 'forums')
        await interaction.followup.send("Successfully removed the forum")


async def setup(bot: commands.Bot):
    await bot.add_cog(forum(bot))
