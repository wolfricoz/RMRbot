"""This cog includes all the code for the contextmenus"""
import discord
from discord import app_commands
from discord.ext import commands

from classes.Advert import Advert
from classes.TagController import TagController
from classes.automod import ForumAutoMod
from views.modals.custom import Custom


# noinspection PyTypeChecker
class contextmenus(commands.Cog, name="contextmenus"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.appr = app_commands.ContextMenu(name="approve", callback=self.approve, )
        self.bot.tree.add_command(self.appr)
        self.appcustom = app_commands.ContextMenu(name="custom warning", callback=self.appcustom, )
        self.bot.tree.add_command(self.appcustom)

    # Max 5 per Message, Max 5 per Member
    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.appcustom().name, type=self.appcustom().type)
        self.bot.tree.remove_command(self.appr.name, type=self.appr.type)
        # self.bot.tree.remove_command(self.ad.name, type=self.ad.type)

    async def approve(self, interaction: discord.Interaction,
                      message: discord.Message) -> None:
        """Approves the post"""
        await interaction.response.defer(ephemeral=True)
        bot = self.bot
        thread: discord.Thread = None

        if message.channel.type is discord.ChannelType.text:
            await interaction.followup.send("You can't approve outside of forums.")
        elif message.channel.type is discord.ChannelType.public_thread:
            thread = message.channel
        tags = [x.name for x in thread.applied_tags]
        forum = bot.get_channel(thread.parent_id)
        await TagController().change_status_tag(thread)
        if "New" in tags:
            for a in forum.available_tags:
                if a.name == "New":
                    await thread.remove_tags(a)
            await interaction.followup.send("Post successfully approved")
        elif "Bump" in tags:

            for a in forum.available_tags:
                if a.name == "Bump":
                    await thread.remove_tags(a)

            await interaction.followup.send("bump successfully approved")
        else:
            await interaction.followup.send("Post successfully approved")
        for a in forum.available_tags:
            if a.name == "Approved":
                await thread.add_tags(a)
        ForumAutoMod.approval_log(interaction)

    async def appcustom(self, interaction: discord.Interaction,
                        message: discord.Message) -> None:
        """Custom advert removal"""
        if interaction.channel.type != discord.ChannelType.public_thread:
            return
        thread, thread_channel = await Advert.get_message(None, interaction)
        await interaction.response.send_modal(Custom(self.bot, thread, thread_channel))


async def setup(bot: commands.Bot):
    """Adds cog to the bot."""
    await bot.add_cog(contextmenus(bot))
