# IMPORT DISCORD.PY. ALLOWS ACCESS TO DISCORD'S API.
# IMPORT THE OS MODULE.
import logging
import os
import pytz
import discord
from datetime import datetime
from discord.ext import commands
from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import db
# IMPORT LOAD_DOTENV FUNCTION FROM DOTENV MODULE.
from dotenv import load_dotenv
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
# LOADS THE .ENV FILE THAT RESIDES ON THE SAME LEVEL AS THE SCRIPT.
load_dotenv('main.env')

# GRAB THE API TOKEN FROM THE .ENV FILE.
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("PREFIX")
DBTOKEN = os.getenv("DB")
timetoken = os.getenv("timetoken")
# GETS THE CLIENT OBJECT FROM DISCORD.PY. CLIENT IS SYNONYMOUS WITH BOT.
intents = discord.Intents.default()
intents.message_content= True
bot = commands.Bot(command_prefix=PREFIX, case_insensitive=False, intents=intents)




@bot.command()
@commands.is_owner()
async def stop(ctx):
    await ctx.send("Rmrbot shutting down")
    exit()

# slash commands
''''@slash.slash(
    name="sher",
    description="A screechy void",
    guild_ids="395614061393477632"
)'''
'''channel : discord.TextChannel,'''

@bot.command(name="sher", description="Oh god")
async def sher(ctx):
    await ctx.send(f"<:void:654990134957178901> **SCREEEEEEECHES**")


# events
@bot.event
async def on_message(message):
    status = True
    tz = pytz.timezone("US/Eastern")
    from datetime import datetime, timedelta
    if message.author.bot:
        return
    #72h Version
    if str(message.channel.id) in channels72 and status == True:
        current = datetime.now(tz)
        cooldown = current + timedelta(hours=72)
        await message.author.send(
            f"{message.author.mention}: You can repost in {message.channel.mention} at: {cooldown.strftime('%d/%m/%Y %I:%M:%S %p')} EST \nBy posting in this channel, you are agreeing to our search rules")
    #24h Version
    if str(message.channel.id) in channels24 and status == True:
        current = datetime.now()
        cooldown = current + timedelta(hours=24)
        await message.author.send(
            f"{message.author.mention}: You can repost in {message.channel.mention} at: {cooldown.strftime('%d/%m/%Y %I:%M:%S %p')} EST \nBy posting in this channel, you are agreeing to our search rules")
    #single post version
    if str(message.channel.id) in single and status == True:
        current = datetime.now()
        await message.author.send(
            "{}: You can repost in {} after the next purge.".format(message.author.mention, message.channel.mention) + "\nBy posting in this channel, you are agreeing to our search rules")
    await bot.process_commands(message)


@bot.listen()
async def on_message(message):
    modchannel = bot.get_channel(763058339088957548)
    user = message.author
    ad = message.channel
    messlength = len(message.content)
    if message.author.bot:
        return
    if str(message.channel.id) in channels24:
        if messlength > 650:
            await modchannel.send(f"{user.mention} in {ad.mention} has posted over 650 characters. \n Character Count: {messlength}")
            await message.add_reaction("❓")
        if messlength < 650:
            await message.add_reaction("🤖")
    else:
        return


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        import time
        await ctx.send("Please fill in the required arguments")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found.")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("You do not have permission")
    else:
        raise error
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, column

Session = sessionmaker(bind=db.engine)
session = Session()
# EVENT LISTENER FOR WHEN THE BOT HAS SWITCHED FROM OFFLINE TO ONLINE.
@bot.event
async def on_ready():
    # CREATES A COUNTER TO KEEP TRACK OF HOW MANY GUILDS / SERVERS THE BOT IS CONNECTED TO.
    guild_count = 0

    # LOOPS THROUGH ALL THE GUILD / SERVERS THAT THE BOT IS ASSOCIATED WITH.
    for guild in bot.guilds:
        # PRINT THE SERVER'S ID AND NAME.
        print(f"- {guild.id} (name: {guild.name})")

        # INCREMENTS THE GUILD COUNTER.
        guild_count = guild_count + 1
        exists = session.query(db.config).filter_by(guild=guild.id).first()
        print(exists)
        if exists is not None:
            pass
        else:
            tr = config(guild.id, None, None, None, None)
            session.add(tr)
            session.commit()
        p = session.query(db.permissions).filter_by(guild=guild.id).first()
        if p is not None:
            pass
        else:
            tr = permissions(guild.id, None, None, None)
            session.add(tr)
            session.commit()
    # PRINTS HOW MANY GUILDS / SERVERS THE BOT IS IN.
    print("rmrbot is in " + str(guild_count) + " guilds.")
@bot.event
async def on_guild_join(guild):
    exists = session.query(db.config).filter_by(guild=guild.id).first()
    if exists is not None:
        pass
    else:
        tr = config(guild.id, None, None, None, None)
        session.add(tr)
        session.commit()
    p = session.query(db.permissions).filter_by(guild=guild.id).first()
    if p is not None:
        pass
    else:
        tr = permissions(guild.id, None, None, None)
        session.add(tr)
        session.commit()

#cogloader
@bot.event
async def setup_hook():
    for filename in os.listdir("modules"):
        if filename.endswith('.py'):
            await bot.load_extension(f"modules.{filename[:-3]}")
            print({filename[:-3]})
        else:
            print(f'Unable to load {filename[:-3]}')





@bot.command(alias=["cr"])
@commands.is_owner()
async def cogreload(ctx):
    for filename in os.listdir("modules"):
        if filename.endswith('.py'):
            await bot.reload_extension(f"modules.{filename[:-3]}")
            await ctx.send(f"{filename[:-3]}")
channels72 = os.getenv('channels72')
channels24 = os.getenv('channels24')
single = os.getenv('single')
test = os.getenv('test')


# EXECUTES THE BOT WITH THE SPECIFIED TOKEN.
bot.run(DISCORD_TOKEN)
