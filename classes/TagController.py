"""In this file all ForumTag related functions will be stored, this includes the creation of tags, the deletion of tags, the editing of tags, and the checking of tags. This file will also contain the TagController class which will be used to create new tag types."""
import logging
from abc import ABC, abstractmethod
import re

from discord import ForumChannel, ForumTag, Message, Thread

from classes.queue import queue


class TagController():
	"""This class is used to handle the tags for the forums."""

	# WARNING: You can only apply tags once in the same function, otherwise it'll overwrite the previous tag.

	async def get_status_tags(self, forum: ForumChannel, tags: list = ("new", "approved", "bump")) -> list[ForumTag] :
		"""This function is used to find the status tags in the forum."""
		found_tags = []
		for a in forum.available_tags :
			if a.name.lower() in tags :
				found_tags.append(a)
		return found_tags


	async def change_status_tag(self, thread: Thread, tags: list =("new")) :
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

