"""The list of adverts waiting for staff approval, per automod forum. Each advert is labelled New (a fresh post) or
Bump (bumped with changes, back in review). Staff see the list in two places that the bot keeps up to date as adverts
are approved, removed or posted:

* the pending board: one message per forum in the channel set as `pendingboard` (/config channels). Its message ids
  are kept in the config (PENDINGBOARD-<forum id>), so the board carries on after a restart;
* the DMs /forum pendingadverts sends. These are tracked in memory only: after a restart, older DMs stop updating.

The same update also crosses out, in the `pendingapproval` channel, the lines about adverts that are no longer
pending: approved (with the approver, when the bot saw who it was) or removed. Only the last LOG_HISTORY messages there
are checked. The bot posting there also triggers an update, so a line that is out of date by the time it is posted
(the daily list goes through the queue) is crossed out too. Approvers and removals are remembered in memory, so after a restart lines are crossed out without the
approver, and removals from before the restart aren't crossed out.

Updates are batched per guild, so a burst of approvals edits each message once. Ported from mousebot."""
import asyncio
import logging
import re
from datetime import datetime, timedelta

import discord
from discord.ext import commands

from databases.transactions.ConfigData import ConfigData
from databases.transactions.ConfigTransactions import ConfigTransactions
from resources.enums.ForumStatus import ForumStatus

# Seconds to wait after a change before editing, so changes close together become one edit.
DEBOUNCE = 10
# How long a /forum pendingadverts DM keeps updating.
DM_LIFETIME = timedelta(hours=24)
# Embed descriptions are limited to 4096 characters.
DESCRIPTION_LIMIT = 4000
# How many of the latest messages in the pendingapproval channel get their lines crossed out.
LOG_HISTORY = 200
# Messages are limited to 2000 characters; the bot sends at most 1800 per message, leaving room for the markers.
MESSAGE_LIMIT = 2000
# How long approvers and removed adverts are remembered for crossing out.
MEMORY = timedelta(days=7)
# The advert a log line is about: its link (thread.jump_url) or its mention (<#id>).
THREAD_REFERENCE = re.compile(r"discord\.com/channels/\d+/(\d+)|<#(\d+)>")


