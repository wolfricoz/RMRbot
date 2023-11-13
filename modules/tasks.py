"""This cogs handles all the tasks."""
import asyncio
import functools
import json
import logging
import os
import typing
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands, tasks

import classes.databaseController
import classes.searchbans as searchbans
from classes import permissions
from classes.databaseController import ConfigData, TimersTransactions, UserTransactions, DatabaseTransactions

OLDLOBBY = int(os.getenv("OLDLOBBY"))


# overhaul of database is needed to allow SQLalchemy to run in async mode.
def to_thread(func: typing.Callable) -> typing.Coroutine:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    return wrapper


class Tasks(commands.GroupCog):
    def __init__(self, bot):
        """loads tasks"""
        self.bot = bot
        self.index = 0
        self.config_reload.start()
        self.lobby_history.start()
        self.search_ban_check.start()
        self.check_users_expiration.start()
        self.unarchiver.start()

    def cog_unload(self):
        """unloads tasks"""
        self.config_reload.cancel()
        self.lobby_history.cancel()
        self.search_ban_check.cancel()
        self.check_users_expiration.cancel()
        self.unarchiver.cancel()

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

    def remove_entry(self, data: classes.databaseController.Timers):
        TimersTransactions.remove_timer(data)
        logging.debug(f"searchban expired with id {data.id} with data: {data.uid}, {data.guild}, {data.role}, {data.reason}, {data.removal}, {data.created_at}")

    @tasks.loop(minutes=60)
    async def search_ban_check(self):
        """checks if searchban can be removed."""
        print("checking search bans")
        for data in DatabaseTransactions.get_table("timers"):
            removal = data.created_at + timedelta(hours=data.removal)
            if datetime.now() < removal:
                continue
            guild = self.bot.get_guild(data.guild)
            try:
                roleid = ConfigData().get_key_int(guild.id, 'posttimeout')
                role = guild.get_role(roleid)
            except classes.databaseController.KeyNotFound:
                self.remove_entry(data)
                continue
            member = guild.get_member(data.uid)
            if member is None:
                self.remove_entry(data)
                continue
            userroles = [x.id for x in member.roles]
            if roleid not in userroles:
                self.remove_entry(data)
                continue

            await searchbans.remove(member, role, data)
            advert_mod = ConfigData().get_key_int(guild.id, "advertmod")
            advert_mod_channel = guild.get_channel(advert_mod)
            await advert_mod_channel.send(f"{member.mention}\'s search ban has expired.")
        print("Finished checking all roles on users for searchbans")

    async def user_expiration_update(self, userids):
        """updates entry time, if entry is expired this also removes it."""
        logging.debug(f"Checking all entries for expiration at {datetime.now()}")
        updated_users = []
        for guild in self.bot.guilds:
            for member in guild.members:
                await asyncio.sleep(0.1)
                if member.id not in userids:
                    logging.debug(f"User {member.id} not found in database, adding.")
                    UserTransactions.add_user_empty(member.id)
                    continue
                updated_users.append(member.id)
                UserTransactions.update_entry_date(member.id)
        uu = ", ".join(updated_users)
        logging.debug(f"Updating entry time for ({len(updated_users)}) {uu}")
        del updated_users
        del uu

    async def user_expiration_remove(self, userdata, removaldate):
        """removes expired entries."""
        for entry in userdata:
            if entry.entry < removaldate:
                await asyncio.sleep(0.1)
                UserTransactions.user_delete(entry.uid)
                logging.debug(f"Database record: {entry.uid} expired")

    @tasks.loop(hours=48)
    async def check_users_expiration(self):
        """updates entry time, if entry is expired this also removes it."""
        if self.check_users_expiration.current_loop == 0:
            return
        print("checking user entries")
        userdata = UserTransactions.get_all_users()
        userids = [x.uid for x in userdata]
        removaldate = datetime.now() - timedelta(days=730)
        await self.user_expiration_update(userids)
        await self.user_expiration_remove(userdata, removaldate)
        print("Finished checking all entries")

    @tasks.loop(hours=72)
    async def unarchiver(self):
        """makes all posts active again"""
        post: discord.Thread
        channel: discord.ForumChannel
        for x in self.bot.guilds:
            for channel in x.channels:
                if channel.type == discord.ChannelType.forum:
                    async for post in channel.archived_threads():
                        postreminder = "Your advert has been unarchived. If this advert is no longer relevant, please close it with /forum close (this message counts as a bump, you do not have to do the bump command.)"
                        try:
                            if permissions.check_admin(post.owner):
                                message = await post.send(postreminder)
                                await asyncio.sleep(1)
                                await message.delete()
                                continue
                            await post.send(f"{post.owner.mention} {postreminder}")
                            await asyncio.sleep(1)
                        except AttributeError:
                            await post.send(postreminder)
                            await asyncio.sleep(1)
                    for thread in channel.threads:
                        user = thread.guild.get_member(thread.owner_id)
                        if user is not None:
                            continue
                        logging.info(f"Deleting thread {thread.name} from {channel.name} in {thread.guild.name} as owner of the thread is no longer in guild.")
                        await thread.delete()

    @unarchiver.before_loop  # it's called before the actual task runs
    async def before_checkactiv(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="expirecheck")
    @permissions.check_app_roles_admin()
    async def expirecheck(self, interaction: discord.Interaction):
        """forces the automatic user expiration check to start; normally runs every 48 hours"""
        self.check_users_expiration.restart()
        await interaction.response.send_message("[Debug]Checking all entries.")

    @app_commands.command(name="searchbans")
    @permissions.check_app_roles_admin()
    async def check_search_bans(self, interaction: discord.Interaction):
        """forces the automatic search ban check to start; normally runs every 30 minutes"""
        await interaction.response.send_message("[Debug]Checking all searchbans.")
        self.search_ban_check.restart()

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
