"""Handles all forum related actions; such as automod and warnings."""
import asyncio
import logging
import os
import re
import typing

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

import classes.permissions as permissions
from classes.Advert import Advert
from classes.Support.LogTo import automod_log
from classes.Support.discord_tools import send_message, send_response
from classes.automod import ForumAutoMod
from classes.databaseController import ConfigData
from classes.queue import queue
from views.buttons.confirmButtons import confirmAction
from views.modals.custom import Custom
from views.paginations.paginate import paginate


class Forum(commands.GroupCog, name="forum") :

	def __init__(self, bot: commands.Bot) :
		self.bot = bot

	@commands.Cog.listener()
	async def on_thread_create(self, thread: discord.Thread) :
		"""Initiates automod to check the thread"""
		# gets the config
		forums = ForumAutoMod.config(guildid=thread.guild.id)
		bot = self.bot
		forum_channel = bot.get_channel(thread.parent_id)
		if forum_channel.id not in forums :
			return

		# Checks if there is space for new tags
		queue().add(ForumAutoMod.checktags(thread))

		msg: discord.Message = await ForumAutoMod.get_message(thread)
		if msg is None :
			queue().add(automod_log(bot, thread.guild.id,
			                        f"Message not found in {thread.name} posted by {thread.owner.mention}", "automodlog"),
			            priority=0)
			queue().add(ForumAutoMod.reminder(thread, thread.guild.id))
			return

		header_status = await ForumAutoMod.check_header(msg, thread)
		duplicate_status = await ForumAutoMod.duplicate(thread=thread, bot=bot, originalmsg=msg)
		if header_status :
			queue().add(automod_log(bot, thread.guild.id,
			                        f"Header not found in `{thread.name}` posted by {thread.owner.mention}", "automodlog"),
			            priority=0)
			return
		if duplicate_status :
			queue().add(automod_log(bot, thread.guild.id,
			                        f"{thread.name} is a duplicate of {duplicate_status.channel.mention} ", "automodlog"),
			            priority=0)
			return
		queue().add(ForumAutoMod.reminder(thread, thread.guild.id))
		# Applies the status tag 'new' to the thread
		queue().add(ForumAutoMod.info(thread))
		queue().add(ForumAutoMod.add_relevant_tags(forum_channel, thread, msg))
		queue().add(automod_log(bot, thread.guild.id,
		                        f"{thread.name} successfully checked and waiting for approval", "automodlog", "Success"),
		            priority=0)
		# await ForumAutoMod.age(msg, botmsg)

	@commands.Cog.listener('on_thread_create')
	async def on_profile_create(self, thread: discord.Thread) :
		key = ConfigData().get_key_int(thread.guild.id, "rpprofiles")
		rpprofiles = thread.guild.get_channel(key)
		if rpprofiles is None or rpprofiles.type != discord.ChannelType.forum or thread.parent_id != rpprofiles.id :
			return
		items = [
			r"\*?\*?Name:?\*?\*?:?(?:.*)",
			r"\*?\*?Pronouns:?\*?\*?:?(?:.*)",
			r"\*?\*?Timezone:?\*?\*?:?(?:.*)",
			r"\*?\*?Availability:?\*?\*?:?(?:.*)",
			r"\*?\*?Preferred Genres:?\*?\*?:?(?:(?:\n\*? .*)*)",
			r"\*?\*?Preferred Character Gender Pairings:?\*?\*?:?(?:.*)",
			r"\*?\*?Preferred Writer Gender:?\*?\*?:?(?:.*)",
			r"\*?\*?Preferred Point of View:?\*?\*?:?(?:.*)",
			r"\*?\*?Average writing length:?\*?\*?:?(?:.*)",
			r"\*?\*?NSFW or SFW\??\*?\*?:?(?:.*)"
		]
		ages = [
			r"\*?\*?Preferred Character Age:?\*?\*?:?\s*(\d+).{,3}?\n",
			r"\*?\*?Preferred Writer Age:?\*?\*?:?\s*(\d+).{,3}?\n",
		]
		items += ages
		text = await thread.fetch_message(thread.id)
		modchannel = self.bot.get_channel(ConfigData().get_key_int(thread.guild.id, "advertmod"))
		forum = self.bot.get_channel(thread.parent_id)
		for item in items :
			match = re.search(item, text.content, re.I)
			if match is None :
				queue().add(automod_log(self.bot, thread.guild.id,
				                        f"{thread.owner.mention} Failed to follow the profile template in {thread.name}. it failed at {item}",
				                        "automodlog"), priority=0)
				queue().add(Advert.send_advert_to_user(thread, text, "Your advert:", "no"))
				queue().add(thread.delete())
				return
		character_age = int(re.search(ages[0], text.content, re.DOTALL | re.I).group(1))
		writer_age = int(re.search(ages[1], text.content, re.DOTALL | re.I).group(1))
		if character_age < 18 or writer_age < 18 :
			await modchannel.send(
				f"{thread.owner.mention} has posted an profile with underaged ages in {thread.mention}."
				f"\nPreferred Character Age: {character_age}\nPreferred Writer Age: {writer_age}")
			for a in forum.available_tags :
				if a.name.lower() == "new" :
					queue().add(thread.remove_tags(a))
				if a.name.lower() == "waiting" :
					queue().add(thread.add_tags(a))
			return
		await ForumAutoMod.checktags(thread)
		for a in forum.available_tags :
			if a.name.lower() == "new" :
				queue().add(thread.remove_tags(a))
			if a.name.lower() == "approved" :
				queue().add(thread.add_tags(a))

	@commands.Cog.listener()
	async def on_message(self, message) :
		"""Checks if user wants to bump"""
		if message.author.bot :
			return
		if message.channel.type is discord.ChannelType.text :
			return
		if message.channel.type is discord.ChannelType.private :
			logging.info(f"Private message from {message.author}:\n{message.content}")
			return
		forums = ForumAutoMod.config(guildid=message.guild.id)
		dobreg = re.compile(r"bump|bumping", flags=re.IGNORECASE)
		match = dobreg.search(message.content)
		try :
			thread: discord.Thread = message.guild.get_thread(message.channel.id)
			forum: discord.ForumChannel = self.bot.get_channel(thread.parent_id)
		except Exception as e :
			print(e)
			return
		if message.channel.type != discord.ChannelType.public_thread or forum.id not in forums :
			return
		if message.id == message.channel.id :
			return
		if match :
			remind = await message.channel.send(
				f"Please use the bump command instead of bumping manually. You can do this by typing `/forum bump`. "
				f"This message will he removed in 60 seconds so you can bump!")
			await asyncio.sleep(60)
			try :
				await message.delete()
			except discord.NotFound :
				pass
			await remind.delete()

	# Could be replaced with on_raw_message_delete, however currently we have a task running to delete the threads
	# without message doing the same effectively. Potentially useful to remember for future.
	@commands.Cog.listener("on_message_delete")
	async def on_message_delete(self, message: discord.Message) :
		"""Removes the thread if the main message is removed."""
		logging.debug("on_message_delete: started")
		if message.channel.type != discord.ChannelType.public_thread :
			logging.debug("on_message_delete: not a thread")
			return
		forums = ForumAutoMod.config(message.guild.id)
		forum: discord.ForumChannel = self.bot.get_channel(message.channel.parent_id)
		if message.author == self.bot :
			logging.debug("on_message_delete: bot message")
			return
		if forum.id not in forums :
			logging.debug("on_message_delete: forum not found")
			return
		if message.id != message.channel.id :
			logging.debug("on_message_delete: not main message")
			return
		mod_channel_id = ConfigData().get_key_int(message.guild.id, 'removallog')
		mod_channel = self.bot.get_channel(mod_channel_id)
		await mod_channel.send(
			f"{message.author.mention} removed main post from {message.channel.mention}, "
			f"formerly known as `{message.channel}`. Message content:")
		count = 0
		while count < len(message.content) :
			await mod_channel.send(message.content[count :count + 1500])
			count += 1500
		await message.channel.delete()
		logging.debug("on_message_delete: finished")

	# Commands start here
	# noinspection PyUnresolvedReferences
	@app_commands.command(name="bump", description="Bumps your post!")
	async def bump(self, interaction: discord.Interaction) :
		"""Allows you to bump your advert every 72 hours."""
		forums = ForumAutoMod.config(interaction.guild.id)
		thread: discord.Thread = interaction.guild.get_thread(interaction.channel.id)
		forum: discord.ForumChannel = self.bot.get_channel(thread.parent_id)
		await ForumAutoMod.checktags(thread)
		if forum.id not in forums :
			await interaction.response.send_message("Forum not found")
			return
		await interaction.response.defer(ephemeral=True)
		queue().add(ForumAutoMod.bump(self.bot, interaction), 2)
		queue().add(ForumAutoMod.clean_bumps(thread, self.bot), 0)

	@app_commands.command(name="close", description="Removes your post from the forum and sends you a copy.")
	async def close(self, interaction: discord.Interaction) :
		"""Closes the advert and sends the advert to your dms"""
		await interaction.response.defer(ephemeral=True)
		thread: discord.Thread = interaction.channel
		if interaction.channel.type != discord.ChannelType.public_thread :
			await interaction.followup.send("[ERROR] This channel is not a thread.")
			return
		if thread.owner_id != interaction.user.id :
			await interaction.followup.send("[ERROR] You do not own this thread.")
			return

		async for m in thread.history(limit=1, oldest_first=True) :
			with open('advert.txt', 'w', encoding='utf-16') as f :
				f.write(m.content)
			await interaction.user.send(
				f"Your post `{m.channel}` has successfully been closed. The contents of your adverts:",
				file=discord.File(f.name, f"{m.channel}.txt"))
		await thread.delete()
		os.remove(f.name)

	async def search_commands_autocompletion(self, interaction: discord.Interaction, current: str) -> typing.List[
		app_commands.Choice[str]] :
		"""generates the options for autocomplete."""
		data = []
		search_commands = ConfigData().get_key(interaction.guild.id, "SEARCH")
		data.append(app_commands.Choice(name="custom", value="custom"))
		for x in search_commands :
			if current.lower() in x.lower() :
				data.append(app_commands.Choice(name=x.lower(), value=x))
		return data

	# /forum warn here.
	@app_commands.command()
	@permissions.check_app_roles()
	@app_commands.autocomplete(warning_type=search_commands_autocompletion)
	@app_commands.choices(warn=[Choice(name=x, value=x) for x in ['Yes', 'No']])
	async def warn(self, interaction: discord.Interaction, warning_type: str, thread_message: str = None,
	               warn: Choice[str] = "Yes") -> None :
		"""Warns the user and removes the advert; logs the warning in database."""
		if type(warn) is Choice :
			warn = warn.value
		warnings: dict = ConfigData().get_key(interaction.guild.id, "SEARCH")
		reason = warnings.get(warning_type.upper())
		if reason is None and warning_type.upper() != "CUSTOM" :
			await interaction.response.send_message("Please select a valid warning type.")
			return
		if interaction.channel.type != discord.ChannelType.public_thread and thread_message is None :
			await interaction.response.send_message("Please use the command in a thread, or fill in a message link.")
			return
		thread_message, thread_channel = await Advert.get_message(thread_message, interaction)
		bot = self.bot
		if warning_type.upper() == "CUSTOM" :
			await interaction.response.send_modal(
				Custom(bot=bot, thread=thread_message, thread_channel=thread_channel, warn=warn))
			return
		await interaction.response.defer(ephemeral=True)
		lc = ConfigData().get_key_int(interaction.guild.id, "ADVERTLOG")
		mc = ConfigData().get_key_int(interaction.guild.id, "ADVERTMOD")
		loggingchannel = bot.get_channel(lc)
		modchannel = bot.get_channel(mc)
		user = thread_message.author

		# adds warning to database
		warning = await Advert.send_in_channel(interaction, user, thread_channel, reason, warning_type, modchannel,
		                                       warn)
		# Logs the advert and sends it to the user.
		await Advert.logadvert(thread_message, loggingchannel)
		reminder = "**__The removed advert: (Please make the required changes before reposting.)__**"
		await Advert.send_advert_to_user(interaction, thread_message, reminder, warning)
		try :
			await interaction.followup.send(f"{thread_message.author.mention} successfully warned")
		except discord.NotFound :
			pass

	@app_commands.command()
	@permissions.check_app_roles()
	async def bans(self, interaction: discord.Interaction) :
		"""View all the search bans in the server."""
		await paginate.create_pagination_table(interaction, "timers", "Search Bans")

	@app_commands.command()
	@permissions.check_app_roles()
	async def history(self, interaction: discord.Interaction, user: discord.Member) :
		"""View the user's past warnings"""
		await paginate.create_pagination_user(interaction, user, "search", "search")

	@app_commands.command()
	@permissions.check_app_roles_admin()
	async def purge(self, interaction: discord.Interaction) :
		"""Purges all threads in the search forums."""
		view = confirmAction()
		await view.send_message(interaction,
		                        f"Are you sure you want to purge **ALL** of adverts in the search channels?")
		await view.wait()
		if view.confirmed is False :
			await interaction.followup.send("Purge cancelled")
			return
		await interaction.followup.send(f"Purge started")
		amount = 0
		forums = ConfigData().get_key(interaction.guild.id, "FORUM")
		for x in forums :
			await asyncio.sleep(0.1)
			forum: discord.ForumChannel = self.bot.get_channel(x)
			if isinstance(forum, discord.ForumChannel) is False :
				continue
			for thread in forum.threads :
				try :
					if thread.owner.id == interaction.user.id :
						continue
				except AttributeError :
					pass
				try :
					thread_message = await thread.fetch_message(thread.id)
					queue().add(Advert.send_advert_to_user(interaction, thread_message,
					                                 "Your advert has been removed due to a purge; you may repost "
					                                 "them once the purge has finished. Thank you for using RMR!",
					                                 "purge"), 0)
					queue().add(thread.delete(), 0)
					amount += 1
				except discord.NotFound :
					queue().add(await thread.delete(), 0)
					continue
				except Exception as e :
					await interaction.channel.send(f"failed to remove {thread.mention} because {e}")
			async for thread in forum.archived_threads(limit=None) :
				try :
					if thread.owner.id == interaction.user.id :
						continue
				except AttributeError :
					pass
				try :
					thread_message = await thread.fetch_message(thread.id)
					queue().add(Advert.send_advert_to_user(interaction, thread_message,
					                                 f"Your advert `{thread.name}` has been removed due to a purge;"
					                                 f"you may repost them once the purge has finished. Thank you for "
					                                 f"using RMR!\nYour advert:",
					                                 "purge"), 0)
					queue().add(thread.delete(), 0)
					amount += 1
				except discord.NotFound :
					queue().add(thread.delete(), 0)
					continue
				except Exception as e :
					await interaction.channel.send(f"failed to remove {thread.mention} because {e}")
		await interaction.channel.send(f"Purge queued, {amount} to be adverts removed.")
		queue().add(send_message(interaction.channel, f"Purge completed, {amount} adverts removed."), 0)

	@app_commands.command(name="count", description="counts all posts in the search forums")
	async def command(self, interaction: discord.Interaction) :
		amount = 0
		forums = ConfigData().get_key(interaction.guild.id, "FORUM")
		for x in forums :
			await asyncio.sleep(0.1)
			forum: discord.ForumChannel = self.bot.get_channel(x)
			if isinstance(forum, discord.ForumChannel) is False :
				continue
			for _ in forum.threads :
					amount += 1
			async for _ in forum.archived_threads(limit=None) :
					amount += 1
		await send_response(interaction, f"Total amount of posts: {amount}")




async def setup(bot: commands.Bot) :
	"""Adds cog to the bot."""
	await bot.add_cog(Forum(bot))
