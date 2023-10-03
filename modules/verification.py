import datetime
import os
import re
from abc import ABC, abstractmethod

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

import classes.permissions as permissions
import databases.current
from classes.AgeCalculations import AgeCalculations
from classes.databaseController import UserTransactions, ConfigData, VerificationTransactions


# the base for a cog.
class verification(commands.GroupCog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    @app_commands.choices(operation=[Choice(name=x, value=x) for x in
                                     ['add', 'update', 'get']])
    @app_commands.choices(toggle=[Choice(name=x, value=x) for x in
                                  ["True", "False"]])
    @permissions.check_app_roles()
    async def idcheck(self, interaction: discord.Interaction, operation: Choice['str'], toggle: Choice['str'],
                      userid: str, reason: str = None):
        if toggle.value == "True":
            toggle = True
        elif toggle.value == "False":
            toggle = False
        await interaction.response.defer(ephemeral=True)
        match operation.value.upper():
            case "UPDATE":
                if reason is None:
                    await interaction.followup.send(f"Please include a reason")
                    return
                VerificationTransactions.update_check(userid, reason, toggle)
                await interaction.followup.send(
                    f"<@{userid}>'s userid entry has been updated with reason: {reason} and idcheck: {toggle}")
            case "ADD":
                if reason is None:
                    await interaction.followup.send(f"Please include a reason")
                    return
                VerificationTransactions.add_idcheck(userid, reason, toggle)
                await interaction.followup.send(
                        f"<@{userid}>'s userid entry has been added with reason: {reason} and idcheck: {toggle}")
            case "GET":
                user = VerificationTransactions.get_id_info(userid)
                if user is None:
                    await interaction.followup.send("Not found")
                    return
                await interaction.followup.send(f"**__USER INFO__**\n"
                                                f"user: <@{user.uid}>\n"
                                                f"Reason: {user.reason}\n"
                                                f"idcheck: {user.idcheck}\n"
                                                f"idverifier: {user.idverified}\n"
                                                f"verifieddob: {user.verifieddob}\n")



async def setup(bot):
    await bot.add_cog(verification(bot))
