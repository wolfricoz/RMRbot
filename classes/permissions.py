import discord
from discord import app_commands
from discord.ext import commands

from classes.databaseController import configData


def check_roles():
    async def pred(ctx):
        modroles = configData().get_key(ctx.guild.id, 'mod')
        adminroles = configData().get_key(ctx.guild.id, 'admin')
        user_roles = [x.id for x in ctx.user.roles]
        return any(x in adminroles for x in user_roles) or any(x in modroles for x in user_roles)

    return commands.check(pred)


def check_roles_admin():
    async def pred(ctx):
        adminroles = configData().get_key(ctx.guild.id, 'admin')
        user_roles = [x.id for x in ctx.user.roles]
        return any(x in adminroles for x in user_roles)

    return commands.check(pred)


def check_app_roles():
    async def pred(interaction: discord.Interaction):
        modroles = configData().get_key(interaction.guild.id, 'mod')
        adminroles = configData().get_key(interaction.guild.id, 'admin')
        user_roles = [x.id for x in interaction.user.roles]
        return any(x in adminroles for x in user_roles) or any(x in modroles for x in user_roles)

    return app_commands.check(pred)


def check_app_roles_admin():
    async def pred(interaction):
        adminroles = configData().get_key(interaction.guild.id, 'admin')
        user_roles = [x.id for x in interaction.user.roles]
        return any(x in adminroles for x in user_roles)

    return app_commands.check(pred)
