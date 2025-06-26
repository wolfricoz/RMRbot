"""This module is used to handle the automod for the forums."""
import asyncio
import logging
import os.path
import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import discord
import pytz
from discord.ext import commands

from classes.Advert import Advert
from classes.AutomodComponents import AutomodComponents
from classes.Support.LogTo import automod_log
from classes.Support.discord_tools import send_message
from classes.TagController import TagController
from classes.databaseController import ApprovalTransactions, ConfigData
from classes.queue import queue
from views.buttons.PostOptions import PostOptions


class AutoMod(ABC) :
	"""This class is used to handle the automod for the forums."""

	@staticmethod
	@abstractmethod
	def config(guildid) :
		"""This function is used to get the config for the forums."""
		data = ConfigData().get_key(guildid, "FORUM")
		return data

	@staticmethod
	@abstractmethod
	async def clean_bumps(thread: discord.Thread, bot: commands.Bot) :
		before = datetime.now() - timedelta(days=3)
		count = 0
		messages = [m async for m in thread.history(limit=1000, before=before, oldest_first=True) if
		            m.author.id == bot.user.id and m.content.lower().startswith("post successfully bumped")]
		logging.info(f"Found {len(messages)} bump messages in {thread.name}")
		for m in messages :
			queue().add(m.delete(), 2)
			count += 1

	@staticmethod
	@abstractmethod
	async def add_relevant_tags(forum, thread, msg, status="new") :
		matched = [tag.name for tag in await TagController().find_tags_in_content(thread, forum, msg)]
		matched.append(status)
		queue().add(TagController().change_tags(forum, thread, matched))
		fm = ", ".join(matched)
		queue().add(thread.send(
			f"Automod has added: `{fm}` to your post. You can edit your tags by right-clicking the thread!"))

	@staticmethod
	@abstractmethod
	async def close_thread(interaction: discord.Interaction) :
		thread: discord.Thread = interaction.channel
		if interaction.channel.type != discord.ChannelType.public_thread :
			await interaction.followup.send("[ERROR] This channel is not a thread.", ephemeral=True)
			return
		if thread.owner_id != interaction.user.id :
			await interaction.followup.send("[ERROR] You do not own this thread.", ephemeral=True)
			return

		async for m in thread.history(limit=1, oldest_first=True) :
			with open('advert.txt', 'w', encoding='utf-16') as f :
				f.write(m.content)
			await interaction.user.send(
				f"Your post `{m.channel}` has successfully been closed. The contents of your adverts:",
				file=discord.File(f.name, f"{m.channel}.txt"))
		await thread.delete()
		os.remove(f.name)

	@staticmethod
	@abstractmethod
	async def info(thread) :
		"""This to remind users about the bumping rules"""
		# This module needs to be fixed; keeps adding too much tags.
		botmessage = await thread.send(
			f"Thank you for posting, you may bump every 3 days with the /forum bump command or simply type bump and users can request to DM in your comments."
			f"\n\n"
			f"To close the advert, please use /forum close", view=PostOptions(forum_controller=AutoMod))

		return botmessage

	@staticmethod
	@abstractmethod
	async def bump(bot, interaction) :
		"""This function is used to bump the post."""
		utc = pytz.UTC
		hours = 72
		thread: discord.Thread = interaction.channel
		current_time = datetime.now(tz=utc)
		messages = thread.history(oldest_first=False)
		count = 0
		user_count = 0
		if "bump" in [x.name.lower() for x in thread.applied_tags] :
			await interaction.followup.send("Your post has not been approved yet. Please wait for staff to review your post.",
			                                ephemeral=True)
			logging.info("Post not approved yet")
			return
		if thread.owner_id != interaction.user.id :
			await interaction.followup.send("You can't bump another's post.", ephemeral=True)
			logging.info("User tried to bump another's post")
			return
		if interaction.channel.type != discord.ChannelType.public_thread :
			return
		async for m in messages :
			if m.author.id == bot.application_id :
				count += 1
			if count == 1 :
				message_time = m.created_at.replace(tzinfo=utc)
				time_diff = current_time - message_time
				if time_diff > timedelta(hours=hours) :
					logging.info("Bump allowed")
					break
				logging.info(f"Cant bump yet with Time diff: {time_diff}")
				time_remaining = timedelta(hours=hours) - time_diff
				timeinfo = f"{int(time_remaining.total_seconds() / 3600)} hours and {int(time_remaining.total_seconds() / 60 % 60)} minutes"
				queue().add(automod_log(bot, interaction.guild_id,
				                        f"User tried to bump too soon in {interaction.channel.mention}: {timeinfo}",
				                        "automodlog"))
				await interaction.followup.send(
					f"Your last bump was within the 72 hours cooldown period in {interaction.channel.mention}, please wait {timeinfo} before bumping again."
					f"\nLast bump: {discord.utils.format_dt(message_time, style='f')} (timediff: {discord.utils.format_dt(message_time, style='R')})",
					ephemeral=True)
				return
			if m.author.id == interaction.user.id :
				user_count += 1
		queue().add(AutoMod.clean_bumps(thread, bot), 2)

		forum = bot.get_channel(thread.parent_id)
		og = await thread.fetch_message(thread.id)
		og_time = og.edited_at.replace(tzinfo=utc) if og.edited_at else None

		if og_time is not None and current_time - og_time > timedelta(
				hours=hours) and user_count <= 0 or og_time is None and user_count <= 0 :
			queue().add(TagController().change_status_tag(thread, ["approved"]), 2)
			queue().add(send_message(interaction.channel,
			                         f"Post successfully bumped and automatically approved. You can bump again in: {discord.utils.format_dt(datetime.now() + timedelta(days=3), style='R')}",
			                         view=PostOptions(AutoMod)))

			queue().add(automod_log(bot, interaction.guild_id,
			                        f"User bumped post in {interaction.channel.mention} and was automatically approved",
			                        "automodlog", message_type="Approval"))
			await interaction.followup.send(
				"You've successfully bumped your post! Your post has been added to the queue, and a follow-up message will be sent with the bump status.",
				ephemeral=True)

			return

		queue().add(TagController().change_status_tag(thread, ["bump"]), 2)
		queue().add(send_message(interaction.channel,
		                         f"Post successfully bumped and awaiting manual review. You may bump again in {discord.utils.format_dt(datetime.now() + timedelta(days=3), style='R')} after a staff member has approved your post.",
		                         view=PostOptions(AutoMod)))
		await interaction.followup.send(
			"You've successfully bumped your post! Your post has been added to the queue, and a follow-up message will be sent with the bump status.",
			ephemeral=True)

	@staticmethod
	@abstractmethod
	async def duplicate(thread: discord.Thread, bot, originalmsg: discord.Message) :
		"""This function is used to check for duplicate posts."""

		forums = AutoMod.config(thread.guild.id)
		if thread.owner_id == 188647277181665280 :
			return
		for c in forums :
			forum = bot.get_channel(c)
			checkdup = await AutomodComponents.check_duplicate(forum, thread, originalmsg)
			if checkdup :
				queue().add(thread.owner.send(
					f"Hi, I am a bot of {thread.guild.name}. Your latest advertisement is too similar to {checkdup.channel.mention}; since 07/01/2023 you're only allowed to have the same advert up once. \n\n"
					f"If you wish to bump your advert, do /forum bump on your advert, if you wish to move then please use /forum close"))
				queue().add(Advert.send_advert_to_user(thread, originalmsg, "Your advert:", "no"))
				queue().add(thread.delete())
				return checkdup

	@staticmethod
	@abstractmethod
	async def reminder(thread: discord.Thread, guildid) :
		"""This function is used to remind users about the bumping rules."""
		reminder = ConfigData().get_key_or_none(guildid, "REMINDER")
		if reminder is None :
			return
		embed = discord.Embed(title="Rule Reminder", description=reminder)
		try :
			await thread.send(embed=embed)
		except discord.NotFound :
			print(f"thread not found, {thread}")
		except discord.Forbidden :
			await asyncio.sleep(5)
			try :
				await thread.send(embed=embed)
			except Exception as e :
				logging.error(e)

	@staticmethod
	@abstractmethod
	async def check_header(message: discord.Message, thread: discord.Thread) -> bool | int | None :
		"""This function is used to check the header."""
		header = re.match(r".?.?.?(All character'?s? are:? \(?([1-9][0-9])([\S\n\t\v ]*)([-|—]{5,100}))", message.content,
		                  flags=re.IGNORECASE)
		if header is None :
			queue().add(message.author.send(
				"""Your advert has been removed because it does not have a header or your header does not follow the template below. Please re-post with a (correct) header.
```text
All characters are (ages)+
(optional) Tags: (Your tags here!)
(optional) Pairings: (Your pairings here!)
(Any other information you want to stand out!)
-----------------------------------
(Your advert here)
```
Common Errors:
* This goes in the body of your post above your advert, not in the title.
* You may have altered 'all characters are', this will cause it to fail as I look for this specifically.
* You may have forgotten the line of dashes (-)
* It is highly recommended to only change the information in the (brackets)
You can use this website to check your header: https://regex101.com/r/HYkkf9/2
This rule went in to effect on the 01/01/2024. If you have any questions, please open a ticket!
"""))
			queue().add(Advert.send_advert_to_user(message, message, "Your advert:", "no"))
			queue().add(thread.delete())
			return True
		age = header.group(2)
		logging.info(age)
		if age.isnumeric() and int(age) < 18 :
			return int(age)

	@staticmethod
	@abstractmethod
	async def check_title(message, thread: discord.Thread) :
		regex_pattern = r'\[[^\s\[\]/\.]+[\/\.][^\s\[\]/\.]+\] .+'
		result = re.search(regex_pattern, thread.name, flags=re.IGNORECASE)
		if result is None :
			queue().add(thread.delete())
			queue().add(message.author.send(
				"""Your advert has been removed because it does not follow our title format. Please re-post with the correct format.
```text
		[pairing/pairing] title here
		Example: [m/m] Hi I am looking for a partner
"""))
			queue().add(Advert.send_advert_to_user(message, message, "Your advert:", "no"))


			return False
		return True

	@staticmethod
	@abstractmethod
	def approval_log(user_id, guild_id, thread_id) :
		"""This function is used to log the approval."""
		ApprovalTransactions.add_approval(user_id, guild_id, thread_id)

	@staticmethod
	@abstractmethod
	async def get_message(thread: discord.Thread) :
		"""Loops through the history of the channel and retrieves the message"""
		if thread.type != discord.ChannelType.public_thread :
			return False
		try :
			message = await thread.fetch_message(thread.id)
		except discord.NotFound :
			await asyncio.sleep(10)
			message = await thread.fetch_message(thread.id)
		return message
