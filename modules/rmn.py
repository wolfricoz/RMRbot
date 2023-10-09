import typing

import discord
from discord import app_commands
from discord.ext import commands

from classes.databaseController import ConfigData


class moderation(commands.Cog, name="rmn"):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def channels_autocomplete(self, interaction: discord.Interaction, current: str) -> typing.List[
        app_commands.Choice[str]]:
        data = []
        no = ['staff information', 'tickets', 'staff chat', 'partner lounge', 'check out roleplay meets: reborn', 'lobby', 'how to become a partner', 'chatter', 'server-related', 'to-be-removed']
        search_commands = [x for x in interaction.guild.categories]
        for x in search_commands:
            if len(data) >= 25:
                break
            if x.name.lower() in no:
                continue
            if current.lower() in x.name:
                data.append(app_commands.Choice(name=x.name, value=str(x.id)))
        return data

    @app_commands.command(name="partnerapprove")
    @app_commands.autocomplete(category=channels_autocomplete)
    async def partner(self, interaction: discord.Interaction, category: str, member: discord.Member,
                      servername: str):
        await interaction.response.defer()
        bot = self.bot
        guild = interaction.guild
        category = discord.utils.get(interaction.guild.categories, id=int(category))
        partner = discord.utils.get(interaction.guild.roles, id=ConfigData().get_key_int(interaction.guild.id, "partner"))
        channel = await interaction.guild.create_text_channel(servername, category=category)
        await channel.set_permissions(member, send_messages=True, view_channel=True)
        await channel.send(
                f"{member.mention} Thank you for partnering with RMN. Please post your advert here, with a minimum of 5 tags and a maximum of 15. Don't forget to post our advert in your server!")
        await member.add_roles(partner)
        await interaction.followup.send("Success!")


async def setup(bot: commands.Bot):
    await bot.add_cog(moderation(bot))
