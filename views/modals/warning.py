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

class Warning(discord.ui.Modal, title='Official Warning'):
    custom_id = "warning"
    def __init__(self, user, notify, warnlog):
        super().__init__(timeout=None)  # Set a timeout for the modal
        self.user = user
        self.notify = notify
        self.warnlog = warnlog

    reason = discord.ui.TextInput(
            label='What is the reason?',
            style=discord.TextStyle.long,
            placeholder='Type your waning here...',
            required=True,
            max_length=1000,
    )

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(self.warnlog)
        warning = f"{interaction.guild.name} **__WARNING__**: {self.reason}"
        UserTransactions.user_add_warning(self.user.id, self.reason.value)
        if self.notify.upper() == "YES":
            await self.user.send(warning)
        embed = discord.Embed(title=f"{self.user.name} has been warned", description=warning)
        embed.set_footer(text=f"Notify: {self.notify}, uid: {self.user.id}")
        await interaction.response.send_message(self.user.mention, embed=embed)
        await channel.send(embed=embed)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        print(error)
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)

