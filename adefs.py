import discord
from discord import app_commands
from discord.ext import commands
from abc import ABC, abstractmethod
from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from functools import lru_cache
import db
Session = sessionmaker(bind=db.engine)
session = Session()
def check_db_roles():
    async def pred(ctx):
        modrole = session.query(db.permissions).filter_by(guild=ctx.guild.id).first()
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
        modrole = session.query(db.permissions).filter_by(guild=ctx.guild.id).first()
        user_roles = ctx.message.author.roles
        if ctx.author.get_role(modrole.admin) is not None:
            return True
        else:
            return False

    return commands.check(pred)

def check_slash_db_roles():
    async def pred(interaction):
        modrole = session.query(db.permissions).filter_by(guild=interaction.guild.id).first()
        user_roles = interaction.user.roles
        if interaction.user.get_role(modrole.mod) is not None:
            return True
        elif interaction.user.get_role(modrole.admin) is not None:
            return True
        elif interaction.user.get_role(modrole.trial) is not None:
            return True
        elif interaction.user.get_role(modrole.trial) is None:
            return False
        else:
            return False
    return app_commands.check(pred)

def check_slash_admin_roles():
    async def pred(interaction):
        modrole = session.query(db.permissions).filter_by(guild=interaction.guild.id).first()
        user_roles = interaction.user.roles
        if interaction.user.get_role(modrole.admin) is not None:
            return True
        else:
            return False
    return app_commands.check(pred)