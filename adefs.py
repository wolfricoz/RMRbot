import discord
from discord.ext import commands
from abc import ABC, abstractmethod
from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import db
Session = sessionmaker(bind=db.engine)
session = Session()

def check_db_roles():
    async def pred(ctx):
        print(ctx.guild.id)
        modrole = session.query(db.permissions).filter_by(guild=ctx.guild.id).first()
        print(modrole.mod)
        user_roles = ctx.message.author.roles
        if ctx.author.get_role(modrole.mod) is not None:
            return True
        elif ctx.author.get_role(modrole.admin) is not None:
            return True
        elif ctx.author.get_role(modrole.trial) is not None:
            return True
        elif ctx.author.get_role(modrole.trial) is None:
            return False
        else:
            return False

    return commands.check(pred)
def check_admin_roles():
    async def pred(ctx):
        print(ctx.guild.id)
        modrole = session.query(db.permissions).filter_by(guild=ctx.guild.id).first()
        print(modrole.mod)
        user_roles = ctx.message.author.roles
        if ctx.author.get_role(modrole.admin) is not None:
            return True
        else:
            return False

    return commands.check(pred)