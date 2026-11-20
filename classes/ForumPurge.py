"""Removes every advert from a guild's search forums and sends each one back to its author.

Used by /forum purge and by the yearly purge dates (see classes/PurgeSchedule.py). The DMs and deletes go through the
queue; on_complete is queued after them, so it runs once the last advert is gone. Deleting the threads also takes the
adverts off the website (Website.on_raw_thread_delete).
"""
import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone

import discord
from discord.ext import commands

from classes import PurgeSchedule
from classes.Support.LogTo import automod_log
from classes.queue import queue
from databases.current import PurgeDates
from databases.exceptions.KeyNotFound import KeyNotFound
from databases.transactions.ConfigData import ConfigData
from databases.transactions.PurgeTransactions import PurgeTransactions

SCHEDULED_REMINDER = ("Your advert `{name}` has been removed in the scheduled search forum purge. You can repost it once "
                      "the purge has finished. Thank you for using RMR! Here is your advert:")
MANUAL_REMINDER = ("Your advert `{name}` has been removed due to a purge; you may repost it once the purge has finished. "
                   "Thank you for using RMR!\nYour advert:")

# Called with the finished ForumPurge, once its last advert is removed.
OnComplete = Callable[["ForumPurge"], Awaitable[None]]

# The hourly loop and /forum purgedates check can overlap; one at a time, so a purge can't start twice.
_check_lock = asyncio.Lock()


class ForumPurge :
	"""Removes all adverts from a guild's search forums and DMs them back to their authors."""

	def __init__(self, bot: commands.Bot, guild: discord.Guild) :
		self.bot = bot
		self.guild = guild
		self.removed = 0
		self.failed_dms: list[str] = []
		self.errors: list[str] = []

	def forums(self) -> list[discord.ForumChannel] :
		"""The guild's search forums, from the FORUM config."""
		forums = []
		for forum_id in ConfigData().get_key_or_none(self.guild.id, "FORUM") or [] :
			forum = self.bot.get_channel(int(forum_id))
			if isinstance(forum, discord.ForumChannel) :
				forums.append(forum)
		return forums

	async def run(self, reminder: str, on_complete: OnComplete | None = None, skip_pinned: bool = False,
	              keep_owner_id: int | None = None) -> int :
		"""Queues the removal of every advert; returns how many were queued. reminder is formatted with the thread's
		name and sent before the advert's text."""
		for forum in self.forums() :
			threads = list(forum.threads)
			threads += [thread async for thread in forum.archived_threads(limit=None)]
			for thread in threads :
				if skip_pinned and thread.flags.pinned :
					continue
				if keep_owner_id is not None and thread.owner_id == keep_owner_id :
					continue
				await self._queue_removal(thread, reminder.format(name=thread.name))
		if on_complete is not None :
			queue().add(self._complete(on_complete), 0)
		return self.removed

	async def _queue_removal(self, thread: discord.Thread, reminder: str) :
		try :
			message = await thread.fetch_message(thread.id)
		except discord.NotFound :
			# The advert itself is already gone; only the empty thread is left.
			queue().add(thread.delete(), 0)
			return
		except Exception as e :
			logging.error(f"[Purge] couldn't fetch {thread.name} ({thread.id}): {e}", exc_info=True)
			self.errors.append(f"{thread.mention}: {e}")
			return
		queue().add(self._return_advert(message, reminder), 0)
		queue().add(thread.delete(), 0)
		self.removed += 1

	async def _return_advert(self, message: discord.Message, reminder: str) :
		"""DMs the reminder and the advert's text to its author, in pieces under Discord's limit."""
		try :
			await message.author.send(reminder)
			for start in range(0, len(message.content), 1950) :
				await message.author.send(message.content[start :start + 1950])
		except (discord.Forbidden, discord.HTTPException) as e :
			logging.info(f"[Purge] couldn't DM {message.author} ({message.author.id}): {e}")
			self.failed_dms.append(message.author.mention)

	def summary(self) -> str :
		"""How the purge went, for the logs."""
		text = f"Purge completed, {self.removed} adverts removed."
		if self.failed_dms :
			text += f"\nCouldn't DM {len(self.failed_dms)} authors their advert: {', '.join(self.failed_dms)}"
		if self.errors :
			text += f"\nCouldn't remove {len(self.errors)} adverts:\n" + "\n".join(f"- {error}" for error in self.errors)
		return text

	async def _complete(self, on_complete: OnComplete) :
		await on_complete(self)


