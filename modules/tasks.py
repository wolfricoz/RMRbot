"""This cogs handles all the tasks."""
import asyncio
import json
import logging
import os
import re
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands, tasks

import classes.databaseController
import classes.searchbans as searchbans
from classes import permissions
from classes.AutomodComponents import AutomodComponents
from classes.Support.LogTo import automod_log
from classes.Support.discord_tools import fetch_message_or_none, send_message
from classes.databaseController import ConfigData, DatabaseTransactions, TimersTransactions, UserTransactions
from classes.forumtasks import ForumTasks
from classes.queue import queue

OLDLOBBY = int(os.getenv("OLDLOBBY"))


class Tasks(commands.GroupCog) :
	def __init__(self, bot: commands.Bot) :
		"""loads tasks"""
		self.bot = bot
		self.index = 0
		self.forums = None  # Potential cache of forums
		self.config_reload.start()
		self.lobby_history.start()
		self.search_ban_check.start()
		# self.check_users_expiration.start()
		self.check_invites_task.start()
		self.forum_manager.start()

	def cog_unload(self) :
		"""unloads tasks"""
		self.config_reload.cancel()
		self.lobby_history.cancel()
		self.search_ban_check.cancel()
# 		self.check_users_expiration.cancel()
		self.check_invites_task.cancel()
		self.forum_manager.cancel()

	@tasks.loop(hours=3)
	async def config_reload(self) :
		"""Reloads the config for the latest data."""
		for guild in self.bot.guilds :
			ConfigData().load_guild(guild.id)
		print("config reload")
		ConfigData().output_to_json()

	@tasks.loop(hours=24)
	async def lobby_history(self) :
		"""Updates banlist when user is unbanned"""
		if self.lobby_history.current_loop == 0 :
			return
		count = 0
		historydict = {}
		channel = self.bot.get_channel(OLDLOBBY)
		if channel is None :
			return
		logging.debug('creating cache...')
		time = datetime.now()
		async for h in channel.history(limit=None, oldest_first=True, before=time) :
			historydict[h.id] = {}
			historydict[h.id]["author"] = h.author.id
			historydict[h.id]["created"] = h.created_at.strftime('%m/%d/%Y')
			historydict[h.id]["content"] = h.content
			count += 1
		else :
			print(f'Cached {count} message(s).')
		if os.path.exists('config') is False :
			os.mkdir('config')
		with open('config/history.json', 'w') as f :
			# noinspection PyTypeChecker
			json.dump(historydict, f, indent=4)
		print("[auto refresh]List updated")
		logging.debug("[auto refresh]List updated")

	def remove_entry(self, data: classes.databaseController.Timers) :
		TimersTransactions.remove_timer(data)
		logging.debug(
			f"searchban expired with id {data.id} with data: {data.uid}, {data.guild}, {data.role}, {data.reason}, {data.removal}, {data.created_at}")

	@tasks.loop(minutes=60)
	async def search_ban_check(self) :
		"""checks if searchban can be removed."""
		print("checking search bans")
		for data in DatabaseTransactions.get_table("timers") :
			removal = data.created_at + timedelta(hours=data.removal)
			if datetime.now() < removal :
				continue
			guild = self.bot.get_guild(data.guild)
			try :
				roleid = ConfigData().get_key_int(guild.id, 'posttimeout')
				role = guild.get_role(roleid)
			except classes.databaseController.KeyNotFound :
				self.remove_entry(data)
				continue
			member = guild.get_member(data.uid)
			if member is None :
				self.remove_entry(data)
				continue
			userroles = [x.id for x in member.roles]
			if roleid not in userroles :
				self.remove_entry(data)
				continue

			await searchbans.remove(member, role, data)
			advert_mod = ConfigData().get_key_int(guild.id, "advertmod")
			advert_mod_channel = guild.get_channel(advert_mod)
			await advert_mod_channel.send(f"{member.mention}\'s search ban has expired.")
		print("Finished checking all roles on users for searchbans")

	async def user_expiration_update(self, userids) :
		"""updates entry time, if entry is expired this also removes it."""
		logging.debug(f"Checking all entries for expiration at {datetime.now()}")
		updated_users = []
		for guild in self.bot.guilds :
			for member in guild.members :
				if member.id not in userids :
					logging.debug(f"User {member.id} not found in database, adding.")
					UserTransactions.add_user_empty(member.id)
					continue
				updated_users.append(str(member.id))
				UserTransactions.update_entry_date(member.id)
		logging.debug(f"Updating entry time for {len(updated_users)} users")
		del updated_users

	async def user_expiration_remove(self, userdata, removaldate) :
		"""removes expired entries."""
		for entry in userdata :
			if entry.entry < removaldate :
				UserTransactions.user_delete(entry.uid)
				logging.debug(f"Database record: {entry.uid} expired")

	# @tasks.loop(hours=48)
	# async def check_users_expiration(self) :
	# 	"""updates entry time, if entry is expired this also removes it."""
	# 	if self.check_users_expiration.current_loop == 0 :
	# 		return
	# 	print("checking user entries")
	# 	userdata = UserTransactions.get_all_users()
	# 	userids = [x.uid for x in userdata]
	# 	removaldate = datetime.now() - timedelta(days=730)
	# 	await self.user_expiration_update(userids)
	# 	await self.user_expiration_remove(userdata, removaldate)
	# 	print("Finished checking all entries")

	@tasks.loop(hours=24)
	async def forum_manager(self) -> None :
		"""makes all posts active again"""
		print("starting the forum manager! The forum will be cleaned.")
		archived_thread: discord.Thread
		channel: discord.ForumChannel
		regex = re.compile(f"search", flags=re.IGNORECASE)
		channels = [
			channel
			for guild in self.bot.guilds
			for channel in guild.channels
			if channel.type == discord.ChannelType.forum and regex.search(channel.name)
		]
		for channel in channels :
			logging.debug(f"[Forum Manager] Checking {channel.name}")
			forum = ForumTasks(channel, self.bot)
			queue().add(forum.start())

	@tasks.loop(hours=24)
	async def check_invites_task(self) :
		"""Checks if the invite is still valid."""
		invite_pattern = r"(https?://)?(www\.)?(discord\.(gg|io|me|li)|discordapp\.com/invite)/[a-zA-Z0-9\-]+"
		logging.info("Checking invites")
		count = 0
		for guild in self.bot.guilds :
			invite_channel_id = ConfigData().get_key_or_none(guild.id, "checkinvites")
			if invite_channel_id is None :
				continue
			invite_channel = self.bot.get_channel(int(invite_channel_id))
			for channel in guild.channels :
				await asyncio.sleep(60)
				if channel.type != discord.ChannelType.text :
					continue
				async for message in channel.history(limit=10) :
					if message.author.bot :
						continue

					match = re.search(invite_pattern, message.content)
					if match :
						invite_link = match.group()
						try :
							await self.bot.fetch_invite(invite_link)
						except discord.HTTPException or discord.NotFound :
							await invite_channel.send(f"The invite link {invite_link} in {channel.mention} is invalid or expired.")
		logging.info(f"Finished checking all invites, found {count} invites.")

	@tasks.loop(hours=24)
	async def reload_logs(self) :
		"""Reloads the logs module at 1am every day."""
		if self.reload_logs.current_loop == 0 :
			return
		# Calculate how long we need to wait until 1am
		now = datetime.now()
		future = datetime(now.year, now.month, now.day, 1, 0)
		if now.hour >= 1 :  # If it's past 1am, set target to 1am tomorrow
			future += timedelta(days=1)
		await discord.utils.sleep_until(future)  # Sleep until the specified time

		# Reload the logs module
		logging.info("Reloading logs module")
		await self.bot.reload_extension("logs")

	@forum_manager.before_loop  # it's called before the actual task runs
	async def before_forum_manager(self) :
		await self.bot.wait_until_ready()

	@app_commands.command(name="expirecheck")
	@permissions.check_app_roles_admin()
	async def expirecheck(self, interaction: discord.Interaction) :
		"""forces the automatic user expiration check to start; normally runs every 48 hours"""
		self.check_users_expiration.restart()
		await interaction.response.send_message("[Debug]Checking all entries.")

	@app_commands.command(name="searchbans")
	@permissions.check_app_roles_admin()
	async def check_search_bans(self, interaction: discord.Interaction) :
		"""forces the automatic search ban check to start; normally runs every 30 minutes"""
		await interaction.response.send_message("[Debug]Checking all searchbans.")
		self.search_ban_check.restart()

	@app_commands.command(name="checkinvites")
	@permissions.check_app_roles_admin()
	async def check_invites(self, interaction: discord.Interaction) :
		"""forces the automatic invite check to start; normally runs every hour"""
		await interaction.response.send_message("[Debug]Checking all invites.")
		self.check_invites_task.restart()

	@search_ban_check.before_loop
	async def before_sbc(self) :
		"""stops event from starting before the bot has fully loaded"""
		await self.bot.wait_until_ready()

	# @check_users_expiration.before_loop
	# async def before_expire(self) :
	# 	"""stops event from starting before the bot has fully loaded"""
	# 	await self.bot.wait_until_ready()

	@lobby_history.before_loop
	async def before_lobbyhistory(self) :
		"""stops event from starting before the bot has fully loaded"""
		await self.bot.wait_until_ready()

	@config_reload.before_loop  # it's called before the actual task runs
	async def before_checkactiv(self) :
		"""stops event from starting before the bot has fully loaded"""
		await self.bot.wait_until_ready()

	@check_invites_task.before_loop
	async def before_checkinvites(self) :
		"""stops event from starting before the bot has fully loaded"""
		await self.bot.wait_until_ready()

	# @delete_abandoned_posts.before_loop
	# async def before_abandoned_posts(self) :
	# 	await self.bot.wait_until_ready()
	#
	# @check_status_tag.before_loop
	# async def before_status_check(self) :
	# 	await self.bot.wait_until_ready()


async def setup(bot) :
	"""Adds the cog to the bot."""
	await bot.add_cog(Tasks(bot))
