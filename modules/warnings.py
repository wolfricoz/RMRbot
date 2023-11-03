"""This cog is meant for every warning related command"""
import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

import classes.permissions as permissions
from classes.databaseController import ConfigData
from views.modals.warningmodal import WarningModal
from views.paginations.paginate import paginate


# the base for a cog.
# noinspection PyUnresolvedReferences
class Warnings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Make a pagination to allow staff to look through multiple warnings; this has to be done using a view.
    @app_commands.command(name="warnhistory")
    @permissions.check_app_roles()
    async def view(self, interaction: discord.Interaction, user: discord.Member):
        """View the user's past warnings"""
        await paginate.create_pagination_user(interaction, user, "warn")

    @app_commands.command(name="warn")
    @app_commands.choices(notify=[
        Choice(name="No", value="no"),
        Choice(name="Yes", value="yes")
    ])
    @permissions.check_app_roles()
    async def warn(self, interaction: discord.Interaction, user: discord.Member, notify: Choice[str]):
        """Warn a user with the option to notify or not notify."""
        warnlog = ConfigData().get_key_int(interaction.guild.id, "warnlog")
        await interaction.response.send_modal(WarningModal(user=user, notify=notify.value, warnlog=warnlog))


async def setup(bot):
    """Sets up the cog"""
    await bot.add_cog(Warnings(bot))
