"""This cogs handles all the tasks."""
import json
import logging
import os
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands, tasks

import classes.databaseController
import classes.searchbans as searchbans
from classes import permissions
from classes.databaseController import ConfigData, TimersTransactions, UserTransactions

OLDLOBBY = int(os.getenv("OLDLOBBY"))


class Tasks(commands.GroupCog):
    def __init__(self, bot):
        """loads tasks"""
        self.bot = bot
        self.index = 0
        self.config_reload.start()
        self.lobby_history.start()
        self.search_ban_check.start()
        self.check_users_expiration.start()

    def cog_unload(self):
        """unloads tasks"""
        self.config_reload.cancel()
        self.lobby_history.cancel()
        self.search_ban_check.cancel()
        self.check_users_expiration.cancel()

    @tasks.loop(hours=3)
    async def config_reload(self):
        """Reloads the config for the latest data."""
        for guild in self.bot.guilds:
            ConfigData().load_guild(guild.id)
        print("config reload")
        ConfigData().output_to_json()

    @tasks.loop(hours=24)
    async def lobby_history(self):
        """Updates banlist when user is unbanned"""
        if self.lobby_history.current_loop == 0:
            return
        count = 0
        historydict = {}
        channel = self.bot.get_channel(OLDLOBBY)
        if channel is None:
            return
        print('creating cache...')
        logging.debug('creating cache...')
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
        logging.debug("[auto refresh]List updated")
    @tasks.loop(minutes=60)
    async def search_ban_check(self):
        """checks if searchban can be removed."""
        if self.search_ban_check.current_loop == 0:
            return
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

    @tasks.loop(hours=48)
    async def check_users_expiration(self):
        """updates entry time, if entry is expired this also removes it."""
        if self.lobby_history.current_loop == 0:
            return
        print("checking user entries")
        userdata = UserTransactions.get_all_users()
        userids = [x.uid for x in userdata]
        removaldate = datetime.now() - timedelta(days=730)
        for guild in self.bot.guilds:
            for member in guild.members:
                if member.id not in userids:
                    UserTransactions.add_user_empty(member.id)
                    continue
                UserTransactions.update_entry_date(member.id)

        for entry in userdata:
            if entry.entry < removaldate:
                UserTransactions.user_delete(entry.uid)
                logging.debug(f"Database record: {entry.uid} expired")

    @app_commands.command(name="expirecheck")
    @permissions.check_app_roles_admin()
    async def expirecheck(self, interaction: discord.Interaction):
        """forces the automatic search ban check to start; normally runs every 30 minutes"""
        await interaction.response.send_message("[Debug]Checking all entries.")
        self.check_users_expiration.restart()
        await interaction.followup.send("check-up finished.")

    @app_commands.command(name="searchbans")
    @permissions.check_app_roles_admin()
    async def check_search_bans(self, interaction: discord.Interaction):
        """forces the automatic search ban check to start; normally runs every 30 minutes"""
        await interaction.response.send_message("[Debug]Checking all searchbans.")
        self.search_ban_check.restart()
        await interaction.followup.send("check-up finished.")

    @search_ban_check.before_loop
    async def before_sbc(self):
        """stops event from starting before the bot has fully loaded"""
        await self.bot.wait_until_ready()

    @check_users_expiration.before_loop
    async def before_expire(self):
        """stops event from starting before the bot has fully loaded"""
        await self.bot.wait_until_ready()

    @lobby_history.before_loop
    async def before_lobbyhistory(self):
        """stops event from starting before the bot has fully loaded"""
        await self.bot.wait_until_ready()

    @config_reload.before_loop  # it's called before the actual task runs
    async def before_checkactiv(self):
        """stops event from starting before the bot has fully loaded"""
        await self.bot.wait_until_ready()


async def setup(bot):
    """Adds the cog to the bot."""
    await bot.add_cog(Tasks(bot))
