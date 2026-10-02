from datetime import datetime, timedelta

import discord

from classes.Support.discord_tools import send_response
from classes.queue import queue
from views.modals.InterestModal import InterestModal


class PostOptions(discord.ui.View) :
	"""This class is for the confirm buttons, which are used to confirm or cancel an action."""
	confirmed = None
	interaction: discord.Interaction
	# One interest message per person per advert in this window, so nobody can flood an author's DMs.
	cooldown = timedelta(hours=24)
	sent: dict[tuple[int, int], datetime] = {}

	def __init__(self, forum_controller=None) :
		super().__init__(timeout=None)
		self.forum_controller = forum_controller

	@discord.ui.button(label="Bump", style=discord.ButtonStyle.green, custom_id="confirm")
	async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) :
		"""Confirms the action"""
		await interaction.response.defer(ephemeral=True)
		forums = self.forum_controller.config(interaction.guild.id)
		thread: discord.Thread = interaction.guild.get_thread(interaction.channel.id)
		forum: discord.ForumChannel = interaction.guild.get_channel(thread.parent_id)
		if forum.id not in forums :
			await send_response(interaction, "Forum not found")
			return
		queue().add(self.forum_controller.bump(interaction.client, interaction), 2)

	@discord.ui.button(label="Close", style=discord.ButtonStyle.red, custom_id="cancel")
	async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button) :
		"""Cancels the action"""
		await interaction.response.send_message("Closing post", ephemeral=True)
		await self.forum_controller.close_thread(interaction)

	# custom_id kept from the rule reminder's button, so the buttons already posted there keep working.
	@discord.ui.button(label="I'm interested", style=discord.ButtonStyle.blurple, custom_id="advert_interest")
	async def interested(self, interaction: discord.Interaction, button: discord.ui.Button) :
		"""Opens the modal for a message to the advert's author; the author is found from the thread."""
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

