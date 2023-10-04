import enum
import os
import typing

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from classes.databaseController import ConfigTransactions, ConfigData


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

    keys = ['welcomemessage', "lobbywelcome"]
    actions = ['set', 'Remove']

    @app_commands.command()
    @app_commands.choices(key=[Choice(name=x, value=x) for x in keys])
    @app_commands.choices(action=[Choice(name=x, value=x) for x in actions])
    @app_commands.checks.has_permissions(manage_guild=True)
    async def messages(self, interaction: discord.Interaction, key: Choice[str], action: Choice[str],
                       value: str = None):
        await interaction.response.defer(ephemeral=True)
        check, reason = self.check(key.value, value)
        match action.value.lower():
            case 'set':
                if check is False:
                    await interaction.followup.send(reason)
                    return
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
                               ["dev", 'helpchannel', 'inviteinfo', 'general', "lobby", "lobbylog", "lobbymod", "idlog"]])
    @app_commands.choices(action=[Choice(name=x, value=x) for x in actions])
    @app_commands.checks.has_permissions(manage_guild=True)
    async def channels(self, interaction: discord.Interaction, key: Choice[str], action: Choice[str],
                       value: discord.TextChannel = None):
        await interaction.response.defer(ephemeral=True)
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

    rkeys = {"moderator": "mod", "administrator": "admin", 'add to user': 'add', 'remove from user': "rem",
             "18+ role": "18", "21+ role": "21", "25+ role": "25", "return to lobby": "return"}
    ractions = ['add', 'Remove']

    @app_commands.command()
    @app_commands.choices(key=[Choice(name=ke, value=val) for ke, val in rkeys.items()])
    @app_commands.choices(action=[Choice(name=x, value=x) for x in ractions])
    @app_commands.checks.has_permissions(manage_guild=True)
    async def roles(self, interaction: discord.Interaction, key: Choice[str], action: Choice[str], value: discord.Role):
        await interaction.response.defer(ephemeral=True)
        value = value.id
        match action.value.lower():
            case 'add':
                result = ConfigTransactions.config_key_add(guildid=interaction.guild.id, key=key.value.upper(),
                                                           value=value, overwrite=False)
                if result is False:
                    await interaction.followup.send(f"{key.name} <@&{value}> already exists")
                    return
                await interaction.followup.send(f"{key.name} <@&{value}> has been added to the database")
            case 'remove':
                result = ConfigTransactions.config_key_remove(guildid=interaction.guild.id, key=key.value.upper(),
                                                              value=value)
                if result is False:
                    await interaction.followup.send(f"{key.name} <@&{value}> could not be found in database")
                await interaction.followup.send(f"{key.name} <@&{value}> has been removed from the database")
            case _:
                raise NotImplementedError

    @app_commands.command()
    @app_commands.choices(action=[Choice(name=x, value=x) for x in ractions])
    @app_commands.checks.has_permissions(manage_guild=True)
    async def searchcommands(self, interaction: discord.Interaction, action: Choice[str],name: str, message: str):
        await interaction.response.defer(ephemeral=True)
        if len(name) > 10:
            await interaction.followup.send("Please keep the name under 10 characters")
            return
        key = f"SEARCH-{name}"
        match action.value.lower():
            case 'add':
                result = ConfigTransactions.config_unique_add(guildid=interaction.guild.id, key=key.upper(),
                                                           value=message, overwrite=False)
                if result is False:
                    await interaction.followup.send(f"{name} already exists")
                    return
                await interaction.followup.send(f"{name} <@&{message}> has been added to the database")
            case 'remove':
                result = ConfigTransactions.config_key_remove(guildid=interaction.guild.id, key=key.upper(),
                                                              value=message)
                if result is False:
                    await interaction.followup.send(f"{key.name} could not be found in database")
                await interaction.followup.send(f"{key.name} <@&{message}> has been removed from the database")
            case _:
                raise NotImplementedError

    @app_commands.command()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def view(self, interaction: discord.Interaction):
        await interaction.response.defer()
        config = ConfigData().get_config(interaction.guild.id)

        with open('config.txt', 'w') as file:
            file.write(f"Config for {interaction.guild.name}: \n\n")
            for key, value in config.items():
                file.write(f"{key}: {value}\n")
        await interaction.followup.send(f"Config for {interaction.guild.name}", file=discord.File(file.name))
        os.remove(file.name)

    async def test_autocompletion(self, interaction: discord.Interaction, current:str) -> typing.List[app_commands.Choice[str]]:
        data = []
        search_commands = ConfigData().get_key(interaction.guild.id, "SEARCH")
        print(search_commands)
        for x in search_commands:
            if current.lower() in x:
                data.append(app_commands.Choice(name=x.lower(), value=x))
        return data
    @app_commands.command()
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.autocomplete(test=test_autocompletion)
    async def view_test(self, interaction: discord.Interaction, test: str):
        print(test)



    # class Fruits(enum.Enum):
    #     apple = 1
    #     banana = 2
    #     cherry = 3
    #
    # @app_commands.command()
    # @app_commands.describe(fruits='fruits to choose from')
    # async def fruit(interaction: discord.Interaction, fruits: Fruits):
    #     await interaction.response.send_message(f'Your favourite fruit is {fruits}.')

    # @app_commands.command(name="updater", description="Updates all user configs")
    # @app_commands.checks.has_permissions(manage_guild=True)
    # async def ageadd(self, interaction: discord.Interaction):
    #     await interaction.response.send_message("updater started. please hold.")
    #     await jsonmaker.Updater.update(self)
    #     await interaction.channel.send("Updater done")
    #
    # @app_commands.command(name="roulette", description="sets roulette channel")
    # @app_commands.checks.has_permissions(manage_guild=True)
    # async def crouls(self, interaction: discord.Interaction, channel: discord.TextChannel):
    #     await interaction.response.send_message("updating roulette channel")
    #     await jsonmaker.guildconfiger.roulette(interaction.guild.id, channel.id, 'roulette')
    #     await interaction.channel.send(f"{channel.mention} is now the new roulette channel")


async def setup(bot: commands.Bot):
    await bot.add_cog(config(bot))
