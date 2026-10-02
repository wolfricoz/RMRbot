import discord

from classes.Website.Advert import Advert
from databases.transactions.AdvertisementTransactions import AdvertisementTransactions


class WebsiteConsent(discord.ui.View) :
	"""Asks an advert's author whether it may be cross-posted to the website. Persistent: the buttons keep
	working after a restart, the advert is found again from the thread the message is in."""

	def __init__(self) :
		super().__init__(timeout=None)

	@discord.ui.button(label="Share on website", style=discord.ButtonStyle.green, custom_id="website_consent:yes")
	async def consent(self, interaction: discord.Interaction, button: discord.ui.Button) :
		"""Gives consent and, if staff already approved the advert, tries to publish straight away; a failed publish is
		left to the sync task. Otherwise the approval publishes it."""
		advert = await self._authorsAdvert(interaction)
		if advert is None :
			return
		AdvertisementTransactions().set_consent(advert.id, True)
		approved = Advert.isApproved(advert, interaction.channel)
		when = "" if approved else " once staff have approved it"
		await interaction.response.edit_message(
			content=f"Thanks! Your advert will be sent to the website{when}. Once it's live, a link will appear in this thread.",
			embed=None,
			view=None,
			allowed_mentions=discord.AllowedMentions.none(),
		)
		if advert.published_at is not None or not approved :
			return
		try :
			message = await interaction.channel.fetch_message(advert.id)
		except discord.HTTPException :
			return
		await Advert(message).publishToWebsite()

	@staticmethod
	async def _authorsAdvert(interaction: discord.Interaction) :
		"""The advert in this thread, if the person pressing the button is its author; otherwise tells them why not."""
		advert = next((advert for advert in AdvertisementTransactions().get_by_thread(interaction.channel.id)
		               if advert.deleted is None), None)
		if advert is None :
			await interaction.response.send_message("This advert no longer exists.", ephemeral=True)
			return None
		if interaction.user.id != advert.user_id :
			await interaction.response.send_message("Only the author of this advert can choose this.", ephemeral=True)
			return None
		return advert
