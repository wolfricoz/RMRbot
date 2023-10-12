import json
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands, tasks

import classes.databaseController
from classes import permissions
from classes.databaseController import ConfigData, TimersTransactions
import classes.searchbans as searchbans
OLDLOBBY = int(os.getenv("OLDLOBBY"))




# the base for a cog.
class Tasks(commands.GroupCog):
    def __init__(self, bot):
        self.bot = bot
        self.index = 0
        self.config_reload.start()
        self.lobby_history.start()
        self.search_ban_check.start()

    def cog_unload(self):
        self.config_reload.cancel()
        self.lobby_history.cancel()
        self.search_ban_check.cancel()


    @tasks.loop(hours=1)
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

    @lobby_history.before_loop
    async def before_lobbyhistory(self):
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=30)
    async def search_ban_check(self):
        print("checking search bans")
        for guild in self.bot.guilds:
            try:
                roleid = ConfigData().get_key_int(guild.id, 'posttimeout')
                role = guild.get_role(roleid)
            except classes.databaseController.KeyNotFound:
                continue
            for member in guild.members:
                userroles = [x.id for x in member.roles]
                if roleid not in userroles:
                    continue
                timer = TimersTransactions.get_timer_with_role(member.id, guild.id, roleid)
                if timer is None:
                    continue
                remove = timer.created_at + timedelta(hours=timer.removal)
                if datetime.now() < remove:
                    continue
                await searchbans.remove(member, role, timer)

    @app_commands.command(name="searchbans")
    async def check_search_bans(self, interaction: discord.Interaction):
        """forces the automatic search ban check to start; normally runs every 30 minutes"""
        await interaction.response.send_message("[Debug]Checking all searchbans.")
        self.search_ban_check.restart()
        await interaction.followup.send("check-up finished.")

    @search_ban_check.before_loop
    async def before_sbc(self):
        await self.bot.wait_until_ready()
async def setup(bot):
    await bot.add_cog(Tasks(bot))
