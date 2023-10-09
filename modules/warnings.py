import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from classes.databaseController import UserTransactions, ConfigData
import classes.permissions as permissions
from views.modals.warning import Warning
from views.paginations.paginate import paginate



# the base for a cog.
class Warnings(commands.GroupCog):
    def __init__(self, bot):
        self.bot = bot

    # Make a pagination to allow staff to look through multiple warnings; this has to be done using a view.
    @app_commands.command()
    @permissions.check_app_roles()
    async def view(self, interaction: discord.Interaction, user: discord.Member):
        """View the user's past warnings"""
        await paginate.create_pagination(interaction, user, "warn")
    @app_commands.command(name="send")
    @app_commands.choices(notify=[
        Choice(name="No", value="no"),
        Choice(name="Yes", value="yes")
    ])
    @permissions.check_app_roles()
    async def warn(self, interaction: discord.Interaction, user: discord.Member, notify: Choice[str]):
        """Warn a user with the option to notify or not notify."""
        warnlog = ConfigData().get_key_int(interaction.guild.id, "warnlog")
        await interaction.response.send_modal(Warning(user=user, notify=notify.value, warnlog=warnlog))


async def setup(bot):
    await bot.add_cog(Warnings(bot))
