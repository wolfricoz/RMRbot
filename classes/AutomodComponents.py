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

