import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

from classes.databaseController import ConfigTransactions



class config(commands.GroupCog, name="config"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
    #this command is used for unique keys. Roles will need their own command due to not being unique.
    keys = ["dev", 'helpchannel', 'inviteinfo']
    actions = ['set', 'Remove']

    def check(self, key:str, value:str):
        intkeys = ["dev", "mod", "admin"]
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


    @app_commands.command()
    @app_commands.choices(key=[Choice(name=x, value=x) for x in keys])
    @app_commands.choices(action=[Choice(name=x, value=x) for x in actions])
    @commands.has_permissions(manage_guild=True)
    async def settings(self, interaction: discord.Interaction, key: Choice[str], action: Choice[str], value: str = None):
        await interaction.response.defer(ephemeral=True)
        check, reason = self.check(key.value, value)
        match action.value.lower():
            case 'set':
                if check is False:
                    await interaction.followup.send(reason)
                    return
                ConfigTransactions.config_unique_add(guildid=interaction.guild.id, key=key.value, value=value, overwrite=True)
                await interaction.followup.send(f"{key.value} has been added to the database with value:\n{value}")
            case 'remove':
                result = ConfigTransactions.config_unique_remove(guildid=interaction.guild.id, key=key.value)
                if result is False:
                    await interaction.followup.send(f"{key.value} was not in database")
                    return
                await interaction.followup.send(f"{key.value} has been removed from the database")
            case _:
                raise NotImplementedError

    rkeys = ["mod", "admin"]
    ractions = ['add', 'Remove']
    @app_commands.command()
    @app_commands.choices(key=[Choice(name=x, value=x) for x in rkeys])
    @app_commands.choices(action=[Choice(name=x, value=x) for x in ractions])
    @commands.has_permissions(manage_guild=True)
    async def roles(self, interaction: discord.Interaction, key: Choice[str], action: Choice[str], value: discord.Role):
        await interaction.response.defer(ephemeral=True)
        value = value.id
        match action.value.lower():
            case 'add':
                result = ConfigTransactions.config_key_add(guildid=interaction.guild.id, key=key.value, value=value, overwrite=False)
                if result is False:
                    await interaction.followup.send(f"{key.value} <@&{value}> already exists")
                    return
                await interaction.followup.send(f"{key.value} <@&{value}> has been added to the database")
            case 'remove':
                result = ConfigTransactions.config_key_remove(guildid=interaction.guild.id, key=key.value, value=value)
                await interaction.followup.send(f"{key.value} <@&{value}> has been removed from the database")
            case _:
                raise NotImplementedError
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


