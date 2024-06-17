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
import pycurl
from io import BytesIO
import certifi
# the base for a cog.
# noinspection PyUnresolvedReferences
class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="giveawayusers")
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
                try:
                    if thread.owner.name not in users:
                        users.append(thread.owner.name)
                except AttributeError:
                    await interaction.channel.send(f"Thread has no owner: {thread.jump_url} in {forum.name}")
        rmrwebsite = BytesIO()
        c = pycurl.Curl()
        c.setopt(c.URL, "https://roleplaymeets.com/api/getpostsusernames")
        c.setopt(c.WRITEDATA, rmrwebsite)
        c.setopt(c.CAINFO, certifi.where())
        c.perform()
        c.close()
        rmrwebsite = rmrwebsite.getvalue().decode("utf-8").replace('[', "").replace(']', "").replace('"', "").split(',')
        with open("forumusers.txt", "w") as f:
            f.write("Forum users: \n")
            f.write("\n".join([x for x in users]))
            f.write("\n\nRoleplay Meets Website Users: \n")
            f.write("\n".join([x for x in rmrwebsite]))

        await interaction.response.send_message(f"Here are all users in the forums:", file=discord.File("forumusers.txt"))



async def setup(bot):
    """Sets up the cog"""
    await bot.add_cog(Utility(bot))
