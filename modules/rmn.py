import logging
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
from discord.app_commands import Choice
Session = sessionmaker(bind=db.engine)
session = Session()

class moderation(commands.Cog, name="rmn"):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot


    @app_commands.command(name="partnerapprove")
    @app_commands.choices(catagory=[
        Choice(name="Roleplay Help", value="839630534065389578"),
        Choice(name="Roleplay Hubs", value="795343022455783434"),
        Choice(name="Community Servers", value="782285734602080307"),
        Choice(name="Canon Fandom", value="782286135711498302"),
        Choice(name="AU fandom", value="782286194519834644"),
        Choice(name="Fantasy OC", value="782286286999650314"),
        Choice(name="Historical", value="809595268537516092"),
        Choice(name="Modern OC", value="782286490280788028"),
        Choice(name="Scifi OC", value="782293429437857833"),
        Choice(name="Gaming Roleplay", value="996936320872099920"),
        Choice(name="forum websites", value="793623051794120704"),
        Choice(name="Social servers", value="798690166154723349"),
    ])
    async def partner(self, interaction: discord.Interaction, catagory: Choice[str], member:discord.Member, servername:str):
        await interaction.response.defer()
        bot = self.bot
        guild = interaction.guild
        category = discord.utils.get(interaction.guild.categories, id=int(catagory.value))
        partner = discord.utils.get(interaction.guild.roles, id=780622396527869988)
        channel = await interaction.guild.create_text_channel(servername, category=category)
        await channel.set_permissions(member, send_messages=True, view_channel=True)
        await channel.send(f"{member.mention} Thank you for partnering with RMN. Please post your advert here, with a minimum of 5 tags and a maximum of 15. Don't forget to post our advert in your server!")
        await member.add_roles(partner)
        await interaction.followup.send("Success!")
async def setup(bot: commands.Bot):
    await bot.add_cog(moderation(bot))
