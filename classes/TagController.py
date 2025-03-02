"""In this file all ForumTag related functions will be stored, this includes the creation of tags, the deletion of tags, the editing of tags, and the checking of tags. This file will also contain the TagController class which will be used to create new tag types."""
import logging
from abc import ABC, abstractmethod
import re

from discord import ForumChannel, ForumTag, Message, Thread

from classes.queue import queue


class TagController():


	async def get_status_tags(self, forum: ForumChannel, tags: list = ("new", "approved", "bump")) -> list[ForumTag] :
		"""This function is used to find the status tags in the forum."""
		found_tags = []
		for a in forum.available_tags :
			if a.name.lower() in tags :
				found_tags.append(a)
		return found_tags


	async def change_status_tag(self, thread: Thread, tags: list =("new")) :
		"""This function checks if there is space for the status tag, if not it removes one of the other tags"""
		tags = thread.applied_tags
		remove_tags = self.get_status_tags(thread.parent)
		if not remove_tags and len(tags) >= 5 :
			remove_tags = [tags[0]]
		await self.change_tags(
			thread.parent,
			thread,
			tags,
			remove_tags
		)

	@staticmethod
	@abstractmethod
	async def change_tags(forum: ForumChannel, thread: Thread, added_tags: str | list,
	                      removed_tags: str | list = ()) :
		logging.info(f"changing tags for {thread.name} adding {added_tags} and {removed_tags}")
		if len(thread.applied_tags) >= 5:
			logging.info(f"Too many tags for {thread.name}")
			return
		if isinstance(added_tags, str) :
			added_tags = added_tags.lower().split()
		if isinstance(removed_tags, str) :
			removed_tags = removed_tags.lower().split()
		for a in forum.available_tags :
			if a.name.lower() in added_tags :
				logging.info(f"Adding {a.name} to {thread.name}")
				queue().add(thread.add_tags(a))
			if a.name.lower() in removed_tags :
				logging.info(f"Removing {a.name} from {thread.name}")
				queue().add(thread.remove_tags(a))

	@staticmethod
	@abstractmethod
	async def find_tags_in_content(thread: Thread, forum: ForumChannel, message: Message) :
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

