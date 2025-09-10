"""In this file all ForumTag related functions will be stored, this includes the creation of tags, the deletion of tags, the editing of tags, and the checking of tags. This file will also contain the TagController class which will be used to create new tag types."""
import asyncio
import logging
from abc import ABC, abstractmethod
import re

import discord
from discord import ForumChannel, ForumTag, Message, Thread

from classes.Support.LogTo import automod_log
from classes.queue import queue


class TagController():
	"""This class is used to handle the tags for the forums."""


	# WARNING: You can only apply tags once in the same function, otherwise it'll overwrite the previous tag.

	# New workflow: Initialize class > add tags > commit.

	def __init__(self, thread: discord.Thread):
		self.thread = thread
		self.status = ""
		self.current_tags = [tag.name.lower() for tag in thread.applied_tags]
		self.added_tags = [] # these tags need to be added, but aren't final yet
		self.new_tags = [] # these are the final tags which will be set as: status + 4 tags.


	async def add_tags(self, tags: str | list['str']):
		if isinstance(tags, str):
			self.added_tags.append(tags)
		old = set(self.added_tags)
		new = set([tag.lower() for tag in tags])
		self.added_tags = self.added_tags + (list(new - old))

	async def remove_tags(self, tags: str | list['str']):
		pass

	async def calculate_finalized_tags(self):
		pass

	async def commit_tags(self):
		pass


	async def get_status_tags(self, forum: ForumChannel, tags: list = ("new", "approved", "bump")) -> list[ForumTag] :
		"""This function is used to find the status tags in the forum."""
		found_tags = []
		for a in forum.available_tags :
			if a.name.lower() in tags :
				found_tags.append(a)
		return found_tags


	async def change_status_tag(self, bot, thread: Thread, tags: list =("new"), attempt = 0) :
		"""This function checks if there is space for the status tag, if not it removes one of the other tags"""
		remove_tags = [status for status in ["new", "approved", "bump"] if status not in tags]
		logging.info(remove_tags)
		applied_tags = thread.applied_tags
		if not remove_tags and len(applied_tags) >= 5 :
			remove_tags = [applied_tags[0]]
		await self.change_tags(
			thread.parent,
			thread,
			tags,
			remove_tags
		)
		await asyncio.sleep(1)
		if await self.verify_tags(thread) is False:
			logging.warning(f"Thread has multiple status tags, restarting the process (attempt {attempt})")
			if attempt > 3 :
				queue().add(automod_log(bot, thread.guild.id,
				                        f"Failed to apply the tags to {thread.name} after 3 attempts, please check the thread manually.",
				                        "automodlog"), priority=0)
				logging.error(f"Failed to apply the tags to {thread.name} after 3 attempts, please check the thread manually.")
				return
			await self.change_status_tag(bot, thread, tags, attempt + 1)


	async def change_tags(self, forum: ForumChannel, thread: Thread, added_tags: str | list[str],
	                      removed_tags: str | list[str] = ()) :
		apply = []
		remove = []
		logging.info(f"changing tags for {thread.name} adding {added_tags} and removing {removed_tags}")
		if isinstance(added_tags, str) :
			added_tags = added_tags.lower().split()
		if isinstance(removed_tags, str) :
			removed_tags = removed_tags.lower().split()
		added_tags = [a.lower() for a in added_tags]
		removed_tags = [a.lower() for a in removed_tags]
		for a in forum.available_tags :
			if a.name.lower() in added_tags :
				apply.append(a)
			if a.name.lower() in removed_tags :
				remove.append(a)
		queue().add(self.remove_tags(thread, remove))
		queue().add(self.add_tags(thread, apply))
		logging.info(f"Tags changed for {thread.name}")

	async def find_tags_in_content(self, thread: Thread, forum: ForumChannel, message: Message) :
		skip = ['New', 'Approved', 'Bump']
		matched = []
		count = len(thread.applied_tags)
		for r in forum.available_tags :
			limitreg = re.compile(fr"(limit.*?{r}|no.*?{r}|dont.*?{r}|don\'t.*?{r})", flags=re.I)
			limitmatch = limitreg.search(message.content)
			if limitmatch :
				continue
			if r.name in skip :
				pass
			if count >= 4 :
				break
			tagreg = re.compile(rf"{r.name}", flags=re.I)
			match = tagreg.search(message.content)
			matcht = tagreg.search(thread.name)
			if match :
				matched.append(r)
				count += 1
			if matcht :
				matched.append(r)
				count += 1
		return matched

	async def add_tags(self, thread,  tags: list[ForumTag]):
		if not tags or len(tags) < 1:
			return
		if len(thread.applied_tags) >= 5:
			logging.info(f"too many tags for {thread.name}, removing {len(tags)} tags")
			await self.remove_tags(thread, thread.applied_tags[:len(tags)])
		logging.info(f"adding {', '.join([tag.name for tag in tags])} tags for {thread.name}")
		queue().add(thread.add_tags(*tags))

	async def remove_tags(self, thread, tags: list[ForumTag]):
		if not tags or len(tags) < 1:
			logging.info("No tags were supplied to remove")
			return
		logging.info(f"Removing tags {', '.join([tag.name for tag in tags])} from {thread.name}")
		queue().add(thread.remove_tags(*tags))

	async def verify_tags(self, thread: Thread):
		"""Checks if the thread does not have multiple status tags, such as new, approved, bump."""
		tags = [tag.name.lower() for tag in thread.applied_tags]
		status_tags = ["new", "approved", "bump"]
		status_count = 0
		for tag in tags:
			if status_count > 1:
				return False
			if tag in status_tags:
				status_count += 1
		return True

