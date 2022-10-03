import discord
from discord.ext import commands
from datetime import datetime
import adefs
from abc import ABC, abstractmethod
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, column
import typing
from discord import app_commands
import db

Session = sessionmaker(bind=db.engine)
session = Session()

class advert(ABC):
    @abstractmethod
    async def clogadvert(ctx, msg, warning, lc):
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

    async def csendadvertuser(ctx, msg, warning):
        user = msg.author
        try:
            await user.send(warning)
            await user.send("**__The removed advert: (Please make the required changes before reposting.)__**")
            if len(msg.content) < 2000:
                await user.send(msg.content)
            if len(msg.content) > 2000:
                await user.send(msg.content[0:2000])
                await user.send(msg.content[2000:4000])
        except:
            await ctx.send("Can't DM user")
            pass

    async def cincreasewarnings(ctx, user):
        exists = session.query(db.warnings).filter_by(uid=user.id).first()
        if exists is not None:
            exists.swarnings += 1
            session.commit()
            return exists.swarnings
        else:
            tr = db.warnings(member.id, 1)
            session.add(tr)
            session.commit()
            exists = session.query(db.warnings).filter_by(uid=user.id).first()
            return exists.swarnings

class contextmenus(commands.Cog, name="contextmenus"):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.ctx_menu = app_commands.ContextMenu(name="adages",callback=self.madages,)
        self.bot.tree.add_command(self.ctx_menu)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.ctx_menu.name, type=self.ctx_menu.type)


    async def madages(self, interaction: discord.Interaction, message: discord.Message) -> None:  # An annotation of discord.Message makes this a message command
        await interaction.response.send_message(f"This command is a work in progress, here is the message \n {message.content}")

async def setup(bot: commands.Bot):
    await bot.add_cog(contextmenus(bot))