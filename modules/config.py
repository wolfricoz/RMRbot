import discord
from discord.ext import commands
from abc import ABC, abstractmethod
import db
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, column
import typing

Session = sessionmaker(bind=db.engine)
session = Session()

class config(commands.Cog, name="config"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def config(self,ctx, option = "default", input : typing.Union[discord.TextChannel, discord.Role] = None):
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
            case default:
                await ctx.send("""**Config options**: 
• lobby #channel
• agelog #channel
• modlobby #channel
• general #channel
• admin @role
• mod @role
• trial @role""")


async def setup(bot: commands.Bot):
    await bot.add_cog(config(bot))

session.commit()