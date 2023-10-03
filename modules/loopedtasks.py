import json
import os
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands, tasks

from classes import permissions
from classes.databaseController import ConfigData

OLDLOBBY = int(os.getenv("OLDLOBBY"))


# the base for a cog.
class loopedTasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.index = 0
        self.config_reload.start()
        self.lobby_history.start()

    def cog_unload(self):
        self.config_reload.cancel()
        self.lobby_history.cancel()

    # noinspection PyUnresolvedReferences
    @app_commands.command(name='test')
    @permissions.check_app_roles()
    async def test(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        config = ConfigData().get_config(interaction.guild.id)
        await interaction.followup.send(f"TEST: Config data:\n{config}")

    @tasks.loop(minutes=10)
    async def config_reload(self):
        for guild in self.bot.guilds:
            ConfigData().load_guild(guild.id)
        print("config reload")
        ConfigData().output_to_json()

    @config_reload.before_loop  # it's called before the actual task runs
    async def before_checkactiv(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=24)
    async def lobby_history(self):
        """Updates banlist when user is unbanned"""
        count = 0
        historydict = {}
        channel = self.bot.get_channel(OLDLOBBY)
        if channel is None:
            return
        print('creating cache...')
        time = datetime.now()
        async for h in channel.history(limit=None, oldest_first=True, before=time):
            historydict[h.id] = {}
            historydict[h.id]["author"] = h.author.id
            historydict[h.id]["created"] = h.created_at.strftime('%m/%d/%Y')
            historydict[h.id]["content"] = h.content
            count += 1
        else:
            print(f'Cached {count} message(s).')
        if os.path.exists('config') is False:
            os.mkdir('config')
        with open('config/history.json', 'w') as f:
            json.dump(historydict, f, indent=4)
        print("[auto refresh]List updated")
    @lobby_history.before_loop  # it's called before the actual task runs
    async def before_checkactiv(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(loopedTasks(bot))
