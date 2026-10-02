import logging
import os
import re

import discord
import aiohttp

from classes.Website.DiscordToHTML import discord_to_html
from databases.current import Advertisements
from databases.transactions.AdvertisementTransactions import AdvertisementTransactions
from databases.transactions.ApprovalTransactions import ApprovalTransactions
from resources.enums.ForumStatus import ForumStatus

# The advert's header (see AutoMod.check_header): "All characters are (age)+", optional lines, then a line of dashes.
# Lazy, so it ends at the first line of dashes rather than one further down in the advert.
HEADER_RE = re.compile(
	r"^(`{0,3})\.?\s*\.?\s*\.?\s*All\s*character'?s?\s*are:?\s*\(?\s*([1-9][0-9])\s*\)?(.*?)[-|—]{5,100}",
	re.IGNORECASE | re.DOTALL,
)
# An optional header line with the partner's age, e.g. "Partner age: 21+" or "Writers 25+".
PARTNER_AGE_RE = re.compile(r"(?:partner|writer)s?\b[^\n\d]{0,20}([1-9][0-9])", re.IGNORECASE)
# The website's allowed ages.
MIN_AGE, MAX_AGE = 18, 999


class Advert:

	baseUrl = os.getenv("WEBSITE_URL")
	key = os.getenv("WEBSITE_KEY")
	# Ids of the adverts being published right now.
	_publishing: set[int] = set()

	def __init__(self, message: discord.Message):
		self.new = False
		self.message: discord.Message = message
		self.advert = self._fetchMessageRecord()

	async def run(self) -> "Advert":
		"""Asks for consent if the advert is new: await Advert(message).run()"""
		if self.new:
			await self.requestConsent()
		return self

	@classmethod
	def _headers(cls) -> dict:
		return {
			"Authorization" : f"Bearer {cls.key}",
			"Content-Type"  : "application/json",
			"Accept"        : "application/json"
		}

	async def publishToWebsite(self) -> str | None:
		"""Sends the advert to the website (POST /api/v1/posts) as its author, unless it is already there or being
		sent. Returns the post's URL on the website, or None when it failed or the URL is unknown."""
		# The consent button, an approval and the publish task can all try to publish the same advert.
		if self.message.id in self._publishing or not self._isApprovedText():
			return None
		advert = AdvertisementTransactions().get(self.message.id)
		if advert is not None and advert.published_at is not None:
			return advert.url
		self._publishing.add(self.message.id)
		try:
			return await self._publish()
		finally:
			self._publishing.discard(self.message.id)

	async def _publish(self) -> str | None:
		member = self.message.author
		payload = {
			"user_id"    : str(member.id),  # send as a string
			"user"       : {
				"username"    : member.name,
				"global_name" : member.global_name,
				"avatar"      : member.avatar.key if member.avatar else None,
			},
			"message_id" : str(self.message.id),  # lets the website post be deleted by this message later
			"source"     : "Roleplay Meets discord",
			"approved"   : True,
			**self._websiteFields(),
		}
		try:
			async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
				async with session.post(f"{self.baseUrl}/api/v1/posts", headers=self._headers(), json=payload) as response:
					if response.status == 201:
						url = (await response.json()).get("url")
						AdvertisementTransactions().set_published(self.message.id, url=url)
						await self.announceWebsitePost(url)
						return url
					if response.status == 422 and "message_id" in (await response.json()).get("errors", {}):
						# message_id is unique on the website: it already has this advert (an earlier publish whose
						# response never arrived), so it counts as published. The website doesn't return its URL here.
						logging.info(f"Advert {self.message.id} is already on the website, marking it published")
						AdvertisementTransactions().set_published(self.message.id)
						return None
					if response.status == 409:
						# Too similar to a post already on the website, usually the author's previous advert that is still
						# up. Left unpublished: publish_pending retries it once that post is removed.
						post_id = (await response.json()).get("post_id")
						logging.info(f"Advert {self.message.id} is waiting for similar website post {post_id} to be removed")
						return None
					logging.warning(f"Failed to publish advert {self.message.id} to website: {response.status} {await response.text()}")
		except Exception as e:
			logging.warning(f"Failed to publish advert {self.message.id} to website: {e}")
		return None

	def _websiteFields(self) -> dict:
		"""The parts of the website post that follow the advert: sent on publish and on every approved edit."""
		thread = self.message.channel
		rating = "sfw"
		if "nsfw" in thread.parent.name.lower():
			rating = "nsfw"
		if "taboo" in thread.parent.name.lower():
			rating = "extreme"
		# clean_content has mentions as names (@name, #channel) instead of ids.
		content, charage, partnerage = self._readHeader(self.message.clean_content)
		return {
			"title"      : thread.name,
			"content"    : discord_to_html(content),
			"charage"    : charage,
			"partnerage" : partnerage,
			"nsfw"       : rating,
			"genres"     : [tag.name for tag in thread.applied_tags],
		}

	@staticmethod
	def _readHeader(content: str) -> tuple[str, int, int]:
		"""Splits the header off the advert: returns the advert without it, the character age and the partner age.
		Without a header the advert is returned whole with the minimum ages."""
		header = HEADER_RE.match(content)
		if header is None:
			return content, MIN_AGE, MIN_AGE
		charage = int(header.group(2))
		partner = PARTNER_AGE_RE.search(header.group(3))
		partnerage = int(partner.group(1)) if partner else MIN_AGE
		advert = content[header.end():].lstrip()
		# A header in a code block leaves the block's closing fence behind.
		if header.group(1) and advert.startswith("```"):
			advert = advert[3:].lstrip()
		return advert, min(max(charage, MIN_AGE), MAX_AGE), min(max(partnerage, MIN_AGE), MAX_AGE)

	async def updateOnWebsite(self) -> bool:
		"""Sends the advert's current version to its website post (PATCH /api/v1/posts/message/{message_id}).
		Kept approved there: moderators approve adverts in Discord."""
		if not self._isApprovedText():
			return False
		payload = {**self._websiteFields(), "approved": True}
		try:
			async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
				async with session.patch(f"{self.baseUrl}/api/v1/posts/message/{self.message.id}", headers=self._headers(), json=payload) as response:
					if response.status == 200:
						return True
					logging.warning(f"Failed to update advert {self.message.id} on website: {response.status} {await response.text()}")
		except Exception as e:
			logging.warning(f"Failed to update advert {self.message.id} on website: {e}")
		return False

	async def syncApproval(self):
		"""Sends the approved version to the website if the author consented (publishing it if an earlier attempt
		failed). Approvals happen in Discord: see AdvertReview.approved."""
		AdvertisementTransactions().set_approved(self.message.id, True)
		advert = AdvertisementTransactions().get(self.message.id)
		if advert is None or advert.consent_at is None or advert.deleted is not None:
			return
		if advert.published_at is None:
			await self.publishToWebsite()
			return
		await self.updateOnWebsite()

	def _isApprovedText(self) -> bool:
		"""Whether the advert's current text is the text staff last approved, so nothing unreviewed reaches the website;
		also catches edits the bot missed (e.g. made while it was offline). AdvertReview.approved stores the text."""
		approved = ApprovalTransactions().get_approved_content(self.message.channel.id)
		if approved != self.message.content:
			logging.info(f"Advert {self.message.id} has text that wasn't approved, not sending it to the website")
			return False
		return True

	@staticmethod
	def isApproved(advert: Advertisements, thread: discord.Thread) -> bool:
		"""Whether staff approved the advert's current version: approved in the database (see syncApproval) and its
		thread still has the approved status tag (a bump puts it back in review). Adverts are only sent to the website
		once approved; an approval publishes them."""
		return advert.approved and ForumStatus.APPROVED.value in [tag.name.lower() for tag in thread.applied_tags]

	@classmethod
	async def approvedInDiscord(cls, thread: discord.Thread, message: discord.Message):
		"""The advert (message) in this thread was approved; syncs it if it is a website advert."""
		# Only adverts the bot has a record of; constructing an Advert would otherwise create one.
		if not any(advert.deleted is None for advert in AdvertisementTransactions().get_by_thread(thread.id)):
			return
		await cls(message).syncApproval()

	@classmethod
	async def bumpOnWebsite(cls, message_id: int) -> bool:
		"""Bumps the website post of a published advert (POST /api/v1/posts/message/{message_id}/bump)."""
		advert = AdvertisementTransactions().get(message_id)
		if advert is None or advert.published_at is None or advert.deleted is not None:
			return False
		try:
			async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
				async with session.post(f"{cls.baseUrl}/api/v1/posts/message/{message_id}/bump", headers=cls._headers()) as response:
					if response.status == 200:
						return True
					logging.warning(f"Failed to bump advert {message_id} on website: {response.status} {await response.text()}")
		except Exception as e:
			logging.warning(f"Failed to bump advert {message_id} on website: {e}")
		return False

	async def announceWebsitePost(self, url: str | None):
		"""Links the website post in the advert's thread."""
		if not url:
			return
		try:
			await self.message.channel.send(
				f"Your advert is now on the website: {url}",
				allowed_mentions=discord.AllowedMentions.none(),
			)
		except discord.HTTPException as e:
			# The post is published either way; only the link message failed.
			logging.warning(f"Failed to link website post in thread {self.message.channel.id}: {e}")

	@classmethod
	async def deleteFromWebsite(cls, message_id: int) -> bool:
		"""Removes the website post made from this advert (DELETE /api/v1/posts/message/{message_id}).
		Returns True when the website no longer has it (a 404 means it never got there)."""
		try:
			async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
				async with session.delete(f"{cls.baseUrl}/api/v1/posts/message/{message_id}", headers=cls._headers()) as response:
					if response.status in (204, 404):
						return True
					logging.warning(f"Failed to delete advert {message_id} from website: {response.status} {await response.text()}")
		except Exception as e:
			logging.warning(f"Failed to delete advert {message_id} from website: {e}")
		return False




	def _fetchMessageRecord(self):
		advertisement = AdvertisementTransactions().get(self.message.id)
		if not advertisement:
			AdvertisementTransactions().add(self.message.id, self.message.channel.id, self.message.channel.parent_id, self.message.author.id)
			advertisement = AdvertisementTransactions().get(self.message.id)
			self.new = True
		return advertisement

	def _createConsentEmbed(self):
		embed = discord.Embed(
			title="Share your advert on our website?",
			description="Would you like this advert to be cross-posted to [roleplaymeets.com](https://roleplaymeets.com)?\n\n"
			            "If you don't have an account on the website yet, one will be created for you with your Discord account.\n\n"
			            "[Terms of Service](https://roleplaymeets.com/tos) | [Rules](https://roleplaymeets.com/rules)",
		)
		# Footers don't render links, so the links are in the description above.
		embed.set_footer(text="By pressing the button, you agree to the Terms of Service and Rules linked above.")
		return embed

	async def requestConsent(self):
		# Imported here: the view imports this class.
		from views.buttons.WebsiteConsent import WebsiteConsent

		# Pings the thread's owner, also when the thread or its owner isn't cached (e.g. adverts found by check_missing).
		owner_id = self.message.channel.owner_id
		await self.message.channel.send(
			content=f"<@{owner_id}>",
			embed=self._createConsentEmbed(),
			view=WebsiteConsent(),
			allowed_mentions=discord.AllowedMentions(users=[discord.Object(id=owner_id)]),
		)