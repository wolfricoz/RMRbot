import discord

from classes.databaseController import UserTransactions


class WarningModal(discord.ui.Modal, title='Official Warning'):
    custom_id = "warning"

    def __init__(self, user, notify, warnlog):
        super().__init__(timeout=None)  # Set a timeout for the modal
        self.user = user
        self.notify = notify
        self.warnlog = warnlog

    reason = discord.ui.TextInput(
            label='What is the reason?',
            style=discord.TextStyle.long,
            placeholder='Type your warning here...',
            max_length=1000,
    )

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(self.warnlog)
        warning = f"{interaction.guild.name} **__WARNING__**: {self.reason}"
        UserTransactions.user_add_warning(self.user.id, self.reason.value)
        if self.notify.upper() == "YES":
            await self.user.send(warning)
        embed = discord.Embed(title=f"{self.user.name} has been warned", description=warning)
        embed.set_footer(text=f"Notify: {self.notify}, uid: {self.user.id}")
        await interaction.response.send_message(self.user.mention, embed=embed)
        await channel.send(embed=embed)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        print(error)
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)
