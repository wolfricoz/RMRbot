import asyncio
import logging
import re
from abc import ABC, abstractmethod

import discord
from Levenshtein import ratio

from classes.queue import queue


class AutomodComponents(ABC):

    @staticmethod
    @abstractmethod
    async def check_duplicate(forum, thread, originalmsg):
        found = None
        for a in forum.threads:
            if found:
                break
            if a.id == thread.id:
                continue
            if a.owner == thread.owner:
                msg: discord.Message = await a.fetch_message(a.id)
                r = ratio(originalmsg.content, msg.content)
                if r >= 0.7:
                    found = msg
                    break
        async for x in forum.archived_threads(limit=1000):
            if found is not None:
                break
            if x.id == thread.id:
                continue
            if x.owner == thread.owner:
                msg: discord.Message = await x.fetch_message(x.id)
                r = ratio(originalmsg.content, msg.content)
                if r >= 0.7:
                    found = msg
                    break
        return found

    @staticmethod
    @abstractmethod
    async def tags(thread, forum, message):
        skip = ['New', 'Approved', 'Bump']
        matched = []
        count = 0
        for r in forum.available_tags:
            limitreg = re.compile(fr"(limit.*?{r}|no.*?{r}|dont.*?{r}|don\'t.*?{r})", flags=re.I)
            limitmatch = limitreg.search(message.content)
            if limitmatch:
                continue
            if r.name in skip:
                pass
            if count >= 3:
                break
            tagreg = re.compile(rf"{r.name}", flags=re.I)
            match = tagreg.search(message.content)
            matcht = tagreg.search(thread.name)
            if match:
                matched.append(r)
                count += 1
            if matcht:
                matched.append(r)
                count += 1
        return matched

    @staticmethod
    @abstractmethod
    async def change_tags(forum: discord.ForumChannel, thread: discord.Thread, added_tags: str | list, removed_tags: str | list, verify=False):
        logging.info(f"changing tags for {thread.name} adding {added_tags} and {removed_tags}")

        if isinstance(added_tags, str):
            added_tags = added_tags.lower().split()
        if isinstance(removed_tags, str):
            removed_tags = removed_tags.lower().split()
        for a in forum.available_tags:
            if a.name.lower() in added_tags:
                queue().add(thread.add_tags(a))
            if a.name.lower() in removed_tags:
                queue().add(thread.remove_tags(a))

        if not verify:
            return
        await asyncio.sleep(3)
        if isinstance(added_tags, list):
            added_tags = added_tags[0]
        if added_tags.lower() not in [x.name.lower() for x in thread.applied_tags]:
            queue().add(AutomodComponents.change_tags(forum, thread, added_tags, removed_tags, verify=False))