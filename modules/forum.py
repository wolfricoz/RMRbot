"""Handles all forum related actions; such as automod and warnings."""
import os
import re
import typing
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands

import classes.permissions as permissions
from classes.Advert import Advert
from classes.automod import ForumAutoMod
from classes.databaseController import ConfigData, SearchWarningTransactions
from views.modals.custom import Custom
from views.paginations.paginate import paginate


# noinspection PyUnresolvedReferences
class Forum(commands.GroupCog, name="forum"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        """Initiates automod to check the thread"""
        # gets the config
        forums = ForumAutoMod.config(guildid=thread.guild.id)
        bot = self.bot
        # Checks the tags and adds the correct ones.
        await ForumAutoMod.checktags(thread)
        msg: discord.Message = await thread.fetch_message(thread.id)
        forum_channel = bot.get_channel(thread.parent_id)
        if forum_channel.id not in forums:
            return
        duplicate = await ForumAutoMod.duplicate(thread=thread, bot=bot)
        if duplicate is True:
            return
        await ForumAutoMod.reminder(thread, thread.guild.id)
        botmsg = await ForumAutoMod.info(forum_channel, thread, msg)
        await ForumAutoMod.age(msg, botmsg)

    @commands.Cog.listener()
    async def on_message(self, message):
        """Checks if user wants to bump"""
        if message.author.bot:
            return
        if message.channel.type is discord.ChannelType.text:
            return
        forums = ForumAutoMod.config(guildid=message.guild.id)
        dobreg = re.compile(r"bump|bumping", flags=re.IGNORECASE)
        match = dobreg.search(message.content)
        try:
            thread: discord.Thread = message.guild.get_thread(message.channel.id)
            forum: discord.ForumChannel = self.bot.get_channel(thread.parent_id)
        except Exception as e:
            print(e)
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
                    user_count = 0
                    await ForumAutoMod.checktags(thread)
                    if thread.owner_id != message.author.id:
                        await message.channel.send(f"{message.author} You can't bump another's post.")
                        return
                    async for m in messages:
                        if m.author.id == bot.application_id:
                            count += 1
                        if count == 1:
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
                        if m.author.id == message.author.id:
                            user_count += 1
                    og = await thread.fetch_message(thread.id)
                    if og.edited_at is not None and og.edited_at <= bcheck and user_count <= 1 or og.edited_at is None and user_count <= 1:
                        for a in forum.available_tags:
                            if a.name == "Approved":
                                await thread.add_tags(a)
                        # await modchannel.send(
                        #         f"`[Experimental]` Automatically approved bump of {message.channel.mention}. Post was not edited in the last 70 hours.")
                        await message.channel.send("Post successfully bumped and automatically approved")
                        return
                    for a in forum.available_tags:
                        if a.name == "Bump":
                            await thread.add_tags(a)
                            await message.channel.send("Post successfully bumped and awaiting manual review")
                        if a.name == "Approved":
                            await thread.remove_tags(a)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Removes the thread if the main message is removed."""
        forums = ForumAutoMod.config(message.guild.id)
        if message.channel.type != discord.ChannelType.public_thread:
            return
        forum: discord.ForumChannel = self.bot.get_channel(message.channel.parent_id)
        if message.author == self.bot:
            return

        if forum.id not in forums:
            return
        if message.id != message.channel.id:
            return
        mod_channel_id = ConfigData().get_key_int(message.guild.id, 'removallog')
        mod_channel = self.bot.get_channel(mod_channel_id)
        await mod_channel.send(
                f"{message.author.mention} removed main post from {message.channel.mention}, formerly known as `{message.channel}`. Message content:\n{message.content[:1900]}")
        await message.channel.delete()

    # Commands start here
    @app_commands.command(name="bump", description="Bumps your post!")
    async def bump(self, interaction: discord.Interaction):
        """Allows you to bump your advert every 72 hours."""
        forums = ForumAutoMod.config(interaction.guild.id)
        thread: discord.Thread = interaction.guild.get_thread(interaction.channel.id)
        forum: discord.ForumChannel = self.bot.get_channel(thread.parent_id)
        await ForumAutoMod.checktags(thread)
        if forum.id not in forums:
            await interaction.response.send_message("Forum not found")
            return
        await interaction.response.defer(ephemeral=True)
        await ForumAutoMod.bump(self.bot, interaction)

    @app_commands.command(name="close", description="Removes your post from the forum and sends you a copy.")
    async def close(self, interaction: discord.Interaction):
        """Closes the advert and sends the advert to your dms"""
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
            await interaction.user.send(
                    f"Your post `{m.channel}` has successfully been closed. The contents of your adverts:",
                    file=discord.File(f.name, f"{m.channel}.txt"))
        await thread.delete()
        os.remove(f.name)

    async def search_commands_autocompletion(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
        """generates the options for autocomplete."""
        data = []
        search_commands = ConfigData().get_key(interaction.guild.id, "SEARCH")
        data.append(app_commands.Choice(name="custom", value="custom"))
        for x in search_commands:
            if current.lower() in x:
                data.append(app_commands.Choice(name=x.lower(), value=x))
        return data

    # /forum warn here.
    @app_commands.command()
    @permissions.check_app_roles()
    @app_commands.autocomplete(warning_type=search_commands_autocompletion)
    async def warn(self, interaction: discord.Interaction, warning_type: str, thread: str = None) -> None:
        """Warns the user and removes the advert; logs the warning in database."""

        warnings: dict = ConfigData().get_key(interaction.guild.id, "SEARCH")
        reason = warnings.get(warning_type)

        if interaction.channel.type != discord.ChannelType.public_thread and thread is None:
            await interaction.response.send_message("Please use the command in a thread, or fill in a message link.")
            return
        thread, thread_channel = await Advert.get_message(thread, interaction)
        bot = self.bot
        if warning_type.upper() == "CUSTOM":
            await interaction.response.send_modal(Custom(bot=bot, thread=thread, thread_channel=thread_channel))
            return
        await interaction.response.defer(ephemeral=True)
        lc = ConfigData().get_key_int(interaction.guild.id, "ADVERTLOG")
        mc = ConfigData().get_key_int(interaction.guild.id, "ADVERTMOD")
        loggingchannel = bot.get_channel(lc)
        modchannel = bot.get_channel(mc)
        user = thread.author

        # adds warning to database
        warning = Advert.send_in_channel(interaction, user, thread, thread_channel, reason, warning_type, modchannel)
        # Logs the advert and sends it to the user.
        await Advert.logadvert(thread, loggingchannel)
        await Advert.sendadvertuser(interaction, thread, warning)
        try:
            await interaction.followup.send(f"{thread.author.mention} successfully warned")
        except discord.NotFound:
            pass

    @app_commands.command()
    @permissions.check_app_roles()
    async def history(self, interaction: discord.Interaction, user: discord.Member):
        """View the user's past warnings"""
        await paginate.create_pagination(interaction, user, "search", "search")


async def setup(bot: commands.Bot):
    """Adds cog to the bot."""
    await bot.add_cog(Forum(bot))