class PendingAdverts :
	"""Builds the pending adverts list and keeps the pending board and the pending list DMs current."""

	# guild id -> [(DM message, forum id, sent at)]
	_dms: dict[int, list[tuple[discord.Message, int, datetime]]] = {}
	# guild id -> the scheduled update. Changes while it waits or runs are picked up by it, never by a second one, so
	# two updates can't both post a board message.
	_timers: dict[int, asyncio.Task] = {}
	# Guilds with changes the running update may have missed.
	_dirty: set[int] = set()
	# thread id -> (approver id, approved at): who approved the advert, for the crossed out lines.
	_approvers: dict[int, tuple[int, datetime]] = {}
	# thread id -> removed at: adverts whose thread was deleted.
	_removed: dict[int, datetime] = {}

	@staticmethod
	def _remember(store: dict, thread_id: int, value) :
		"""Stores value for the thread and forgets entries older than MEMORY. Values are tuples ending in, or are, the
		time they were stored."""
		now = discord.utils.utcnow()
		for key in [key for key, stored in store.items()
		            if now - (stored[-1] if isinstance(stored, tuple) else stored) > MEMORY] :
			del store[key]
		store[thread_id] = value

	@staticmethod
	def note_approval(thread_id: int, approver_id: int) :
		"""Remembers who approved the advert, so its pending lines are crossed out with their name."""
		PendingAdverts._remember(PendingAdverts._approvers, thread_id, (approver_id, discord.utils.utcnow()))

	@staticmethod
	def is_log_message(bot: commands.Bot, message: discord.Message) -> bool :
		"""Whether the bot posted the message in the guild's pendingapproval channel."""
		if message.guild is None or bot.user is None or message.author.id != bot.user.id :
			return False
		try :
			channel_id = ConfigData().get_key_or_none(message.guild.id, "PENDINGAPPROVAL")
		except KeyError :
			return False
		return channel_id is not None and int(channel_id) == message.channel.id

	@staticmethod
	def note_removed(thread_id: int) :
		"""Remembers that the advert's thread was deleted, so its pending lines are crossed out as removed."""
		PendingAdverts._remember(PendingAdverts._removed, thread_id, discord.utils.utcnow())

	@staticmethod
	def forums(bot: commands.Bot, guild: discord.Guild) -> list[discord.ForumChannel] :
		"""The guild's automod forums (/config forums)."""
		try :
			forum_ids = ConfigData().get_key(guild.id, "FORUM")
		except Exception :
			# Config not loaded (yet) for this guild.
			return []
		return [forum for forum in (bot.get_channel(forum_id) for forum_id in forum_ids)
		        if isinstance(forum, discord.ForumChannel)]

	@staticmethod
	def pending(forum: discord.ForumChannel) -> list[discord.Thread] :
		"""The forum's open adverts without the approved tag."""
		return [thread for thread in forum.threads
		        if ForumStatus.APPROVED.value not in [tag.name.lower() for tag in thread.applied_tags]]

	@staticmethod
	def kind(thread: discord.Thread) -> str :
		"""Bump when the advert is back in review after a bump, New otherwise (a fresh post awaiting its first review)."""
		if ForumStatus.BUMP.value in [tag.name.lower() for tag in thread.applied_tags] :
			return "Bump"
		return "New"

	@staticmethod
	def line(thread: discord.Thread) -> str :
		"""One pending advert as a list entry. Uses owner_id: the author may not be cached."""
		return f"- **{PendingAdverts.kind(thread)}** {thread.jump_url} by <@{thread.owner_id}>"

	@staticmethod
	def render(forum: discord.ForumChannel) -> discord.Embed :
		"""One forum's pending adverts as an embed; mentions in embeds don't ping."""
		threads = PendingAdverts.pending(forum)
		if not threads :
			return discord.Embed(
				title=f"{forum.name}: up to date",
				description="All adverts are checked and approved! Good job everyone!",
				color=discord.Color.green(),
				timestamp=discord.utils.utcnow(),
			)
		lines = []
		length = 0
		for index, thread in enumerate(threads) :
			line = PendingAdverts.line(thread)
			# Leaves room for the "...and N more" line.
			if length + len(line) + 1 > DESCRIPTION_LIMIT - 30 :
				lines.append(f"...and {len(threads) - index} more")
				break
			lines.append(line)
			length += len(line) + 1
		bumps = sum(1 for thread in threads if PendingAdverts.kind(thread) == "Bump")
		return discord.Embed(
			title=f"{forum.name}: {len(threads)} pending advert{'s' if len(threads) != 1 else ''} "
			      f"({len(threads) - bumps} new, {bumps} bump{'s' if bumps != 1 else ''})",
			description="\n".join(lines),
			color=discord.Color.orange(),
			timestamp=discord.utils.utcnow(),
		)

	@staticmethod
	def track_dm(guild_id: int, forum_id: int, message: discord.Message) :
		"""Keeps a /forum pendingadverts DM up to date from now on."""
		PendingAdverts._dms.setdefault(guild_id, []).append((message, forum_id, datetime.now()))

	@staticmethod
	def refresh(bot: commands.Bot, guild: discord.Guild | None) :
		"""Schedules an update of the guild's pending board and DMs in DEBOUNCE seconds, unless one is on its way."""
		if guild is None :
			return
		PendingAdverts._dirty.add(guild.id)
		timer = PendingAdverts._timers.get(guild.id)
		if timer is not None and not timer.done() :
			return
		PendingAdverts._timers[guild.id] = asyncio.create_task(PendingAdverts._refresh_later(bot, guild))

	@staticmethod
	async def _refresh_later(bot: commands.Bot, guild: discord.Guild) :
		# Runs again when something changed during the update.
		while guild.id in PendingAdverts._dirty :
			await asyncio.sleep(DEBOUNCE)
			PendingAdverts._dirty.discard(guild.id)
			try :
				await PendingAdverts.update(bot, guild)
			except Exception as e :
				logging.error(f"Failed to update the pending adverts list in {guild.name}: {e}", exc_info=True)

	@staticmethod
	async def update(bot: commands.Bot, guild: discord.Guild) :
		"""Edits the guild's pending board and tracked DMs to the current pending adverts, and crosses out the lines
		about adverts that are no longer pending in the pendingapproval channel."""
		embeds = {forum.id : PendingAdverts.render(forum) for forum in PendingAdverts.forums(bot, guild)}
		await PendingAdverts._update_board(bot, guild, embeds)
		await PendingAdverts._update_dms(guild, embeds)
		await PendingAdverts._update_log(bot, guild)

	@staticmethod
	async def _update_log(bot: commands.Bot, guild: discord.Guild) :
		try :
			channel_id = ConfigData().get_key_or_none(guild.id, "PENDINGAPPROVAL")
		except KeyError :
			return
		channel = bot.get_channel(int(channel_id)) if channel_id else None
		if not isinstance(channel, discord.TextChannel | discord.Thread) :
			return
		try :
			messages = [message async for message in channel.history(limit=LOG_HISTORY)
			            if message.author.id == bot.user.id]
		except discord.HTTPException as e :
			logging.warning(f"Failed to read the pendingapproval channel in {guild.name}: {e}")
			return
		for message in messages :
			content = PendingAdverts.cross_out(guild, message.content, message.created_at)
			if content is None :
				continue
			try :
				await message.edit(content=content, allowed_mentions=discord.AllowedMentions.none())
			except discord.HTTPException as e :
				logging.warning(f"Failed to cross out pending adverts in message {message.id} in {guild.name}: {e}")

	@staticmethod
	def status(guild: discord.Guild, thread_id: int) -> str | None :
		"""approved or removed when the advert is no longer pending, None while it is (or the bot can't tell)."""
		thread = guild.get_thread(thread_id)
		if thread is not None :
			approved = ForumStatus.APPROVED.value in [tag.name.lower() for tag in thread.applied_tags]
			return "approved" if approved else None
		# Archived threads aren't cached either, so only a deletion the bot saw counts as removed.
		return "removed" if thread_id in PendingAdverts._removed else None

	@staticmethod
	def cross_out(guild: discord.Guild, content: str, posted_at: datetime) -> str | None :
		"""The message with the lines about adverts that are no longer pending crossed out, or None if nothing
		changes. A line is crossed out once: an advert that is bumped again gets a new line."""
		lines = content.split("\n")
		detailed = [PendingAdverts._cross_out_line(guild, line, posted_at, True) for line in lines]
		if detailed == lines :
			return None
		result = "\n".join(detailed)
		if len(result) <= MESSAGE_LIMIT :
			return result
		# Too long with the approvers: icons only, for as many lines as fit. The rest wait for room that won't come,
		# which is rare: the bot sends at most 1800 characters per message.
		length = len(content)
		changed = False
		for index, line in enumerate(lines) :
			new = PendingAdverts._cross_out_line(guild, line, posted_at, False)
			if new == line or length + len(new) - len(line) > MESSAGE_LIMIT :
				continue
			lines[index] = new
			length += len(new) - len(line)
			changed = True
		return "\n".join(lines) if changed else None

	@staticmethod
	def _cross_out_line(guild: discord.Guild, line: str, posted_at: datetime, detailed: bool) -> str :
		# The daily list's lines are list items: the strikethrough goes after the "- ", or the list breaks. Its first
		# item starts with a space.
		indent = line[: len(line) - len(line.lstrip())]
		bullet = indent + "- " if line.lstrip().startswith("- ") else indent
		text = line[len(bullet) :]
		reference = THREAD_REFERENCE.search(text)
		if reference is None or text.startswith("~~") :
			return line
		thread_id = int(reference.group(1) or reference.group(2))
		status = PendingAdverts.status(guild, thread_id)
		if status is None :
			return line
		icon = "✅" if status == "approved" else "🗑️"
		if not detailed :
			return f"{bullet}~~{text}~~ {icon}"
		marker = f"{icon} {status}"
		approver = PendingAdverts._approvers.get(thread_id)
		# Only an approval made after the line was posted is this line's approval.
		if status == "approved" and approver is not None and approver[1] > posted_at :
			marker += f" by <@{approver[0]}>"
		return f"{bullet}~~{text}~~ {marker}"

	@staticmethod
	async def _update_board(bot: commands.Bot, guild: discord.Guild, embeds: dict[int, discord.Embed]) :
		try :
			channel_id = ConfigData().get_key_or_none(guild.id, "PENDINGBOARD")
		except KeyError :
			return
		channel = bot.get_channel(int(channel_id)) if channel_id else None
		if not isinstance(channel, discord.TextChannel | discord.Thread) :
			return
		for forum_id, embed in embeds.items() :
			key = f"PENDINGBOARD-{forum_id}"
			message_id = ConfigData().get_key_or_none(guild.id, key)
			if message_id is not None :
				try :
					await channel.get_partial_message(int(message_id)).edit(content=None, embed=embed)
					continue
				except discord.NotFound :
					# Removed: posts a new one below.
					pass
				except discord.HTTPException as e :
					logging.warning(f"Failed to edit the pending board for forum {forum_id} in {guild.name}: {e}")
					continue
			try :
				message = await channel.send(embed=embed)
			except discord.HTTPException as e :
				logging.warning(f"Failed to post the pending board for forum {forum_id} in {guild.name}: {e}")
				continue
			# The config table's key includes an autoincrement id, so overwrite=True would add a second row instead
			# of replacing the old message id: remove it first.
			ConfigTransactions().config_unique_remove(guild.id, key)
			ConfigTransactions().config_unique_add(guild.id, key, message.id, overwrite=True)

	@staticmethod
	async def _update_dms(guild: discord.Guild, embeds: dict[int, discord.Embed]) :
		now = datetime.now()
		kept = []
		for message, forum_id, sent_at in PendingAdverts._dms.get(guild.id, []) :
			embed = embeds.get(forum_id)
			if embed is None or now - sent_at > DM_LIFETIME :
				continue
			try :
				await message.edit(content=None, embed=embed)
			except (discord.NotFound, discord.Forbidden) :
				continue
			except discord.HTTPException as e :
				logging.warning(f"Failed to update a pending adverts DM in {guild.name}: {e}")
			kept.append((message, forum_id, sent_at))
		PendingAdverts._dms[guild.id] = kept
