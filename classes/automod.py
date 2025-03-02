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
from classes.databaseController import ConfigData
from classes.queue import queue


class ForumAutoMod(ABC) :
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
		messages = [m async for m in thread.history(limit=1000, before=before, oldest_first=True) if m.author.id == bot.user.id and m.content.lower().startswith("post successfully bumped")]
		logging.info(f"Found {len(messages)} bump messages in {thread.name}")
		for m in messages :
			queue().add(m.delete(), 2)
			count += 1

	@staticmethod
	@abstractmethod
	async def get_status_tags(forum, thread, tag="new") -> discord.ForumTag :
		"""This function is used to find the status tags in the forum."""
		for a in forum.available_tags :
			if a.name.lower() == tag.lower() :
				return a

	@staticmethod
	@abstractmethod
	async def add_relevant_tags(forum, thread, msg) :
		matched = await AutomodComponents.tags(thread, forum, msg)
		counted_tags = [await ForumAutoMod.get_status_tags(forum, thread)]
		if matched :
			count = 0
			maxtags = 5 - len(thread.applied_tags) + len(counted_tags)
			for x in matched :
				if x in thread.applied_tags :
					continue
				if count >= maxtags :
					break
				counted_tags.append(x)
				count += 1

		fm = ', '.join([x.name for x in counted_tags])
		queue().add(thread.send(
			f"Automod has added: `{fm}` to your post. You can edit your tags by right-clicking the thread!"))
		queue().add(thread.add_tags(*counted_tags, reason=f"Automod applied {fm}"))
		logging.info(f"[role change] added {', '.join([x.name for x in counted_tags])}")


	@staticmethod
	@abstractmethod
	async def change_status_tag(thread: discord.Thread, tags=("new")) :
		"""This function checks if there is space for the status tag, if not it removes one of the other tags"""
		tags = thread.applied_tags
		status = ["new", "approved", "bump"]
		remove_tags = []
		for r in status :
			if r in tags :
				remove_tags.append(r)
		if not remove_tags and len(tags) >= 5 :
			remove_tags.append(tags[0])
		await AutomodComponents.change_tags(
			thread.parent,
			thread,
			tags,
			remove_tags
		)


	@staticmethod
	@abstractmethod
	async def info(thread) :
		"""This to remind users about the bumping rules"""
		# This module needs to be fixed; keeps adding too much tags.
		botmessage = await thread.send(
			f"Thank you for posting, you may bump every 3 days with the /forum bump command or simply type bump and users can request to DM in your comments."
			f"\n\n"
			f"To close the advert, please use /forum close")

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
			await interaction.followup.send("Your post has not been approved yet. Please wait for staff to review your post.")
			logging.info("Post not approved yet")
			return
		if thread.owner_id != interaction.user.id :
			await interaction.followup.send("You can't bump another's post.")
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
				                  f"User tried to bump too soon in {interaction.channel.mention}: {timeinfo}", "automodlog"))
				await interaction.followup.send(
					f"Your last bump was within the 72 hours cooldown period in {interaction.channel.mention}, please wait {timeinfo} before bumping again."
					f"\nLast bump: {discord.utils.format_dt(message_time, style='f')} (timediff: {discord.utils.format_dt(message_time, style='R')})")
				return
			if m.author.id == interaction.user.id :
				user_count += 1
		queue().add(ForumAutoMod.clean_bumps(thread, bot), 2)


		forum = bot.get_channel(thread.parent_id)
		og = await thread.fetch_message(thread.id)
		og_time = og.edited_at.replace(tzinfo=utc) if og.edited_at else None
		try :
			if og_time is not None and current_time - og_time > timedelta(hours=hours) and user_count <= 0 or og_time is None and user_count <= 0 :
				queue().add(AutomodComponents.change_tags(forum, thread, "approved", ["bump", "new"], verify=True), 2)
				queue().add(send_message(interaction.channel, "Post successfully bumped and automatically approved"))

				queue().add(automod_log(bot, interaction.guild_id,
				                  f"User bumped post in {interaction.channel.mention} and was automatically approved",
				                  "automodlog", message_type="Approval"))
				await interaction.followup.send("You've successfully bumped your post! Your post has been added to the queue, and a follow-up message will be sent with the bump status.")

				return
		except Exception as e :
			logging.error(e)
		queue().add(AutomodComponents.change_tags(forum, thread, "bump", ["approved", "new"], verify=True), 2)
		queue().add(send_message(interaction.channel, "Post successfully bumped and awaiting manual review"))
		await interaction.followup.send("You've successfully bumped your post! Your post has been added to the queue, and a follow-up message will be sent with the bump status.")

	@staticmethod
	@abstractmethod
	async def duplicate(thread: discord.Thread, bot, originalmsg: discord.Message) :
		"""This function is used to check for duplicate posts."""

		forums = ForumAutoMod.config(thread.guild.id)
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
	async def check_header(message: discord.Message, thread: discord.Thread) -> bool | None :
		"""This function is used to check the header."""
		header = re.match(r"(All character'?s? are \(?[1-9][0-9])([\S\n\t\v ]*)([-|—]{5,100})", message.content,
		                  flags=re.IGNORECASE)
		pattern = re.compile(r'\bsearch\b', re.IGNORECASE)
		search = pattern.search(thread.parent.name)
		if search is None :
			return
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

	@staticmethod
	@abstractmethod
	def approval_log(interaction) :
		"""This function is used to log the approval."""
		file_name = f"config/approvals{datetime.now().strftime('%m-%y')}.txt"
		if os.path.isfile(file_name) is False :
			with open(file_name, 'w') as f :
				f.write('Advert Approvals')
		with open(file_name, 'a') as f :
			f.write(
				f"\n{datetime.now().strftime('%m/%d/%Y %I:%M %p')}: {interaction.user} has approved post '{interaction.channel}'")

	@staticmethod
	@abstractmethod
	async def get_message(thread: discord.Thread) :
		"""Loops through the history of the channel and retrieves the message"""
		if thread.type != discord.ChannelType.public_thread :
			return False
		messages = thread.history(limit=10, oldest_first=True)
		async for message in messages :
			if message.id == thread.id :
				return message
		else :
			return thread.starter_message
