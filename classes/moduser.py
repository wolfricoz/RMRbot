import logging
from abc import ABC, abstractmethod
from datetime import datetime

import discord
from discord.app_commands import AppCommandError

import classes.databaseController
from classes.databaseController import ConfigData, VerificationTransactions


class ModUser(ABC):

    @staticmethod
    @abstractmethod
    async def ban_user(interaction, member, bot, reason, appeal, idlist):
        """Checks the selected options, and ensures user doesn't ban self."""
        if member == interaction.user:
            await interaction.followup.send(f"Error: user ID belongs to {member.mention}.")
            return
        await ModUser.ban_user_from_guilds(interaction, member, bot, reason, appeal)
        if idlist.name.upper() == "YES":
            VerificationTransactions.set_idcheck_to_true(member.id, f"BAN: {reason}")
            await interaction.channel.send(f"{member}({member.id}) added to ID list")

    @staticmethod
    @abstractmethod
    async def ban_user_from_guilds(interaction, member, bot, reason, appeal):
        """This bans the user from the servers; by cycling through the bot.guilds"""
        rguilds = []
        try:
            if member in interaction.guild.members:
                await member.send(f"You've been banned from {interaction.guild} with reason: \n {reason} \n\n {appeal.value}")
        except Exception as e:
            logging.exception(f"Can't DM {member}\nReason: {e}")
        else:
            for guild in bot.guilds:
                user2 = await bot.fetch_user(member.id)
                try:
                    await guild.ban(user2, reason=reason, delete_message_days=0)
                    # await interaction.channel.send("BAN DISABLED: TESTING MODE ON.")
                    # Logs the ban into the correct channel
                    await ModUser.log_ban(interaction, member, reason, guild, typeofaction="banned")
                    rguilds.append(guild.name)
                except Exception as e:
                    print(f"{guild} could not ban, permissions? \n {AppCommandError}")
                    await interaction.followup.send(f"User was not in {guild}, could not ban. Please do this manually.\n"
                                                    f"reason: {e}")
            guilds = ", ".join(rguilds)
            await ModUser.notify_ban(interaction, member, reason, interaction.guild, typeofaction="banned", servers=guilds)


    @staticmethod
    @abstractmethod
    async def log_ban(interaction, member, reason, guild, typeofaction):
        """Catch all logging function for all the warnings. No more repeating."""

        try:
            log = guild.get_channel(ConfigData().get_key_int(guild.id, "warnlog"))
            banlog = guild.get_channel(ConfigData().get_key_int(guild.id, "blog"))
        except Exception as e:
            await interaction.guild.owner.send(f"config error in {guild.name}: {e}")
            logging.exception(f"{guild.name}: {e}")
            return
        try:
            embed = discord.Embed(title=f"{member.name} {typeofaction}",
                                  description=f"**Mention:** {member.mention} \n**UID:** {member.id}\n **Reason:** \n{reason}")
            embed.set_footer(text=f"Time:{datetime.now().strftime('%m/%d/%Y, %H:%M:%S')}")
            await log.send(embed=embed)
            if typeofaction == "banned":
                await banlog.send(embed=embed)
        except classes.databaseController.KeyNotFound as e:

            logging.exception(f"{guild.name}: {e}")

    @staticmethod
    @abstractmethod
    async def notify_ban(interaction: discord.Interaction, member, reason, guild, typeofaction, servers=None):
        """Catch all logging function for all the warnings. No more repeating."""
        try:
            embed = discord.Embed(title=f"{member.name} {typeofaction}",
                                  description=f"**Mention:** {member.mention} \n**UID:** {member.id}\n **Reason:** \n{reason}")
            embed.set_footer(text=f"Time:{datetime.now().strftime('%m/%d/%Y, %H:%M:%S')} {f'servers:{servers}' if servers else ''}")
            await interaction.channel.send(embed=embed)
        except classes.databaseController.KeyNotFound as e:
            await interaction.guild.owner.send(f"could not send ban notification to {interaction.guild.name} \n")
            logging.exception(f"{guild.name}: {e}")
