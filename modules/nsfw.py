import json
import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime

import discord
from dateutil.relativedelta import relativedelta
from discord import app_commands
from discord.ext import commands
from sqlalchemy.orm import sessionmaker

from classes import permissions
from classes.databaseController import ConfigData
from modals.NsfwModal import NsfwVerifyModal


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
        await interaction.channel.send(text, view=self.NsfwVerifyButton())



async def setup(bot: commands.Bot):
    await bot.add_cog(nsfw(bot))
