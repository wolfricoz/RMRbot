# IMPORT DISCORD.PY. ALLOWS ACCESS TO DISCORD'S API.
# IMPORT THE OS MODULE.
import json
import logging
import os
import sys
import traceback
from datetime import datetime

import discord
import pytz
from discord import Interaction
from discord.app_commands import AppCommandError
from discord.ext import commands, tasks
# IMPORT LOAD_DOTENV FUNCTION FROM DOTENV MODULE.
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker

import adefs
import db
import jsonmaker

# logger = logging.getLogger('discord')
# logger.setLevel(logging.DEBUG)
# handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='r+')
# handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
# logger.addHandler(handler)
# alogger = logging.getLogger('sqlalchemy')
# alogger.setLevel(logging.WARN)
# handler2 = logging.FileHandler(filename='database.log', encoding='utf-8', mode='r+')
# handler2.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
# alogger.addHandler(handler2)
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
activity = discord.Activity(type=discord.ActivityType.watching, name="over RMR")
bot = commands.Bot(command_prefix=PREFIX, case_insensitive=False, intents=intents, activity=activity)


exec(open("db.py").read())
db.engine.echo = False
@bot.command()
@commands.is_owner()
async def stop(ctx):
    await ctx.send("Rmrbot shutting down")
    exit()
def restart_bot():
  os.execv(sys.executable, ["python"] + sys.argv)
@bot.command()
@commands.is_owner()
async def restart(ctx):
    await ctx.send("Restarting bot...")
    restart_bot()
    await ctx.send("succesfully restarted")

invites = {}

@bot.command(name="sher", description="Oh god")
async def sher(ctx):
    await ctx.send(f"<:void:654990134957178901> **SCREEEEEEECHES**")


# events
@bot.event
async def on_message(message):
    await bot.process_commands(message)



#database sessionmaker
Session = sessionmaker(bind=db.engine)
session = Session()

# EVENT LISTENER FOR WHEN THE BOT HAS SWITCHED FROM OFFLINE TO ONLINE.
@bot.event
async def on_ready():
    devroom = bot.get_channel(987679198560796713)
    # CREATES A COUNTER TO KEEP TRACK OF HOW MANY GUILDS / SERVERS THE BOT IS CONNECTED TO.
    guild_count = 0
    guilds = []
    # LOOPS THROUGH ALL THE GUILD / SERVERS THAT THE BOT IS ASSOCIATED WITH.
    for guild in bot.guilds:
        await jsonmaker.guildconfiger.create(guild.id, guild.name)
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
            try:
                tr = db.config(guild.id, None, None, None, None)
                session.add(tr)
                session.commit()
            except:
                print("Database error, rolled back")
                session.rollback()
                session.close()
        p = session.query(db.permissions).filter_by(guild=guild.id).first()
        if p is not None:
            pass
        else:
            try:
                tr = db.permissions(guild.id, None, None, None, None)
                session.add(tr)
                session.commit()
            except:
                print("Database error, rolled back")
                session.rollback()

    # PRINTS HOW MANY GUILDS / SERVERS THE BOT IS IN.
    formguilds = "\n".join(guilds)
    await bot.tree.sync()
    await devroom.send(f"{formguilds} \nRMRbot is in {guild_count} guilds. RMRbot 3.0: You shall be matched.")
    session.close()
    print("Commands synced, start up _done_")
    return guilds

@bot.event
async def on_guild_join(guild):
    #adds user to database
    exists = session.query(db.config).filter_by(guild=guild.id).first()
    if exists is not None:
        pass
    else:
        try:
            tr = db.config(guild.id, None, None, None, None)
            session.add(tr)
            session.commit()
        except:
            print("Database error, rolled back")
            session.rollback()
            session.close()
    p = session.query(db.permissions).filter_by(guild=guild.id).first()
    if p is not None:
        pass
    else:
        try:
            tr = db.permissions(guild.id, None, None, None)
            session.add(tr)
            session.commit()
        except:
            print("Database error, rolled back")
            session.rollback()
            session.close()

@bot.event
async def on_member_join(member):
    add = session.query(db.warnings).filter_by(uid=member.id).first()
    if add is not None:
        pass
    else:
        try:
            tr = db.warnings(member.id, 0)
            session.add(tr)
            session.commit()
        except:
            print("Database error, rolled back")
            session.rollback()
            session.close()

    await jsonmaker.Configer.create(member.id, member)
@bot.command()
@commands.is_owner()
async def addall(ctx):
    count = 0
    concount = 0
    guildmembers = ctx.guild.members
    print(guildmembers)
    for member in guildmembers:

        add = session.query(db.warnings).filter_by(uid=member.id).first()
        if add is not None:
            pass
        else:
            count += 1
            tr = db.warnings(member.id, 0)
            session.add(tr)
            session.commit()
            continue
        # try:
        #     tr = warnings(member.id, 0)
        #     session.add(tr)
        #     session.commit()
        # except:
        #     print("Database error, rolled back")
        #     session.rollback()
        #     session.close()
    for member in guildmembers:
        try:
            await jsonmaker.Configer.create(member.id, member)
            concount += 1
        except:
            continue

    await ctx.send(f"added {count} members to the database\ncreated {concount} member configs")

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
                try:
                    embed.set_image(url=member.avatar.url)
                except:
                    pass
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
                try:
                    embed.set_image(url=member.avatar.url)
                except:
                    pass
                embed.set_footer(text=f"USERID: {member.id}")
                channel = bot.get_channel(1019029308620152902)
                await channel.send(embed=embed)

                invites[member.guild.id] = invites_after_join

                return



#cogloader
@bot.event
async def setup_hook():
    bot.lobbyages = bot.get_channel(454425835064262657)
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
@adefs.check_admin_roles()
async def cogreload(ctx):
    filesloaded = []
    for filename in os.listdir("modules"):
        if filename.endswith('.py'):
            await bot.reload_extension(f"modules.{filename[:-3]}")
            filesloaded.append(filename[:-3])
    fp = ', '.join(filesloaded)
    await ctx.send(f"Modules loaded: {fp}")
    session.rollback()
    session.close()
    db.engine.dispose()
    await bot.tree.sync()

@tasks.loop(hours=24)
async def printer(self):
    """Updates banlist when user is unbanned"""
    count = 0
    historydict = {}
    channel = self.bot.get_channel(454425835064262657)
    print(channel)
    print('creating cache...')
    time = datetime.datetime.now()
    async for h in channel.history(limit=None, oldest_first=True, before=time):
        historydict[h.id] = {}
        historydict[h.id]["author"] = h.author.id
        historydict[h.id]["created"] = h.created_at.strftime('%m/%d/%Y')
        historydict[h.id]["content"] = h.content
        count += 1
    else:
        print(f'Cached {count} message(s).')
    try:
        os.mkdir('config')
    except:
        pass
    with open('config/history.json', 'w') as f:
        json.dump(historydict, f, indent=4)
    print("[auto refresh]List updated")



# EXECUTES THE BOT WITH THE SPECIFIED TOKEN.
bot.run(DISCORD_TOKEN)
