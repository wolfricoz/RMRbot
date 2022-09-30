# IMPORT DISCORD.PY. ALLOWS ACCESS TO DISCORD'S API.
# IMPORT THE OS MODULE.
import logging
import os
import re
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
alogger = logging.getLogger('sqlalchemy')
alogger.setLevel(logging.ERROR)
handler2 = logging.FileHandler(filename='database.log', encoding='utf-8', mode='w')
handler2.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
alogger.addHandler(handler2)
# LOADS THE .ENV FILE THAT RESIDES ON THE SAME LEVEL AS THE SCRIPT.
load_dotenv('main.env')
channels72 = os.getenv('channels72')
spec = os.getenv('spec')
channels24 = os.getenv('channels24')
single = os.getenv('single')
test = os.getenv('test')
# GRAB THE API TOKEN FROM THE .ENV FILE.
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("PREFIX")
DBTOKEN = os.getenv("DB")
timetoken = os.getenv("timetoken")
#declares the bots intent
intents = discord.Intents.default()
intents.message_content= True
intents.members= True
bot = commands.Bot(command_prefix=PREFIX, case_insensitive=False, intents=intents)


exec(open("db.py").read())
db.engine.echo = False
@bot.command()
@commands.is_owner()
async def stop(ctx):
    await ctx.send("Rmrbot shutting down")
    exit()
@bot.command()
@commands.is_owner()
async def restart(ctx):
    await ctx.send("Rmrbot shutting down")
    exec(open("restart.py").read())
    exit()

invites = {}

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
            f"{message.author.mention}: You can repost in {message.channel.mention} at: {cooldown.strftime('%m/%d/%Y %I:%M:%S %p')} EST \nBy posting in this channel, you are agreeing to our search rules")
    #24h Version
    if str(message.channel.id) in channels24 and status == True:
        current = datetime.now(tz)
        cooldown = current + timedelta(hours=24)
        await message.author.send(
            f"{message.author.mention}: You can repost in {message.channel.mention} at: {cooldown.strftime('%m/%d/%Y %I:%M:%S %p')} EST \nBy posting in this channel, you are agreeing to our search rules")
    #single post version
    if str(message.channel.id) in single and status == True:
        current = datetime.now(tz)
        await message.author.send(
            "{}: You can repost in {} after the next purge.".format(message.author.mention, message.channel.mention) + "\nBy posting in this channel, you are agreeing to our search rules")
    await bot.process_commands(message)


@bot.listen()
async def on_message(message):
    modchannel = bot.get_channel(763058339088957548)
    user = message.author
    ad = message.channel
    messlength = len(message.content)
    listcount = 0
    if message.author.bot:
        return
    #length counters
    if str(message.channel.id) in channels24:
        if messlength > 650:
            await modchannel.send(f"{user.mention} in {ad.mention} has posted over 650 characters. \n Character Count: {messlength}")
            await message.add_reaction("❓")
        if messlength < 650:
            await message.add_reaction("🤖")
    elif str(message.channel.id) in channels72:
        if messlength < 600:
            await modchannel.send(f"{user.mention} in {ad.mention} has posted over under 600 characters. \n Character Count: {messlength}")
            await message.add_reaction("❓")
        if messlength > 600:
            await message.add_reaction("🤖")
        for i in message.content:
            if i == "-" or i == "•" or i == "»":
                listcount += 1
        if listcount >= 10:
            await modchannel.send(f"{user.mention} in {ad.mention} has potentially posted a list with too many options. \n list Count: {listcount}")
        else:
            pass
    elif str(message.channel.id) in spec:
        for i in message.content:
            if i == "-" or i == "•" or i == "»":
                listcount += 1
        if listcount >= 10:
            await modchannel.send(f"{user.mention} in {ad.mention} has potentially posted a list with too many options. \n list Count: {listcount}")
        else:
            pass


    else:
        return
#database sessionmaker
Session = sessionmaker(bind=db.engine)
session = Session()
@bot.listen()
async def on_message(message):
    #Enforces lobby format
    dobreg = re.compile("([0-9][0-9]) (1[0-2]|[0]?[0-9]|1)\/([0-3]?[0-9])\/([0-2][0-9][0-9][0-9])")
    match = dobreg.search(message.content)
    if message.guild is None:
        return
    if message.author.bot:
        return
    #Searches the config for the lobby for a specific guild
    p = session.query(db.permissions).filter_by(guild=message.guild.id).first()
    c = session.query(db.config).filter_by(guild=message.guild.id).first()
    staff = [p.mod, p.admin, p.trial]
    #reminder: change back to c.lobby
    if message.author.get_role(p.mod) is None and message.author.get_role(p.admin) is None and message.author.get_role(p.trial) is None:
        if message.channel.id == c.lobby :
            if match:
                channel = bot.get_channel(c.modlobby)
                await message.add_reaction("🤖")
                if int(match.group(1)) < 18:
                    await channel.send(f"<@&{p.lobbystaff}> {message.author.mention} has given an age under the age of 18: {message.content}")
                if int(match.group(1)) > 18 and not int(match.group(1)) > 20:
                    await channel.send(f"<@&{p.lobbystaff}> user has given age. You can let them through with `?18a {message.author.mention} {message.content}`")
                elif int(match.group(1)) > 21 and not int(match.group(1)) > 24:
                    await channel.send(f"<@&{p.lobbystaff}> user has given age. You can let them through with `?21a {message.author.mention} {message.content}`")
                elif int(match.group(1)) > 25:
                    await channel.send(f"<@&{p.lobbystaff}> user has given age. You can let them through with `?25a {message.author.mention} {message.content}`")
                return
            else:
                try:
                    await message.author.send(f"Please use format age mm/dd/yyyy \n Example: `122 01/01/1900` \n __**Do not round up your age**__ \n You can input your age and dob at: <#{c.lobby}>")
                except:
                    await message.channel.send(f"Couldn't message {message.author.mention}! Please use format age mm/dd/yyyy \n Example: `122 01/01/1900")
                await message.delete()
                return
    else:
        pass

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        import time
        await ctx.send("Please fill in the required arguments")
    elif isinstance(error, commands.CommandNotFound):
        pass
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("You do not have permission")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("User not found")
    elif isinstance(error, commands.CommandInvokeError):
        await ctx.send("Command failed: See log.")
        await ctx.send(error)
        raise error
    else:
        await ctx.send(error)
        raise error
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, column

