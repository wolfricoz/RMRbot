"""Creates a custom warning modal for the bot."""
import logging

import discord

from classes.Advert import Advert
from classes.databaseController import ConfigData


class Custom(discord.ui.Modal, title='Custom Warning'):
    custom_id = "cw"

    def __init__(self, bot, thread, thread_channel, warn):
        super().__init__(timeout=None)  # Set a timeout for the modal
        logging.info(f'warning modal created with warn: {type(warn)}' )
        self.bot = bot
        self.thread = thread
        self.thread_channel = thread_channel
        self.warn = warn

    reason = discord.ui.TextInput(label='What is the reason?', style=discord.TextStyle.long, placeholder='Type your waning here...', max_length=512)

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
        warning = await Advert.send_in_channel(interaction, user, thread_channel, self.reason.value, "Custom", modchannel, self.warn)
        # Logs the advert and sends it to the user.
        await Advert.logadvert(thread, loggingchannel)
        reminder = "**__The removed advert: (Please make the required changes before reposting.)__**"
        await Advert.send_advert_to_user(interaction, thread, reminder, self.reason.value)
        try:
            await self.send_message(interaction, f"{user.mention} has been warned for: {self.reason.value}")
        except discord.errors.HTTPException:
            pass



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
