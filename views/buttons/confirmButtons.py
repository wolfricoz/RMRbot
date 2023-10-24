"""This module is for the confirm buttons, which are used to confirm or cancel an action."""

import discord


class confirmAction(discord.ui.View):
    """This class is for the confirm buttons, which are used to confirm or cancel an action."""
    confirmed = None
    interaction: discord.Interaction

    async def send_message(self, interaction, description="Are you sure you want to confirm this action?"):
        embed = await self.create_embed(description=description)
        await interaction.response.send_message(embed=embed, view=self)
        self.interaction = interaction

    async def remove_message(self):
        await self.interaction.delete_original_response()


    async def create_embed(self, description):
        embed = discord.Embed(title="Confirm action", description=description, color=discord.Color.green())
        return embed

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green, custom_id="confirm")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirms the action"""
        await interaction.response.send_message("Confirmed!", ephemeral=True)
        self.confirmed = True
        await self.remove_message()
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, custom_id="cancel")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancels the action"""
        await interaction.response.send_message("Cancelled!", ephemeral=True)
        self.confirmed = False
        await self.remove_message()
        self.stop()
