"""these commands are strictly for RMN."""
import typing

import discord
from discord import app_commands
from discord.ext import commands

from classes import permissions
from classes.databaseController import ConfigData


class moderation(commands.Cog, name="rmn"):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def channels_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
        """generates the autocompletion for partner channels"""
        data = []
        no = ['staff information', 'tickets', 'staff chat', 'partner lounge', 'check out roleplay meets: reborn', 'lobby', 'how to become a partner', 'chatter', 'server-related', 'to-be-removed']
        search_commands = [x for x in interaction.guild.categories]
        for x in search_commands:
            if len(data) >= 25:
                break
            if x.name.lower() in no:
                continue
            if current.lower() in x.name:
                data.append(app_commands.Choice(name=x.name, value=x.name))
        return data

    @app_commands.command(name="partnerapprove")
    @app_commands.autocomplete(category=channels_autocomplete)
    @permissions.check_app_roles()
    async def partner(self, interaction: discord.Interaction, category: str, member: discord.Member, servername: str):
        """Creates partner channel for partnerships."""
        await interaction.response.defer()
        category = discord.utils.get(interaction.guild.categories, name=category)
        partner = discord.utils.get(interaction.guild.roles, id=ConfigData().get_key_int(interaction.guild.id, "partner"))
        channel = await interaction.guild.create_text_channel(servername, category=category)
        overwrite = discord.PermissionOverwrite(send_messages=True, read_messages=True, read_message_history=True)
        await channel.set_permissions(member, overwrite=overwrite)
        await channel.send(
                f"{member.mention} Thank you for partnering with RMN. Please post your advert here, with a minimum of 5 tags and a maximum of 15. Don't forget to post our advert in your server!")
        await member.add_roles(partner)
        await interaction.followup.send("Success!")


async def setup(bot: commands.Bot):
    """Adds the cog to the bot."""
    await bot.add_cog(moderation(bot))
