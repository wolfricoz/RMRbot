from abc import ABC, abstractmethod
from datetime import datetime

import discord

from classes.databaseController import SearchWarningTransactions, ConfigData


class Advert(ABC):

    @staticmethod
    @abstractmethod
    async def get_message(thread, interaction):
        if interaction.channel.type != discord.ChannelType.public_thread and thread is not None:
            link = thread.split('/')
            thread_channel = interaction.guild.get_thread(int(link[5]))
            thread = await thread_channel.fetch_message(int(link[6]))
            return thread, thread_channel
        thread_channel = interaction.guild.get_thread(interaction.channel.id)
        thread_message = await thread_channel.fetch_message(thread_channel.id)
        return thread_message, thread_channel

    @staticmethod
    @abstractmethod
    async def logadvert(msg, lc):
        user = msg.author
        await lc.send(
                f"{user.mention}\'s advert was removed at {datetime.now().strftime('%m/%d/%Y, %H:%M:%S')}. Contents:")
        if len(msg.content) < 2000:
            await lc.send(msg.content)
        if len(msg.content) > 2000:
            await lc.send(msg.content[0:2000])
            await lc.send(msg.content[2000:4000])
        if msg.channel.type is discord.ChannelType.text:
            print(f"This is a Text channel {msg.channel.id}")
            await msg.delete()
        elif msg.channel.type is discord.ChannelType.public_thread:
            print(f"This is a Thread channel {msg.channel.id}")
            await msg.channel.delete()
        else:
            print("Channel was neither")
            await msg.delete()

    @staticmethod
    @abstractmethod
    async def send_advert_to_user(interaction, msg, reminder, warning):
        """Sends the advert and the warning to the user."""
        user = msg.author
        count = 0
        try:
            if warning.lower() not in ["purge", "no"]:
                await user.send(warning)
            await user.send(reminder)
            while count < len(msg.content):
                await user.send(msg.content[count:count + 1950])
                count += 1950
        except discord.Forbidden:
            if isinstance(interaction, discord.Interaction) is False:
                await interaction.channel.send(f"Can't DM {user.mention}.")
            await interaction.followup.send(f"Can't DM {user.mention}.")
            pass



    @staticmethod
    @abstractmethod
    async def send_in_channel(interaction, user, thread_channel, reason, warning_type, modchannel, warn):
        """Sends the warning to the user and logs it in the mod channel."""
        warning = (f"Hello, I'm a staff member of **Roleplay Meets Reborn**. Your advert `{thread_channel.name}` has been removed with the following reason: \n"
                   f"{reason}"
                   f"\n\nIf you have any more questions, you can open a ticket at <#{ConfigData().get_key_int(interaction.guild.id, 'HELPCHANNEL')}>.")
        if warn.lower() == "yes":
            SearchWarningTransactions.add_warning(user.id, warning)
        total_warnings, active_warnings = SearchWarningTransactions.get_total_warnings(user.id)
        embed = discord.Embed(title=f"{thread_channel.name}", description=f"{interaction.user.mention} has warned {user.mention} with warning type: {warning_type}\nWarning user received:\n{warning}",
                              color=discord.Color.from_rgb(255, 117, 24))
        embed.set_footer(text=f"userId: {user.id} Active Warnings: {active_warnings} Total Warnings: {total_warnings}, warn: {warn}")
        await modchannel.send(f"{user.mention}", embed=embed)
        return warning
