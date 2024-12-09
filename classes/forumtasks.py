import asyncio
import logging
from collections.abc import AsyncIterator
from itertools import count
import re

import discord
from discord import Thread
from discord.ext import commands

from classes import permissions
from classes.AutomodComponents import AutomodComponents
from classes.Support.LogTo import automod_log
from classes.Support.discord_tools import delete_message, fetch_message_or_none, send_message
from classes.queue import queue


class ForumTasks :

	def __init__(self, forum: discord.ForumChannel, bot: commands.Bot) :
		# setting up the data all the underlying functions need to reduce api calls.
		self.forum: discord.ForumChannel = forum
		self.threads: list[discord.Thread] = forum.threads
		self.archived: AsyncIterator[Thread] = forum.archived_threads(limit=None)
		self.members: list[int] = [member.id for member in forum.guild.members]
		self.bot = bot

	async def start(self) :
		"""This starts the checking of the forum and will walk through all the tasks."""
		await self.recover_archived_posts()
		for thread in self.threads :
			queue().add(self.cleanup_forum(thread), priority=0)
			queue().add(self.check_status_tag(thread), priority=0)
			queue().add(self.check_abandoned_status(thread), priority=0)

	async def recover_archived_posts(self) :
		"""Loop through archived posts and send a reminder there."""
		logging.info("recovering archived posts")
		async for archived_thread in self.archived :
			if archived_thread.owner.id not in self.members :
				queue().add(archived_thread.delete(), priority=0)
				continue
			if archived_thread.archived is False :
				continue
			queue().add(self.send_reminder(archived_thread), priority=0)

	async def check_status_tag(self, thread) :

		tags = [tag.name.lower() for tag in thread.applied_tags]
		result = list({'new', 'approved', 'bump'}.intersection(tags))
		if not any(result) :
			queue().add(AutomodComponents.change_tags(self.forum, thread, "new", ["approved", "bump"]))



	async def cleanup_forum(self, thread: discord.Thread) :
		logging.info("Cleaning up the forum")
		if self.check_user(thread.owner) is None:
			logging.info(f"{thread.name}'s user left, cleaning up")
			queue().add(thread.delete())
			return




	def check_user(self, member: discord.Member) -> None | discord.Member:
		if member is None:
			return None
		if member.id not in self.members:
			return None
		return member


	async def check_post(self, thread) :
		"""Check if the main message still exists, if not it deletes the post"""
		message = await fetch_message_or_none(thread, thread.id)
		if message is None:
			logging.info(
				f"Deleting thread {thread.name} from {self.forum.name} in {thread.guild.name} as the starter message is missing or because the author has left..")
			queue().add(delete_message(message))

	async def check_abandoned_status(self, thread):
		count = 0
		pattern = r"<@\d+> Your advert has been reopened after discord archived it\."

		async for m in thread.history(limit=None) :

			if count >= 3 :
				# return
				message = await fetch_message_or_none(thread, thread.id)
				if message is None :
					queue().add(thread.delete(), priority=0)
					return
				queue().add(send_message(message.author,
				                         f"Your post in {thread.name} has been removed due to not being bumped "
				                         f"after 3 reminders. Here is the content: {message.content}"),
				            priority=0)
				queue().add(automod_log(self.bot, thread.guild.id,
				                        f"`[ABANDONED POST CHECK]{thread.name}` by {thread.owner.mention} has been "
				                        f"reminded three times to bump their post but failed to do so. ",
				                        "automodlog", message_type="CLEANUP"), priority=0)
				queue().add(thread.delete(), priority=0)
				break
			if m.content is None :
				continue
			if re.search(pattern, m.content) and m.author.id == self.bot.user.id :
				count += 1
				continue
			return

	async def send_reminder(self, archived_thread) :
		post_reminder = "Your advert has been reopened after discord archived it. If this advert is no longer relevant, please close it with </forum close:1096183254605901976> if it is no longer relevant. Please bump the post in 3 days with </forum bump:1096183254605901976>. After three reopen reminders your post will be automatically removed."
		try :
			if permissions.check_admin(archived_thread.owner):
				try :
					message = await archived_thread.send(post_reminder)
					queue().add(message.delete(), priority=0)
				except discord.Forbidden or discord.NotFound :
					pass
				return
			await archived_thread.send(f"{archived_thread.owner.mention} {post_reminder}")
		except AttributeError :
			await archived_thread.send(post_reminder)
		except Exception as e :
			logging.error(f"Failed to inform {archived_thread.name}: {e}")
