import discord
from discord.ext import commands

import db
from sqlalchemy.orm import sessionmaker
from discord import app_commands
from classes.jsonmaker import guildconfiger
import adefs
Session = sessionmaker(bind=db.engine)
session = Session()

class config(commands.GroupCog, name="remrole"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="add", description="**CONFIG COMMAND**: Adds role to list that will be removed from user when /approve is used")
    @adefs.check_slash_admin_roles()
    async def radd(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer(ephemeral=True)
        await guildconfiger.addrole(interaction.guild.id, interaction, role.id, "remrole")

    @app_commands.command(name="remove", description="**CONFIG COMMAND**: Removes role from list that will be removed from user when /approve is used")
    @adefs.check_slash_admin_roles()
    async def rrem(self, interaction: discord.Interaction, role: discord.Role):
        await interaction.response.defer( ephemeral=True)
        try:
            await guildconfiger.remrole(interaction.guild.id, interaction, role.id, "remrole")
            await interaction.followup.send(f"{role} was removed from config.")
        except:
            await interaction.followup.send(f"{role} was not in the list.")

async def setup(bot: commands.Bot):
    await bot.add_cog(config(bot))

session.commit()