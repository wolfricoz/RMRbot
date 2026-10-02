import discord

from views.modals.InterestReportModal import InterestReportModal


class InterestReport(discord.ui.DynamicItem[discord.ui.Button], template=r"interest_report:(?P<guild>\d+):(?P<sender>\d+)") :
	"""Report button under an interest message in the advert author's DMs. The guild and the sender are kept in
	the custom_id, so the button keeps working after a restart; the message itself is read back from the embed."""

	def __init__(self, guild_id: int, sender_id: int) :
		super().__init__(discord.ui.Button(
			label="Report",
			style=discord.ButtonStyle.red,
			custom_id=f"interest_report:{guild_id}:{sender_id}",
		))
		self.guild_id = guild_id
		self.sender_id = sender_id

	@classmethod
	async def from_custom_id(cls, interaction: discord.Interaction, item: discord.ui.Button, match, /) :
		return cls(int(match["guild"]), int(match["sender"]))

	async def callback(self, interaction: discord.Interaction) :
		"""Asks the recipient why they are reporting the message."""
		await interaction.response.send_modal(InterestReportModal(self.guild_id, self.sender_id))

	@staticmethod
	def view(guild_id: int, sender_id: int) -> discord.ui.View :
		"""A view holding just the report button, to send along with an interest message."""
		view = discord.ui.View(timeout=None)
		view.add_item(InterestReport(guild_id, sender_id))
		return view
