import discord
from discord.ext import commands
from abc import ABC, abstractmethod
import db
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, column
import typing
from discord import app_commands
Session = sessionmaker(bind=db.engine)
session = Session()

class slash(commands.Cog, name="slashtest"):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot


async def setup(bot: commands.Bot):
    await bot.add_cog(slash(bot))

session.commit()