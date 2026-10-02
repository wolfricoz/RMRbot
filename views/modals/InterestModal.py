import logging

import discord

from views.buttons.InterestReport import InterestReport


class InterestModal(discord.ui.Modal, title="Let them know you're interested") :
	"""DMs the author of an advert a short message from someone interested in it, with a button to report it."""

	message = discord.ui.TextInput(
		label="Your message",
		style=discord.TextStyle.long,
		placeholder="Introduce yourself and say what caught your eye...",
		max_length=500,
	)

	def __init__(self, thread: discord.Thread, on_sent) :
		super().__init__(timeout=None)
		self.thread = thread
		self.on_sent = on_sent

	async def on_submit(self, interaction: discord.Interaction) :
		try :
			author = await interaction.client.fetch_user(self.thread.owner_id)
		except discord.HTTPException :
			await interaction.response.send_message("The author of this advert could not be found.", ephemeral=True)
			return

		embed = discord.Embed(title="Someone is interested in your advert!", description=self.message.value)
		embed.add_field(name="From", value=f"{interaction.user.mention} ({interaction.user.name})", inline=True)
		embed.add_field(name="Advert", value=f"[{self.thread.name}]({self.thread.jump_url})", inline=True)
		embed.set_footer(text=f"Sent through {interaction.guild.name}. "
		                      f"If this message is abusive, press Report to send it to the staff.")
		try :
			await author.send(embed=embed, view=InterestReport.view(interaction.guild.id, interaction.user.id))
		except discord.Forbidden :
			await interaction.response.send_message(
				f"{author.mention} doesn't accept direct messages, so your message could not be delivered.",
				ephemeral=True)
			return

		self.on_sent(interaction.user.id, self.thread.id)
		await interaction.response.send_message(f"Your message has been sent to {author.mention}!", ephemeral=True)

	async def on_error(self, interaction: discord.Interaction, error: Exception) -> None :
		logging.error(error)
		await interaction.response.send_message("Oops! Something went wrong.", ephemeral=True)
