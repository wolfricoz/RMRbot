import re
from abc import ABC, abstractmethod

import discord
from Levenshtein import ratio


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
    async def change_tags_bump(forum, thread):
        for a in forum.available_tags:
            if a.name == "Bump":
                await thread.add_tags(a)
            if a.name == "Approved" or a.name == "New":
                await thread.remove_tags(a)

    @staticmethod
    @abstractmethod
    async def change_tags_approve(forum, thread):
        for a in forum.available_tags:

            if a.name == "Approved":
                await thread.add_tags(a)
            if a.name == "Bump" or a.name == "New":
                await thread.remove_tags(a)
