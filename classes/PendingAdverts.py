"""The list of adverts waiting for staff approval, per automod forum. Staff see it in two places that the bot keeps
up to date as adverts are approved, removed or posted:

* the pending board: one message per forum in the channel set as `pendingboard` (/config channels). Its message ids
  are kept in the config (PENDINGBOARD-<forum id>), so the board carries on after a restart;
* the DMs /forum pendingadverts sends. These are tracked in memory only: after a restart, older DMs stop updating.

Updates are batched per guild, so a burst of approvals edits each message once."""
import asyncio
import logging
from datetime import datetime, timedelta

import discord
from discord.ext import commands

from databases.transactions.ConfigData import ConfigData
from databases.transactions.ConfigTransactions import ConfigTransactions

# Seconds to wait after a change before editing, so changes close together become one edit.
DEBOUNCE = 10
# How long a /forum pendingadverts DM keeps updating.
DM_LIFETIME = timedelta(hours=24)
# Embed descriptions are limited to 4096 characters.
DESCRIPTION_LIMIT = 4000


class PendingAdverts :
	"""Builds the pending adverts list and keeps the pending board and the pending list DMs current."""

	# guild id -> [(DM message, forum id, sent at)]
	_dms: dict[int, list[tuple[discord.Message, int, datetime]]] = {}
	# guild id -> the scheduled update. Changes while it waits or runs are picked up by it, never by a second one, so
	# two updates can't both post a board message.
	_timers: dict[int, asyncio.Task] = {}
	# Guilds with changes the running update may have missed.
	_dirty: set[int] = set()

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
		        if "approved" not in [tag.name.lower() for tag in thread.applied_tags]]

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
			line = f"- {thread.jump_url} by <@{thread.owner_id}>"
			# Leaves room for the "...and N more" line.
			if length + len(line) + 1 > DESCRIPTION_LIMIT - 30 :
				lines.append(f"...and {len(threads) - index} more")
				break
			lines.append(line)
			length += len(line) + 1
		return discord.Embed(
			title=f"{forum.name}: {len(threads)} pending advert{'s' if len(threads) != 1 else ''}",
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
		"""Edits the guild's pending board and tracked DMs to the current pending adverts."""
		embeds = {forum.id : PendingAdverts.render(forum) for forum in PendingAdverts.forums(bot, guild)}
		await PendingAdverts._update_board(bot, guild, embeds)
		await PendingAdverts._update_dms(guild, embeds)

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
