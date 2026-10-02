import logging
from datetime import timedelta

import discord
from discord.ext import tasks
from discord.ext.commands import Cog, Bot

from classes.Website.Advert import Advert
from classes.automod import AutoMod
from classes.queue import queue
from databases.current import Advertisements
from databases.transactions.AdvertisementTransactions import AdvertisementTransactions
from views.buttons.WebsiteConsent import WebsiteConsent


# A plain Cog: a GroupCog without commands would still register an empty /website command.
class Website(Cog) :

	def __init__(self, bot: Bot) :
		self.bot = bot
		# Persistent, so consent buttons on older adverts keep working after a restart.
		self.bot.add_view(WebsiteConsent())
		self.publish_pending.start()
		self.check_deleted.start()
		self.check_missing.start()

	def cog_unload(self) :
		self.publish_pending.cancel()
		self.check_deleted.cancel()
		self.check_missing.cancel()

	# The other listeners are in forum.py - integrated with existing logic.

	@Cog.listener()
	async def on_raw_thread_delete(self, payload: discord.RawThreadDeleteEvent) :
		"""Removes an advert from the website when its thread is deleted, whoever deleted it (the author, a mod,
		automod, or forum.py after the main message was removed). Raw, so uncached threads count too."""
		for advert in AdvertisementTransactions().get_by_thread(payload.thread_id) :
			if advert.deleted is not None :
				continue
			await self._remove(advert)

	@tasks.loop(minutes=5)
	async def publish_pending(self) :
		"""Sends the approved adverts with consent that aren't on the website yet (consent given while a publish failed,
		or the website was down)."""
		for advert in AdvertisementTransactions().get_unpublished() :
			message = await self._fetch_advert(advert)
			# Unapproved adverts wait for their approval, which publishes them.
			if message is None or not Advert.isApproved(advert, message.channel) :
				continue
			await Advert(message).publishToWebsite()

	@tasks.loop(minutes=5)
	async def check_deleted(self) :
		"""Marks the adverts that are gone from Discord as deleted and removes them from the website, for deletions the
		bot missed (e.g. while it was offline)."""
		for advert in AdvertisementTransactions().get_active() :
			await self._fetch_advert(advert)

	@tasks.loop(hours=1)
	async def check_missing(self) :
		"""Asks for consent on the adverts in the forums that the bot has no record of (posted before the website
		existed, or while the bot was offline). Archived adverts are left to the forum manager, which unarchives them."""
		known = AdvertisementTransactions().get_ids()
		for guild in self.bot.guilds :
			for forum_id in AutoMod.config(guild.id) :
				forum = guild.get_channel(forum_id)
				if not isinstance(forum, discord.ForumChannel) :
					continue
				for thread in forum.threads :
					# A forum thread's id is its starter message's id, the advert.
					if thread.id in known :
						continue
					# Newer threads may still be in automod, which creates the record itself.
					if discord.utils.utcnow() - thread.created_at < timedelta(hours=1) :
						continue
					try :
						message = thread.starter_message or await thread.fetch_message(thread.id)
					except discord.HTTPException :
						# Starter message gone: the forum cleanup removes the thread.
						continue
					if message.author.bot :
						continue
					queue().add(Advert(message).run())

	async def _fetch_advert(self, advert: Advertisements) -> discord.Message | None :
		"""The advert's message. When its thread or message no longer exists, the advert is removed."""
		try :
			thread = self.bot.get_channel(advert.thread_id) or await self.bot.fetch_channel(advert.thread_id)
			return await thread.fetch_message(advert.id)
		except discord.NotFound :
			await self._remove(advert)
		except discord.HTTPException as e :
			# Not proof that it's gone (no access, Discord outage): checked again on the next run.
			logging.warning(f"Failed to fetch advert {advert.id} in thread {advert.thread_id}: {e}")
		return None

	@staticmethod
	async def _remove(advert: Advertisements) :
		"""Marks the advert deleted once it's off the website. If the website can't be reached it stays active, so
		check_deleted retries it."""
		# Without consent it was never sent to the website.
		if advert.consent_at is not None and not await Advert.deleteFromWebsite(advert.id) :
			return
		AdvertisementTransactions().set_deleted(advert.id)

	@publish_pending.before_loop
	async def before_publish_pending(self) :
		await self.bot.wait_until_ready()

	@check_deleted.before_loop
	async def before_check_deleted(self) :
		await self.bot.wait_until_ready()

	@check_missing.before_loop
	async def before_check_missing(self) :
		await self.bot.wait_until_ready()


async def setup(bot: Bot) :
	await bot.add_cog(
		Website(bot),
	)
