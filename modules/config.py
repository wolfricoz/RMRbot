import os

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from classes.databaseController import ConfigTransactions, ConfigData
from views.modals.configinput import ConfigInputUnique


# noinspection PyUnresolvedReferences
class config(commands.GroupCog, name="config"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # this command is used for unique keys. Roles will need their own command due to not being unique.

    def check(self, key: str, value: str):
        intkeys = ["dev", "mod", "admin", 'general', 'helpchannel', ]
        # strkeys = ["welcome"]
        reason = ""
        if value is None:
            reason = "Please fill in the 'value' field."
            return False, reason
        if value.isdigit() is False and key.lower() in intkeys:
            reason = "This key only accepts integers (digits)"
            return False, reason
        # elif key.lower() in strkeys:
        #     reason = "This key only accepts strings (Text)"
        #     return False, reason
        return True, reason

    keys = ['welcomemessage', "lobbywelcome", "reminder"]
    actions = ['set', 'Remove']

    @app_commands.command()
    @app_commands.choices(key=[Choice(name=x, value=x) for x in keys])
    @app_commands.choices(action=[Choice(name=x, value=x) for x in actions])
    @app_commands.checks.has_permissions(manage_guild=True)
    async def messages(self, interaction: discord.Interaction, key: Choice[str], action: Choice[str],
                       ):
        match action.value.lower():
            case 'set':
                await interaction.response.send_modal(ConfigInputUnique(key=key.value))
            case 'remove':
                await interaction.response.defer(ephemeral=True)
                result = ConfigTransactions.config_unique_remove(guildid=interaction.guild.id, key=key.value)
                if result is False:
                    await interaction.followup.send(f"{key.value} was not in database")
                    return
                await interaction.followup.send(f"{key.value} has been removed from the database")
            case _:
                raise NotImplementedError

    @app_commands.command()
    @app_commands.choices(action=[Choice(name=x, value=x) for x in ["enabled", "disabled"]])
    @app_commands.checks.has_permissions(manage_guild=True)
    async def welcometoggle(self, interaction: discord.Interaction, action: Choice[str]):
        match action.value.upper():
            case "ENABLED":
                ConfigTransactions.toggle_welcome(interaction.guild.id, "WELCOME", action.value.upper())
            case "DISABLED":
                ConfigTransactions.toggle_welcome(interaction.guild.id, "WELCOME", action.value.upper())
        await interaction.response.send_message(f"Welcome has been set to {action.value}", ephemeral=True)

    @app_commands.command()
    @app_commands.choices(key=[Choice(name=x, value=x) for x in
                               ["dev", 'helpchannel', 'inviteinfo', 'general', "lobby", "lobbylog", "lobbymod",
                                "idlog", "advertmod", "advertlog", "nsfwlog", "warnlog"]])
    @app_commands.choices(action=[Choice(name=x, value=x) for x in actions])
    @app_commands.checks.has_permissions(manage_guild=True)
    async def channels(self, interaction: discord.Interaction, key: Choice[str], action: Choice[str],
                       value: discord.TextChannel = None):
        """adds the channels to the config, you can only add 1 value per option."""
        await interaction.response.defer(ephemeral=True)
        if value is not None:
            value = value.id
        match action.value.lower():
            case 'set':
                ConfigTransactions.config_unique_add(guildid=interaction.guild.id, key=key.value, value=value,
                                                     overwrite=True)
                await interaction.followup.send(f"{key.value} has been added to the database with value:\n{value}")
            case 'remove':
                result = ConfigTransactions.config_unique_remove(guildid=interaction.guild.id, key=key.value)
                if result is False:
                    await interaction.followup.send(f"{key.value} was not in database")
                    return
                await interaction.followup.send(f"{key.value} has been removed from the database")
            case _:
                raise NotImplementedError

    @app_commands.command()
    @app_commands.choices(action=[Choice(name=x, value=x) for x in ['add', 'remove']])
    @app_commands.checks.has_permissions(manage_guild=True)
    async def forums(self, interaction: discord.Interaction, action: Choice[str],
                     value: discord.ForumChannel = None):
        """Adds forums to the automod for checking. You can add multiple forums!"""
        await interaction.response.defer(ephemeral=True)
        value = value.id
        match action.value.lower():
            case 'add':
                ConfigTransactions.config_key_add(guildid=interaction.guild.id, key="FORUM", value=value,
                                                  overwrite=True)
                await interaction.followup.send(f"Forum has been added to the database with value:\n{value}")
            case 'remove':
                result = ConfigTransactions.config_key_remove(guildid=interaction.guild.id, key="FORUM", value=value)
                if result is False:
                    await interaction.followup.send(f"<#{value}> was not in database")
                    return
                await interaction.followup.send(f"<#{value}> has been removed from the database")
            case _:
                raise NotImplementedError

    rkeys = {"moderator": "mod", "administrator": "admin", 'add to user': 'add', 'remove from user': "rem", "18+ role": "18", "21+ role": "21", "25+ role": "25", "return to lobby": "return", "NSFW role": "NSFW", "Partner role": "partner", "Searchban role": "posttimeout"}
    ractions = ['add', 'Remove']

    @app_commands.command()
    @app_commands.choices(key=[Choice(name=ke, value=val) for ke, val in rkeys.items()])
    @app_commands.choices(action=[Choice(name=x, value=x) for x in ractions])
    @app_commands.checks.has_permissions(manage_guild=True)
    async def roles(self, interaction: discord.Interaction, key: Choice[str], action: Choice[str], value: discord.Role):
        """Add roles to the database, for the bot to use."""
        await interaction.response.defer(ephemeral=True)
        value = value.id
        match action.value.lower():
            case 'add':
                result = ConfigTransactions.config_key_add(guildid=interaction.guild.id, key=key.value.upper(),
                                                           value=value, overwrite=False)
                if result is False:
                    await interaction.followup.send(f"{key.name}: <@&{value}> already exists")
                    return
                await interaction.followup.send(f"{key.name}: <@&{value}> has been added to the database")
            case 'remove':
                result = ConfigTransactions.config_key_remove(guildid=interaction.guild.id, key=key.value.upper(),
                                                              value=value)
                if result is False:
                    await interaction.followup.send(f"{key.name}: <@&{value}> could not be found in database")
                await interaction.followup.send(f"{key.name}: <@&{value}> has been removed from the database")
            case _:
                raise NotImplementedError

    @app_commands.command()
    @app_commands.choices(action=[Choice(name=x, value=x) for x in ractions])
    @app_commands.checks.has_permissions(manage_guild=True)
    async def searchcommands(self, interaction: discord.Interaction, action: Choice[str], name: str):
        """Adds search command to the /forum warn command"""

        if len(name) > 10:
            await interaction.followup.send("Please keep the name under 10 characters")
            return
        key = f"SEARCH-{name}"
        match action.value.lower():
            case 'add':

                await interaction.response.send_modal(ConfigInputUnique(key=key))

            case 'remove':
                await interaction.response.defer(ephemeral=True)
                result = ConfigTransactions.config_unique_remove(guildid=interaction.guild.id, key=key.upper())
                if result is False:
                    await interaction.followup.send(f"{key.name} could not be found in database")
                await interaction.followup.send(f"{key.name} has been removed from the database")
            case _:
                raise NotImplementedError

    @app_commands.command()
    @app_commands.choices(action=[Choice(name=x, value=x) for x in ractions])
    @app_commands.checks.has_permissions(manage_guild=True)
    async def banmessages(self, interaction: discord.Interaction, action: Choice[str], name: str):
        """Adds an option to the /ban command."""

        if len(name) > 10:
            await interaction.followup.send("Please keep the name under 10 characters")
            return
        key = f"BAN-{name}"
        match action.value.lower():
            case 'add':
                await interaction.response.send_modal(ConfigInputUnique(key=key))
            case 'remove':
                await interaction.response.defer(ephemeral=True)
                result = ConfigTransactions.config_unique_remove(guildid=interaction.guild.id, key=key.upper())
                if result is False:
                    await interaction.followup.send(f"{key.name} could not be found in database")
                await interaction.followup.send(f"{key.name} has been removed from the database")
            case _:
                raise NotImplementedError

    @app_commands.command()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def view(self, interaction: discord.Interaction):
        await interaction.response.defer()
        config_data = ConfigData().get_config(interaction.guild.id)

        with open('config.txt', 'w') as file:
            file.write(f"Config for {interaction.guild.name}: \n\n")
            for key, value in config_data.items():
                file.write(f"{key}: {value}\n")
        await interaction.followup.send(f"Config for {interaction.guild.name}", file=discord.File(file.name))
        os.remove(file.name)


async def setup(bot: commands.Bot):
    await bot.add_cog(config(bot))
