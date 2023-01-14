import logging
import pytz
from datetime import timedelta
from discord.ext import commands
from discord import app_commands
import discord
import adefs
from datetime import datetime
from abc import ABC, abstractmethod
from discord.app_commands import Choice
import jsonmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, column
import db
from discord.app_commands import AppCommandError
Session = sessionmaker(bind=db.engine)
session = Session()

class moderation(commands.GroupCog, name="dark"):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="deny")
    @adefs.check_slash_db_roles()
    async def deny(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer(ephemeral=True)
        reason = "Your kinks don't apply to After Dark. Please use our NSFW search channels to suit your RP needs. Good luck!"
        await user.send(f"{interaction.guild.name} **__After Dark Application denied__**: {reason} ")
        await interaction.followup.send(f"{user.mention} has been denied with reason {reason}")

async def setup(bot: commands.Bot):
    await bot.add_cog(moderation(bot))
