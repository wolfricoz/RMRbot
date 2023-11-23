"""Creates a custom warning modal for the bot."""
import logging

import discord

from classes.Advert import Advert
from classes.databaseController import ConfigData


class Custom(discord.ui.Modal, title='Custom Warning'):
    # Our modal classes MUST subclass `discord.ui.Modal`,
    # but the title can be whatever you want.
    # This will be a short input, where the user can enter their name
    # It will also have a placeholder, as denoted by the `placeholder` kwarg.
    # By default, it is required and is a short-style input which is exactly
    # what we want.
    custom_id = "cw"

    def __init__(self, bot, thread, thread_channel):
        super().__init__(timeout=None)  # Set a timeout for the modal
        self.bot = bot
        self.thread = thread
        self.thread_channel = thread_channel

    reason = discord.ui.TextInput(label='What is the reason?', style=discord.TextStyle.long, placeholder='Type your waning here...', max_length=512)

    # This is a longer, paragraph style input, where user can submit feedback
    # Unlike the name, it is not required. If filled out, however, it will
    # only accept a maximum of 300 characters, as denoted by the
    # `max_length=300` kwarg.

    async def on_submit(self, interaction: discord.Interaction) -> None:
        bot = self.bot
        thread = self.thread
        thread_channel = self.thread_channel
        lc = ConfigData().get_key_int(interaction.guild.id, "ADVERTLOG")
        mc = ConfigData().get_key_int(interaction.guild.id, "ADVERTMOD")
        loggingchannel = bot.get_channel(lc)
        modchannel = bot.get_channel(mc)
        user = thread.author
        await interaction.response.send_message(content="Command received", ephemeral=True)
        warning = await Advert.send_in_channel(interaction, user, thread, thread_channel, self.reason.value, "Custom", modchannel)
        # Logs the advert and sends it to the user.
        await Advert.logadvert(thread, loggingchannel)
        await Advert.sendadvertuser(interaction, thread, warning)
        await self.send_message(interaction, f"{user.mention} has been warned for: {self.reason.value}")

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        print(error)
        await self.send_message(interaction, f"An error occurred: {error}")

    async def send_message(self, interaction: discord.Interaction, message: str) -> None:
        """sends the message to the channel."""
        try:
            await interaction.response.send_message(message, ephemeral=True)
        except discord.errors.HTTPException:
            pass
        except Exception as e:
            logging.error(e)
