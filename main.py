# IMPORT DISCORD.PY. ALLOWS ACCESS TO DISCORD'S API.
# IMPORT THE OS MODULE.
import asyncio
import logging
import os
from contextlib import asynccontextmanager

import discord
from discord.ext import commands
# IMPORT LOAD_DOTENV FUNCTION FROM DOTENV MODULE.
from dotenv import load_dotenv
from fastapi import FastAPI

import api

from classes import permissions
from classes.automod import AutoMod
from databases.transactions.ConfigData import ConfigData
from databases.transactions.ConfigTransactions import ConfigTransactions
from databases.transactions.UserTransactions import UserTransactions
from databases import current as db
from views.buttons.PostOptions import PostOptions

# Creating database
db.database.create()
# Declares the bots intent

# Load the data from env
load_dotenv('.env')
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("PREFIX")
# TODO: dead code - DBTOKEN is never used
DBTOKEN = os.getenv("DB")
version = os.getenv('VERSION')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
activity = discord.Activity(type=discord.ActivityType.watching, name="over RMR")
bot = commands.Bot(command_prefix=PREFIX, case_insensitive=True, intents=intents, activity=activity)
bot.DEV = int(os.getenv("DEV"))
# TODO: dead code - bot.KEY is never read (classes/encryption.py reads KEY from the env itself)
bot.KEY = os.getenv("KEY")


# Runs the bot inside the API when started with uvicorn (API=TRUE in .env).
@asynccontextmanager
async def lifespan(app: FastAPI):
    async def run_bot():
        try:
            await bot.start(DISCORD_TOKEN)
        except asyncio.CancelledError:
            # Graceful cancellation
            await bot.close()
            raise
        except Exception as e:
            logging.error(f"Bot encountered an error: {e}", exc_info=True)
            raise

    bot_task = asyncio.create_task(run_bot())
    logging.info("Bot started.")
    app.state.bot = bot
    try:
        yield
    finally:
        # Trigger shutdown if still running
        if not bot.is_closed():
            await bot.close()
        # Ensure the task finishes
        if not bot_task.done():
            bot_task.cancel()
            try:
                await bot_task
            except asyncio.CancelledError:
                pass


app = FastAPI(lifespan=lifespan,
              docs_url=None,
              redoc_url=None,
              openapi_url=None,
              )
routers = []
for router in api.__all__:
    try:
        app.include_router(getattr(api, router))
        routers.append(router)
    except Exception as e:
        logging.error(f"Failed to load {router}: {e}", exc_info=True)


# Move to devtools?
@bot.command()
@commands.is_owner()
async def stop(ctx):
    await ctx.send("Rmrbot shutting down")
    exit()


bot.invites = {}


@bot.event
async def on_ready():
    devroom: discord.TextChannel = bot.get_channel(bot.DEV)
    # CREATES A COUNTER TO KEEP TRACK OF HOW MANY GUILDS / SERVERS THE BOT IS CONNECTED TO.
    guilds = []
    for guild in bot.guilds:
        bot.invites[guild.id] = await guild.invites()
        ConfigTransactions().server_add(guild.id)
        ConfigData().load_guild(guild.id)
        guilds.append(guild.name)
        bot.invites[guild.id] = await guild.invites()
    formguilds = "\n".join(guilds)
    await bot.tree.sync()
    await devroom.send(f"{formguilds} \nRMRbot is in {len(guilds)} guilds. RMRbot {version}")
    print("Commands synced, start up _done_")
    logging.info("Loaded routers: " + ", ".join(routers))
    bot.add_view(PostOptions(AutoMod))
    return guilds


# This can become its own cog.
@bot.event
async def on_guild_join(guild):
    # adds user to database
    ConfigTransactions().server_add(guild.id)
    ConfigData().load_guild(guild.id)


@bot.event
async def on_member_join(member):
    UserTransactions().add_user_empty(member.id)


# cogloader
@bot.event
async def setup_hook():
    # TODO: dead code - bot.lobbyages is never read
    bot.lobbyages = bot.get_channel(454425835064262657)
    for filename in os.listdir("modules"):

        if filename.endswith('.py'):
            await bot.load_extension(f"modules.{filename[:-3]}")
            print({filename[:-3]})
        else:
            print(f'Unable to load {filename[:-3]}')


@bot.command(aliases=["cr", "reload"])
@permissions.check_roles_admin()
async def cogreload(ctx):
    filesloaded = []
    for filename in os.listdir("modules"):
        if filename.endswith('.py'):
            await bot.reload_extension(f"modules.{filename[:-3]}")
            filesloaded.append(filename[:-3])
    fp = ', '.join(filesloaded)
    await ctx.send(f"Modules loaded: {fp}")
    await bot.tree.sync()


# EXECUTES THE BOT WITH THE SPECIFIED TOKEN. With API=TRUE the bot is started by uvicorn (uvicorn main:app) instead.
if os.getenv("API") != "TRUE":
    bot.run(DISCORD_TOKEN)
# Empty commit time