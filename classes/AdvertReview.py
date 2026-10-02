"""Approval history and edit diffs for every advert. Moderators re-check an advert when its author bumps it, so the
bot keeps a diff against the last approved text in the thread until the advert is approved again."""
import difflib
import io
import logging

import discord

from classes.Website.Advert import Advert as WebsiteAdvert
from databases.transactions.AdvertisementTransactions import AdvertisementTransactions
from databases.transactions.ApprovalTransactions import ApprovalTransactions

# Starts every edit diff message, so the bot can find them again to remove them.
DIFF_HEADER = "**This advert was edited.** Changes since it was last approved:"


class AdvertReview :

	@staticmethod
	async def approved(thread: discord.Thread, approver_id: int) :
		"""The advert in this thread was approved (by a moderator, or the bot for an auto-approved bump): stores the
		approved text, removes the edit diff and, if the author consented, sends the approved version to the website."""
		try :
			# A forum thread's id is the id of its starter message, the advert.
			message = await thread.fetch_message(thread.id)
		except discord.HTTPException as e :
			logging.warning(f"Failed to fetch advert {thread.id} to store its approval: {e}")
			return
		ApprovalTransactions().add_approval(approver_id, thread.guild.id, thread.id, message.content)
		await AdvertReview.clear_diffs(thread)
		await WebsiteAdvert.approvedInDiscord(thread, message)

	@staticmethod
	async def bumped(thread: discord.Thread, approver_id: int | None = None) :
		"""The advert was bumped: approves it first when the bump was auto-approved, then bumps it on the website."""
		# A bump puts the advert back in review; an auto-approved bump approves it again right away.
		AdvertisementTransactions().set_approved(thread.id, False)
		if approver_id is not None :
			await AdvertReview.approved(thread, approver_id)
		await WebsiteAdvert.bumpOnWebsite(thread.id)

	@staticmethod
	async def edited(thread: discord.Thread, content: str) :
		"""Keeps one diff in the thread between the advert's last approved text and its current text."""
		approved = ApprovalTransactions().get_approved_content(thread.id)
		if approved is None :
			# Never approved with its text stored: nothing to compare against yet.
			return
		changes = AdvertReview.diff(approved, content)
		if changes :
			# Edited since its approval: unapproved until staff approve the new version.
			AdvertisementTransactions().set_approved(thread.id, False)
		body = f"{DIFF_HEADER}\n```diff\n{changes}\n```"
		posted = await AdvertReview._diff_messages(thread)
		# Discord also sends edit events when embeds load: the diff in the thread is already this one.
		if changes and len(posted) == 1 and posted[0].content == body :
			return
		await AdvertReview._delete(thread, posted)
		if not changes :
			# Edited back to the approved text.
			return
		try :
			if len(body) <= 2000 :
				await thread.send(body, allowed_mentions=discord.AllowedMentions.none())
			else :
				# Too long for one message: attach it instead.
				await thread.send(
					DIFF_HEADER,
					file=discord.File(io.BytesIO(changes.encode()), filename="advert.diff"),
					allowed_mentions=discord.AllowedMentions.none(),
				)
		except discord.HTTPException as e :
			logging.warning(f"Failed to post the edit diff in thread {thread.id}: {e}")

	@staticmethod
	async def clear_diffs(thread: discord.Thread) :
		"""Removes the edit diff the bot posted in the thread."""
		await AdvertReview._delete(thread, await AdvertReview._diff_messages(thread))

	@staticmethod
	async def _diff_messages(thread: discord.Thread) -> list[discord.Message] :
		"""The bot's edit diff messages in the thread, recognised by their header."""
		return [message async for message in thread.history(limit=500)
		        if message.author.id == thread.guild.me.id and message.content.startswith(DIFF_HEADER)]

	@staticmethod
	async def _delete(thread: discord.Thread, messages: list[discord.Message]) :
		for message in messages :
			try :
				await message.delete()
			except discord.NotFound :
				pass
			except discord.HTTPException as e :
				logging.warning(f"Failed to remove edit diff {message.id} in thread {thread.id}: {e}")

	@staticmethod
	def diff(before: str, after: str) -> str :
		"""What changed between two versions of an advert, as a unified diff without the file headers."""
		lines = list(difflib.unified_diff(before.splitlines(), after.splitlines(), lineterm="", n=1))[2 :]
		# Keep the advert's own code fences from closing the ```diff block.
		return "\n".join(lines).replace("```", "`​``")
