from datetime import datetime, timedelta

import discord

from views.modals.InterestModal import InterestModal


class AdvertInterest(discord.ui.View) :
	"""Lets people tell an advert's author they are interested. Sent with the rule reminder; persistent, the author
	is found again from the thread the message is in."""

	# One message per person per advert in this window, so nobody can flood an author's DMs.
	cooldown = timedelta(hours=24)
	sent: dict[tuple[int, int], datetime] = {}

	def __init__(self) :
		super().__init__(timeout=None)

	@discord.ui.button(label="I'm interested", style=discord.ButtonStyle.blurple, custom_id="advert_interest")
	async def interested(self, interaction: discord.Interaction, button: discord.ui.Button) :
		"""Opens the modal for the message to the author."""
		thread = interaction.channel
		if not isinstance(thread, discord.Thread) :
			return
		if interaction.user.id == thread.owner_id :
			await interaction.response.send_message("You can't send a message to your own advert.", ephemeral=True)
			return
		last = self.sent.get((interaction.user.id, thread.id))
		if last is not None and discord.utils.utcnow() - last < self.cooldown :
			await interaction.response.send_message(
				f"You've already messaged the author of this advert. You can send another "
				f"{discord.utils.format_dt(last + self.cooldown, 'R')}.", ephemeral=True)
			return
		await interaction.response.send_modal(InterestModal(thread, self.mark_sent))

	@classmethod
	def mark_sent(cls, user_id: int, thread_id: int) :
		cls.sent[(user_id, thread_id)] = discord.utils.utcnow()
