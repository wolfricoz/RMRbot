"""NSFW verification is done through this cog."""
import discord
from discord import app_commands
from discord.ext import commands

from classes import permissions
from views.modals.NsfwModal import NsfwVerifyModal


class nsfw(commands.GroupCog, name="nsfw"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(self.NsfwVerifyButton())

    class NsfwVerifyButton(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        @discord.ui.button(label="Verify Here!", style=discord.ButtonStyle.red, custom_id="NSFWverify")
        async def test(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_modal(NsfwVerifyModal())

    @app_commands.command(name="button")
    @permissions.check_app_roles_admin()
    async def verify_button(self, interaction: discord.Interaction, text: str):
        """Creates the verification button for NSFW"""
        await interaction.channel.send(text, view=self.NsfwVerifyButton())


async def setup(bot: commands.Bot):
    """Adds the cog to the bot."""
    await bot.add_cog(nsfw(bot))