# EVENT LISTENER FOR WHEN THE BOT HAS SWITCHED FROM OFFLINE TO ONLINE.
@bot.event
async def on_ready():
    devroom = bot.get_channel(987679198560796713)
    # CREATES A COUNTER TO KEEP TRACK OF HOW MANY GUILDS / SERVERS THE BOT IS CONNECTED TO.
    guild_count = 0
    guilds = []
    # LOOPS THROUGH ALL THE GUILD / SERVERS THAT THE BOT IS ASSOCIATED WITH.
    for guild in bot.guilds:
        #add invites
        invites[guild.id] = await guild.invites()
        # PRINT THE SERVER'S ID AND NAME.
        guilds.append(f"- {guild.id} (name: {guild.name})")

        # INCREMENTS THE GUILD COUNTER.
        guild_count = guild_count + 1
        exists = session.query(db.config).filter_by(guild=guild.id).first()
        if exists is not None:
            pass
        else:
            tr = db.config(guild.id, None, None, None, None)
            session.add(tr)
            session.commit()
        p = session.query(db.permissions).filter_by(guild=guild.id).first()
        if p is not None:
            pass
        else:
            tr = db.permissions(guild.id, None, None, None, None)
            session.add(tr)
            session.commit()
    # PRINTS HOW MANY GUILDS / SERVERS THE BOT IS IN.
    formguilds = "\n".join(guilds)
    await bot.tree.sync()
    await devroom.send(f"{formguilds} \nRMRbot is in {guild_count} guilds. RMRbot 1.5: Stronger than before")
    return guilds
@bot.event
async def on_guild_join(guild):
    #adds user to database
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
@bot.event
async def on_member_join(member):
    add = session.query(db.warnings).filter_by(uid=member.id).first()
    if add is not None:
        pass
    else:
        tr = warnings(member.id, 0)
        session.add(tr)
        session.commit()

def find_invite_by_code(invite_list, code):
    #makes an invite dictionary
    for inv in invite_list:
        if inv.code == code:
            return inv

@bot.listen()
async def on_member_join(member):
    #reads invite dictionary, and outputs user info
    invites_before_join = invites[member.guild.id]
    invites_after_join = await member.guild.invites()

    for invite in invites_before_join:
        if invite.uses < find_invite_by_code(invites_after_join, invite.code).uses:
            if member.guild.id == 395614061393477632:
                embed = discord.Embed(description=f"""Member {member} Joined
Invite Code: **{invite.code}**
Code created by: {invite.inviter} ({invite.inviter.id})
account created at: {member.created_at.strftime("%m/%d/%Y")}
Member joined at {datetime.now().strftime("%m/%d/%Y")}
""")
                embed.set_image(url=member.avatar.url)
                embed.set_footer(text=f"USERID: {member.id}")
                channel = bot.get_channel(692529154695889022)
                await channel.send(embed=embed)

                invites[member.guild.id] = invites_after_join

                return
            if member.guild.id == 780622396297183252:
                embed = discord.Embed(description=f"""Member {member} Joined
Invite Code: **{invite.code}**
Code created by: {invite.inviter} ({invite.inviter.id})
account created at: {member.created_at.strftime("%m/%d/%Y")}
Member joined at {datetime.now().strftime("%m/%d/%Y")}
""")
                embed.set_image(url=member.avatar.url)
                embed.set_footer(text=f"USERID: {member.id}")
                channel = bot.get_channel(1019029308620152902)
                await channel.send(embed=embed)

                invites[member.guild.id] = invites_after_join

                return


@bot.command()
@commands.is_owner()
async def addall(ctx):
    count = 0
    for member in ctx.guild.members:
        add = session.query(db.warnings).filter_by(uid=member.id).first()
        if add is not None:
            pass
        else:
            count += 1
            tr = db.warnings(member.id, 0)
            session.add(tr)
            session.commit()
        continue
    await ctx.send(f"added {count} members to the database")
#cogloader
@bot.event
async def setup_hook():
    for filename in os.listdir("modules"):

        if filename.endswith('.py'):
            await bot.load_extension(f"modules.{filename[:-3]}")
            print({filename[:-3]})
        else:
            print(f'Unable to load {filename[:-3]}')

@bot.event
async def on_member_remove(member):

    invites[member.guild.id] = await member.guild.invites()


@bot.command(aliases=["cr", "reload"])
@commands.is_owner()
async def cogreload(ctx):
    filesloaded = []
    for filename in os.listdir("modules"):
        if filename.endswith('.py'):
            await bot.reload_extension(f"modules.{filename[:-3]}")
            filesloaded.append(filename[:-3])
    fp = ', '.join(filesloaded)
    await ctx.send(f"Modules loaded: {fp}")




# EXECUTES THE BOT WITH THE SPECIFIED TOKEN.
bot.run(DISCORD_TOKEN)
