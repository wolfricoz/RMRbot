import datetime
import re
from abc import ABC, abstractmethod

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

import classes.permissions as permissions
import databases.current
from classes.AgeCalculations import AgeCalculations
from classes.databaseController import UserTransactions, ConfigData, VerificationTransactions, SearchWarningTransactions
from classes.Advert import Advert

class Custom(discord.ui.Modal, title='Custom Warning'):
    # Our modal classes MUST subclass `discord.ui.Modal`,
    # but the title can be whatever you want.
    # This will be a short input, where the user can enter their name
    # It will also have a placeholder, as denoted by the `placeholder` kwarg.
    # By default, it is required and is a short-style input which is exactly
    # what we want.
    custom_id = "cw"
    def __init__(self, bot, thread, thread_channel):
        super().__init__(timeout=None)  # Set a timeout for the modal
        self.bot = bot
        self.thread = thread
        self.thread_channel = thread_channel

    reason = discord.ui.TextInput(
            label='What is the reason?',
            style=discord.TextStyle.long,
            placeholder='Type your waning here...',
            required=True,
            max_length=300,
    )


    # This is a longer, paragraph style input, where user can submit feedback
    # Unlike the name, it is not required. If filled out, however, it will
    # only accept a maximum of 300 characters, as denoted by the
    # `max_length=300` kwarg.


    async def on_submit(self, interaction: discord.Interaction):
        bot = self.bot
        thread = self.thread
        thread_channel = self.thread_channel
        lc = ConfigData().get_key_int(interaction.guild.id, "ADVERTLOG")
        mc = ConfigData().get_key_int(interaction.guild.id, "ADVERTMOD")
        loggingchannel = bot.get_channel(lc)
        modchannel = bot.get_channel(mc)
        user = thread.author

        await interaction.response.send_message(content="Command received", ephemeral=True)
        warning = (
            f"Hello, I'm a staff member of **Roleplay Meets Reborn**. Your advert `{thread_channel.name}` has been removed with the following reason: \n"
            f"{self.reason.value}"
            f"\n\nIf you have any more questions, you can open a ticket at <#977720278396305418>.")
        # adds warning to database
        total_warnings, active_warnings = SearchWarningTransactions.add_warning(user.id, warning)
        await modchannel.send(
                f"{interaction.user.mention} has warned {user.mention} for failing to include character ages to their adverts in {thread.channel.mention}\n userId: {user.id} Active Warnings: {active_warnings} Total Warnings: {total_warnings}")
        # Logs the advert and sends it to the user.
        await Advert.logadvert(thread, loggingchannel)
        await Advert.sendadvertuser(interaction, thread, warning)
        try:
            await interaction.followup.send(f"{thread.author.mention} successfully warned")
        except discord.NotFound or discord.HTTPException:
            pass

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        print(error)
        await interaction.response.send_message(f'Oops! Something went wrong.\n{error}', ephemeral=True)

