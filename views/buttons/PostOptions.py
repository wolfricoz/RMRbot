import discord

from classes.Support.discord_tools import send_response
from classes.queue import queue


class PostOptions(discord.ui.View) :
	"""This class is for the confirm buttons, which are used to confirm or cancel an action."""
	confirmed = None
	interaction: discord.Interaction

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

