import typing
from classes import confirm


import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy.orm import sessionmaker

import db
from classes import jsonmaker
Session = sessionmaker(bind=db.engine)
session = Session()


class config(commands.GroupCog, name="config"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def config(self, ctx, option="default", input: typing.Union[discord.TextChannel, discord.Role] = None):
        print(ctx.guild.id)
        c = session.query(db.config).filter_by(guild=ctx.guild.id).first()
        p = session.query(db.permissions).filter_by(guild=ctx.guild.id).first()
        match option:
            case "lobby":
                c.lobby = input.id
                session.commit()
                await ctx.send(f"Value **lobby** channel has been updated to {input.id}")
            case "agelog":
                c.agelog = input.id
                session.commit()
                await ctx.send(f"Value **agelog** channel has been updated to {input.id}")
            case "modlobby":
                c.modlobby = input.id
                session.commit()
                await ctx.send(f"Value **modlobby** channel has been updated to {input.id}")
            case "general":
                c.general = input.id
                session.commit()
                await ctx.send(f"Value **general** channel has been updated to {input.id}")
            case "admin":
                p.admin = input.id
                session.commit()
                await ctx.send(f"Value **admin** role has been updated to {input.id}")
            case "mod":
                p.mod = input.id
                session.commit()
                await ctx.send(f"Value **mod** role has been updated to {input.id}")
            case "trial":
                p.trial = input.id
                session.commit()
                await ctx.send(f"Value **trial** role has been updated to {input.id}")
            case "lobbystaff":
                p.lobbystaff = input.id
                session.commit()
                await ctx.send(f"Value **lobbyteam** role has been updated to {input.id}")
            case default:
                await ctx.send("""**Config options**: 
• lobby #channel
• agelog #channel
• modlobby #channel
• general #channel
• admin @role
• mod @role
• trial @role
• lobbystaff @role""")
        session.close()

    @app_commands.command(name="updater", description="Updates all user configs")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def ageadd(self, interaction: discord.Interaction):
        await interaction.response.send_message("updater started. please hold.")
        await jsonmaker.Updater.update(self)
        await interaction.channel.send("Updater done")

    @app_commands.command(name="roulette", description="sets roulette channel")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def crouls(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.send_message("updating roulette channel")
        await jsonmaker.guildconfiger.roulette(interaction.guild.id, channel.id, 'roulette')
        await interaction.channel.send(f"{channel.mention} is now the new roulette channel")

    @app_commands.command(name="reminder", description="Sets the search forum reminder")
    @app_commands.checks.has_permissions(manage_guild=True)
    async def reminder(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        title = "New forum reminder"
        desc = "Submit a message of maximum 1900 characters."
        text = await confirm.ConfirmDialogue.input(self.bot, discord, interaction, desc, title)
        await interaction.followup.send("updating rule reminder")
        await jsonmaker.guildconfiger.edit_string(interaction.guild.id, text, 'reminder')
        await interaction.channel.send(f"New reminder: \n {text}")


async def setup(bot: commands.Bot):
    await bot.add_cog(config(bot))


session.commit()
