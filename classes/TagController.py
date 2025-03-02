"""In this file all ForumTag related functions will be stored, this includes the creation of tags, the deletion of tags, the editing of tags, and the checking of tags. This file will also contain the TagController class which will be used to create new tag types."""

from abc import ABC, abstractmethod
from discord import ForumChannel, ForumTag, Thread


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
		await AutomodComponents.change_tags(
			thread.parent,
			thread,
			tags,
			remove_tags
		)

	@staticmethod
	@abstractmethod
	async def change_tags(forum: discord.ForumChannel, thread: discord.Thread, added_tags: str | list,
	                      removed_tags: str | list, verify=False) :
		logging.info(f"changing tags for {thread.name} adding {added_tags} and {removed_tags}")

		if isinstance(added_tags, str) :
			added_tags = added_tags.lower().split()
		if isinstance(removed_tags, str) :
			removed_tags = removed_tags.lower().split()
		for a in forum.available_tags :
			if a.name.lower() in added_tags :
				queue().add(thread.add_tags(a))
			if a.name.lower() in removed_tags :
				queue().add(thread.remove_tags(a))

		if not verify :
			return
		await asyncio.sleep(3)
		if isinstance(added_tags, list) :
			added_tags = added_tags[0]
		if added_tags.lower() not in [x.name.lower() for x in thread.applied_tags] :
			queue().add(AutomodComponents.change_tags(forum, thread, added_tags, removed_tags, verify=False))