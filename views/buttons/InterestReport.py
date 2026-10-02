import discord

from views.modals.InterestReportModal import InterestReportModal


class InterestReport(discord.ui.DynamicItem[discord.ui.Button],
                     template=r"interest_report:(?P<guild>\d+):(?P<sender>\d+)(?::(?P<interest>\d+))?") :
	"""Report button under an interest message in the advert author's DMs. The guild, the sender and the logged
	interest (see InterestTransactions) are kept in the custom_id, so the button keeps working after a restart; the
	message itself is read back from the embed. Buttons sent before interests were logged have no interest id."""

	def __init__(self, guild_id: int, sender_id: int, interest_id: int | None = None) :
		custom_id = f"interest_report:{guild_id}:{sender_id}" + (f":{interest_id}" if interest_id else "")
		super().__init__(discord.ui.Button(
			label="Report",
			style=discord.ButtonStyle.red,
			custom_id=custom_id,
		))
		self.guild_id = guild_id
		self.sender_id = sender_id
		self.interest_id = interest_id

	@classmethod
	async def from_custom_id(cls, interaction: discord.Interaction, item: discord.ui.Button, match, /) :
		interest = match["interest"]
		return cls(int(match["guild"]), int(match["sender"]), int(interest) if interest else None)

	async def callback(self, interaction: discord.Interaction) :
		"""Asks the recipient why they are reporting the message."""
		await interaction.response.send_modal(InterestReportModal(self.guild_id, self.sender_id, self.interest_id))

	@staticmethod
	def view(guild_id: int, sender_id: int, interest_id: int | None = None) -> discord.ui.View :
		"""A view holding just the report button, to send along with an interest message."""
		view = discord.ui.View(timeout=None)
		view.add_item(InterestReport(guild_id, sender_id, interest_id))
		return view
