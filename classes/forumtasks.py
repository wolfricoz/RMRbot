import logging
from collections.abc import AsyncIterator

import discord
from discord import Thread

from classes.AutomodComponents import AutomodComponents
from classes.Support.discord_tools import fetch_message_or_none
from classes.queue import queue


class ForumTasks() :

	def __init__(self, forum: discord.ForumChannel) :
		# setting up the data all the underlying functions need to reduce api calls.
		self.forum: discord.ForumChannel = forum
		self.threads: list[discord.Thread] = forum.threads
		self.archived: AsyncIterator[Thread] = forum.archived_threads(limit=None)
		self.members: list[int] = [member.id for member in forum.guild.members]

	async def start(self) :
		"""This starts the checking of the forum and will walk through all the tasks."""
		queue().add(self.recover_archived_posts())
		for thread in self.threads :
			queue().add(self.cleanup_forum(thread), priority=0)
			queue().add(self.check_status_tag(thread))

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
		if thread.owner is None or thread.owner.id not in self.members :
			logging.info(f"{thread.name}'s user left, cleaning up")
			queue().add(thread.delete())
			return
		message = await fetch_message_or_none(thread, thread.id)
		if message is None or message.author not in message.guild.members :
			logging.info(
				f"Deleting thread {thread.name} from {self.forum.name} in {thread.guild.name} as the starter message is missing or because the author has left..")
			try :
				await thread.delete()
			except Exception as e :
				logging.error(
					f"Error deleting thread {thread.name} in {self.forum.name} in {thread.guild.name} due to {e}")


	async def check_user(self) :
		raise NotImplemented


	async def check_post(self) :
		raise NotImplemented


	async def send_reminder(self, archived_thread) :
		post_reminder = "Your advert has been reopened after discord archived it. If this advert is no longer relevant, please close it with </forum close:1096183254605901976> if it is no longer relevant. Please bump the post in 3 days with </forum bump:1096183254605901976>. After three reopen reminders your post will be automatically removed."
		try :
			if permissions.check_admin(archived_thread.owner) or regex.search(channel.name) is None :
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
