"""This cog is meant for every warning related command"""
import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

import classes.permissions as permissions
from classes.databaseController import ConfigData
from views.modals.warningmodal import WarningModal
from views.paginations.paginate import paginate
import classes.automod as automod

# the base for a cog.
# noinspection PyUnresolvedReferences
class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="forumusers")
    @permissions.check_app_roles()
    async def forumusers(self, interaction: discord.Interaction):
        """Get a list of forum users"""
        forums = automod.ForumAutoMod.config(interaction.guild.id)
        users = []
        for x in forums:
            forum: discord.ForumChannel = interaction.guild.get_channel(int(x))
            if forum is None:
                print(f"Forum channel {x} not found.")
                continue
            if not isinstance(forum, discord.ForumChannel):
                print(f"Channel {x} is not a forum channel. it is a {forum.type}")
                continue
            print(f"Forum: {forum.name}")
            for thread in forum.threads:
                if thread.owner.name not in users:
                    users.append(thread.owner.name)
        with open("forumusers.txt", "w") as f:
            f.write("Forum users: \n")
            f.write("\n".join([x for x in users]))

        await interaction.response.send_message(f"Here are all users in the forums:", file=discord.File("forumusers.txt"))



async def setup(bot):
    """Sets up the cog"""
    await bot.add_cog(Utility(bot))
