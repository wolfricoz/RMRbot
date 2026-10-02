import logging

import discord

from databases.transactions.ConfigData import ConfigData


class InterestReportModal(discord.ui.Modal, title="Report this message") :
	"""Sends an interest message, with the recipient's reason, to the guild's advert moderators."""

	reason = discord.ui.TextInput(
		label="Why are you reporting this message?",
		style=discord.TextStyle.long,
		placeholder="Optional, but it helps staff look into it.",
		required=False,
		max_length=500,
	)

	def __init__(self, guild_id: int, sender_id: int) :
		super().__init__(timeout=None)
		self.guild_id = guild_id
		self.sender_id = sender_id

	async def on_submit(self, interaction: discord.Interaction) :
		guild = interaction.client.get_guild(self.guild_id)
		channel_id = ConfigData().get_key_or_none(self.guild_id, "advertmod") if guild else None
		channel = guild.get_channel(int(channel_id)) if channel_id else None
		if channel is None :
			await interaction.response.send_message(
				"Your report could not be delivered. Please contact the server staff directly.")
			return

		original = interaction.message.embeds[0] if interaction.message and interaction.message.embeds else None
		embed = discord.Embed(title="Interest message reported", color=discord.Color.red())
		embed.add_field(name="Sent by", value=f"<@{self.sender_id}> ({self.sender_id})", inline=True)
		embed.add_field(name="Reported by", value=f"{interaction.user.mention} ({interaction.user.id})", inline=True)
		embed.add_field(name="Message", value=original.description if original else "Unavailable", inline=False)
		advert = next((field.value for field in original.fields if field.name == "Advert"), None) if original else None
		if advert :
			embed.add_field(name="Advert", value=advert, inline=False)
		embed.add_field(name="Reason", value=self.reason.value or "No reason given", inline=False)
		await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())

		# Only one report per message.
		await interaction.response.edit_message(view=None)
		await interaction.followup.send(f"Thanks, the message has been reported to the {guild.name} staff.")

	async def on_error(self, interaction: discord.Interaction, error: Exception) -> None :
		logging.error(error)
		await interaction.response.send_message("Oops! Something went wrong.")
