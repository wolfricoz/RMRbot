import discord

from views.modals.verifyModal import VerifyModal


class VerifyButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verify Here!", style=discord.ButtonStyle.red, custom_id="verify")
    async def test(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VerifyModal())