async def check_purge_dates(bot: commands.Bot, report_missed: bool = False) :
	"""Posts the announcements and starts the purges that are due. Runs every hour; report_missed also logs purges
	that were missed while the bot was offline, which the first run after a start does."""
	async with _check_lock :
		await _check_purge_dates(bot, report_missed)


async def _check_purge_dates(bot: commands.Bot, report_missed: bool) :
	now = datetime.now(timezone.utc)
	for entry in PurgeTransactions().get_all() :
		guild = bot.get_guild(entry.guild)
		if guild is None :
			continue
		try :
			if PurgeSchedule.should_announce(entry.day, entry.month, entry.announced_at, now) :
				await announce_purge(bot, guild, entry, now)
			status = PurgeSchedule.purge_status(entry.day, entry.month, entry.created_at, entry.last_purged_at, now)
			if status == "due" :
				await start_scheduled_purge(bot, guild, entry)
			elif status == "missed" and report_missed :
				latest = PurgeSchedule.latest_occurrence(entry.day, entry.month, now)
				if now - latest <= PurgeSchedule.REPORT_MISSED :
					await log_purge(bot, guild.id, f"The purge of {PurgeSchedule.format_date(entry.day, entry.month)} "
					                               f"was missed while the bot was offline; it runs again next year.")
		except Exception as e :
			logging.error(f"[Purge] checking purge date {entry.id} of {guild.name} failed: {e}", exc_info=True)


async def announce_purge(bot: commands.Bot, guild: discord.Guild, entry: PurgeDates, now: datetime) :
	"""Posts the 7-day announcement in the purgeannouncement channel."""
	# Marked first: without a channel it would otherwise be retried, and logged, every hour.
	PurgeTransactions().set_announced(entry.id)
	date = PurgeSchedule.format_date(entry.day, entry.month)
	channel_id = ConfigData().get_key_or_none(guild.id, "purgeannouncement")
	channel = bot.get_channel(int(channel_id)) if channel_id else None
	if channel is None :
		await log_purge(bot, guild.id, f"The purge of {date} wasn't announced: set the purgeannouncement channel with "
		                               f"/config channels.")
		return
	help_channel = ConfigData().get_key_or_none(guild.id, "helpchannel")
	text = PurgeSchedule.announcement_text(PurgeSchedule.next_occurrence(entry.day, entry.month, now),
	                                       [forum.mention for forum in ForumPurge(bot, guild).forums()],
	                                       int(help_channel) if help_channel else None)
	await channel.send(text, allowed_mentions=discord.AllowedMentions(everyone=True))
	await log_purge(bot, guild.id, f"The purge of {date} has been announced in {channel.mention}.")


async def start_scheduled_purge(bot: commands.Bot, guild: discord.Guild, entry: PurgeDates) :
	"""Queues the purge; the check mark moves to this date once its last advert is removed."""
	# Marked first, so the next hourly check doesn't start it again while the queue works through it.
	PurgeTransactions().set_started(entry.id)
	date = PurgeSchedule.format_date(entry.day, entry.month)

	async def done(purge: ForumPurge) :
		PurgeTransactions().set_checked(entry.id)
		await log_purge(bot, guild.id, f"[Scheduled purge of {date}] {purge.summary()}")

	count = await ForumPurge(bot, guild).run(SCHEDULED_REMINDER, on_complete=done, skip_pinned=True)
	await log_purge(bot, guild.id, f"The scheduled purge of {date} has started: {count} adverts queued for removal.")


async def log_purge(bot: commands.Bot, guild_id: int, message: str) :
	"""Logs to automodlog; automod_log raises when that channel isn't set."""
	try :
		await automod_log(bot, guild_id, message, "automodlog", message_type="PURGE")
	except KeyNotFound :
		logging.warning(f"[Purge] {guild_id} has no automodlog channel: {message}")
