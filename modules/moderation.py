import logging
from abc import ABC, abstractmethod
from datetime import datetime
from datetime import timedelta

import discord
import pytz
from discord import app_commands
from discord.app_commands import AppCommandError
from discord.app_commands import Choice
from discord.ext import commands
from sqlalchemy.orm import sessionmaker

import adefs
import db
from classes import jsonmaker

Session = sessionmaker(bind=db.engine)
session = Session()


class ModUser(ABC):
    @abstractmethod
    async def userbanned(self, ctx, member, bot, reason, appeal):
        rguilds = []
        if member == ctx.user:
            await ctx.followup.send(f"Error: user ID belongs to {member.mention}.")
            return
        try:
            if member in ctx.guild.members:
                await member.send(
                    f"You've been banned from {ctx.guild} with reason: \n {reason} \n\n {appeal.value}")
            else:
                print("member not found in server, can't dm")
        except:
            logging.exception(f"Can't DM {member}")
        else:
            for guild in bot.guilds:
                user = guild.get_member(member.id)
                user2 = await bot.fetch_user(member.id)
                try:
                    await guild.ban(user2, reason=reason, delete_message_days=0)
                    # await ctx.channel.send("BAN DISABLED: TESTING MODE ON.")
                    await ModUser.banlog(ctx, member, reason, guild)
                    rguilds.append(guild.name)
                except:
                    print(f"{guild} could not ban, permissions? \n {AppCommandError}")
                    await ctx.followup.send(f"User was not in {guild}, could not ban. Please do this manually.")
            print(rguilds)
            guilds = ", ".join(rguilds)
            embed = discord.Embed(title=f"{member.name} banned", description=reason)
            embed.set_footer(text=f"User removed from: {guilds}")
            await ctx.channel.send(embed=embed)

    @abstractmethod
    async def userbannedperm(self, ctx, member, bot, reason):
        rguilds = []
        if member == ctx.user:
            await ctx.followup.send(f"Error: user ID belongs to {member.mention}.")
        try:
            await member.send(
                f"You've been banned from {ctx.guild} with reason: \n {reason} \n\n This ban can __not__ be appealed")
        except:
            logging.exception(f"Can't DM {member}")
        else:
            for guild in bot.guilds:
                user = guild.get_member(member.id)
                user2 = await bot.fetch_user(member.id)
                try:
                    await guild.ban(user2, reason=reason, delete_message_days=0)
                    await ModUser.banlog(ctx, member, reason, guild)
                    rguilds.append(guild.name)
                except:
                    print(f"{guild} could not ban, permissions? \n {AppCommandError}")
                    await ctx.followup.send(f"User was not in {guild}, could not ban. Please do this manually.")
            print(rguilds)
            guilds = ", ".join(rguilds)
            embed = discord.Embed(title=f"{member.name} banned", description=reason)
            embed.set_footer(text=f"User removed from: {guilds}")
            await ctx.channel.send(embed=embed)

    async def userbannedid(self, ctx, member, bot, reason):
        rguilds = []
        if member == ctx.user:
            await ctx.followup.send(f"Error: user ID belongs to {member.mention}.")
        else:
            for guild in bot.guilds:
                user = guild.get_member(member.id)
                user2 = await bot.fetch_user(member.id)
                try:
                    await guild.ban(user2, reason=reason, delete_message_days=0)
                    await ModUser.banlog(ctx, member, reason, guild)
                    rguilds.append(guild.name)
                except:
                    print(f"{guild} could not ban, permissions? \n {AppCommandError}")
                    await ctx.followup.send(f"User was not in {guild}, could not ban. Please do this manually.")
            print(rguilds)
            guilds = ", ".join(rguilds)
            embed = discord.Embed(title=f"{member.name} banned", description=reason)
            embed.set_footer(text=f"User removed from: {guilds}")
            await ctx.channel.send(embed=embed)

    @abstractmethod
    def idcheckeradd(userid: int):
        idchecker = session.query(db.idcheck).filter_by(uid=userid).first()
        if idchecker is not None:
            idchecker.check = True
            session.commit()
        else:
            try:
                idcheck = db.idcheck(userid, True)
                session.add(idcheck)
                session.commit()
            except:
                session.rollback()
                session.close()
                logging.exception("failed to  log to database")

    async def banlog(ctx, member, reason, guild):
        embed = discord.Embed(title=f"{member.name} Banned",
                              description=f"**Mention:** {member.mention} \n**UID:** {member.id}\n **Reason:** \n{reason}")
        embed.set_footer(text=datetime.now().strftime('%m/%d/%Y, %H:%M:%S'))
        if guild.id == 395614061393477632:
            log = guild.get_channel(695112426642997279)
            await log.send(embed=embed)
        if guild.id == 780622396297183252:
            log = guild.get_channel(851651921823268874)
            await log.send(embed=embed)

    async def kicklog(ctx, member, reason, guild):
        embed = discord.Embed(title=f"{member.name} kicked",
                              description=f"**Mention:** {member.mention} \n**UID:** {member.id}\n **Reason:** \n{reason}")
        embed.set_footer(text=datetime.now().strftime('%m/%d/%Y, %H:%M:%S'))
        if guild.id == 395614061393477632:
            log = guild.get_channel(537365631675400192)
            await log.send(embed=embed)
        if guild.id == 780622396297183252:
            log = guild.get_channel(780622396595372039)
            await log.send(embed=embed)

    async def warnlog(ctx, member, reason, guild):
        embed = discord.Embed(title=f"{member.name} warned",
                              description=f"**Mention:** {member.mention} \n**UID:** {member.id}\n **Reason:** \n{reason}")
        embed.set_footer(text=datetime.now().strftime('%m/%d/%Y, %H:%M:%S'))
        await ctx.channel.send(embed=embed)
        if guild.id == 395614061393477632:
            log = guild.get_channel(537365631675400192)
            await log.send(embed=embed)
        if guild.id == 780622396297183252:
            log = guild.get_channel(780622396595372039)
            await log.send(embed=embed)

    async def searchban(ctx, member, reason, guild, time):
        embed = discord.Embed(title=f"{member.name} search banned",
                              description=f"**Mention:** {member.mention} \n**UID:** {member.id}\n **Reason:** \n{reason}\nTime: {time}")
        embed.set_footer(text=datetime.now().strftime('%m/%d/%Y, %H:%M:%S'))
        await ctx.channel.send(embed=embed)
        if guild.id == 395614061393477632:
            log = guild.get_channel(537365631675400192)
            await log.send(embed=embed)
        if guild.id == 780622396297183252:
            log = guild.get_channel(780622396595372039)
            await log.send(embed=embed)

    async def ban(self, interaction, member, bot, reason, type, appeal):
        if member == interaction.user:
            await interaction.followup.send(f"Error: user ID belongs to {member.mention}.")
            return
        elif type.name == "Custom":
            await ModUser.userbanned(self, interaction, member, bot, reason, appeal)
        elif type.name == "ID":
            preason = f"{member.name} {type.value}"
            await ModUser.userbanned(self, interaction, member, bot, preason, appeal)
            ModUser.idcheckeradd(int(member.id))
            await interaction.channel.send(f"{member}({member.id}) added to ID list")

        else:
            preason = f"{member.name} {type.value}"
            await ModUser.userbanned(self, interaction, member, bot, preason, appeal)


class moderation(commands.Cog, name="Moderation"):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="watchlist")
    @adefs.check_slash_db_roles()
    async def watchlist(self, interaction: discord.Interaction, user: discord.Member, *, reason: str):
        await interaction.response.send_message(f"adding {user} to watchlist", ephemeral=True)
        bot = self.bot
        # warnchannel = bot.get_channel(537365631675400192)
        watchlist = bot.get_channel(661375573649522708)
        await watchlist.send(f"""Name: {user.mention}
UID: {user.id}
username: {user}
reason {reason}""")

    @app_commands.command(name="ban", description="Bans user from all roleplay meets servers")
    @app_commands.choices(type=[
        Choice(name="ID",
               value="You have failed to ID after an age discrepancy was found, to protect our users you have been banned"),
        Choice(name="Pedophilia",
               value="Your rp profile/F-list/advert indicates a willingness to write with underaged characters/users."),
        Choice(name="Community",
               value="After discussion amongst the staff, we have decided that you are not fit to remain within RMR."),
        Choice(name="Custom", value="custom"),
    ],
        appeal=[
            Choice(name="Yes", value="To appeal this ban, you can send an email to roleplaymeetsappeals@gmail.com"),
            Choice(name="No", value="This ban is permanent and can not be appealed.")
        ]
    )
    @adefs.check_admin_roles()
    async def banc(self, interaction: discord.Interaction, type: Choice[str], member: discord.User = None,
                  memberid: str = None, *, reason: str = "You have been banned by an admin",
                  appeal: Choice[str]) -> None:
        await interaction.response.defer(ephemeral=True)
        bot = self.bot
        if member is not None:
            await ModUser.ban(self, interaction, member, bot, reason, type, appeal)
        elif memberid is not None:
            member = await self.bot.fetch_user(int(memberid))
            await ModUser.ban(self, interaction, member, bot, reason, type, appeal)
        elif memberid and member is not None:
            try:
                await ModUser.ban(self, interaction, member, bot, bot, reason, type, appeal)
            except:
                member = await self.bot.fetch_user(int(memberid))
                await ModUser.ban(self, interaction, member, bot, reason, type, appeal)

    @app_commands.command(name="kick")
    @adefs.check_slash_db_roles()
    async def kick(self, interaction: discord.Interaction, user: discord.Member, *, reason: str = None):
        await interaction.response.send_message(f"Kicking {user}", ephemeral=True)
        try:
            await user.send(
                f"you've been kicked from {interaction.guild.name} for {reason} \n \n You may rejoin once your behavior improves.")
        except:
            await interaction.channel.send("Error: user could not be dmed.")
        await user.kick(reason=reason)
        await ModUser.kicklog(interaction, user, reason, interaction.guild)

    @app_commands.command(name="warn")
    @app_commands.choices(notify=[
        Choice(name="Yes", value="yes"),
        Choice(name="No", value="no")
    ])
    @adefs.check_slash_db_roles()
    async def warn(self, interaction: discord.Interaction, user: discord.Member, notify: Choice['str'], *, reason: str):
        await interaction.response.defer(ephemeral=True)
        if notify.value == "yes":
            await user.send(f"{interaction.guild.name} **__WARNING__**: You've been warned for: {reason} ")
        await jsonmaker.Configer.addwarning(self, user, interaction, reason)
        await ModUser.warnlog(interaction, user, reason, interaction.guild)
        if notify.value == "yes":
            await interaction.followup.send(f"{user.mention} has been warned about {reason}")
        else:
            await interaction.followup.send(f"{user.mention}'s warning has been logged with reason: {reason}")

    @app_commands.command(name="notify")
    @adefs.check_slash_db_roles()
    async def notify(self, interaction: discord.Interaction, user: discord.Member, *, reason: str):
        await interaction.response.defer()
        await user.send(f"{interaction.guild.name} **__Notification__**: {reason} ")
        await interaction.followup.send(f"{user.mention} has been notified about {reason}")

    @app_commands.command(name="warnings")
    @adefs.check_slash_db_roles()
    async def warns(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer()
        bot = self.bot
        exists = session.query(db.warnings).filter_by(uid=user.id).first()
        embed = discord.Embed(title=f"{user}'s warnings", description=f"""User ID: {user.id}
\nSearch warning count: {exists.swarnings}""")
        await interaction.channel.send(embed=embed)
        await jsonmaker.Configer.getwarnings(self, user, interaction)
        await interaction.followup.send("Success! ~~The bot is still thinking about world domination~~")

    @app_commands.command(name="searchban", description="ADMIN adcommand: search bans the users")
    @app_commands.choices(time=[
        Choice(name="one week", value="for **1 Week**"),
        Choice(name="two weeks", value="for **2 Weeks**"),
        Choice(name="1 month", value="for **1 Month**"),
        Choice(name="permanent", value="**permanently**"),
        Choice(name="custom", value=f"custom"),
    ])
    @adefs.check_slash_admin_roles()
    async def searchban(self, interaction: discord.Interaction, member: discord.Member, time: Choice[str],
                        custom: str = None) -> None:
        await interaction.response.defer(ephemeral=True)
        tz = pytz.timezone("US/Eastern")
        bot = self.bot
        searchbanrole = discord.utils.get(interaction.guild.roles, id=538809717808693248)
        await member.add_roles(searchbanrole)
        current = datetime.now(tz)
        cooldown = None
        if time.name == "one week":
            cooldown = current + timedelta(weeks=1)
        elif time.name == "two weeks":
            cooldown = current + timedelta(weeks=2)
        elif time.name == "1 month":
            cooldown = current + timedelta(days=30)
        else:
            pass
        reason = f"{interaction.guild.name} **__SEARCH BAN__**: Hello, I'm a staff member from RMR. Due to your frequent refusal to follow our search rules concerning ads, your ad posting privileges have been revoked and you've been given a search ban {time.value}. Please use this time to thoroughly review RMR's rules. Continued refusal to follow the server's search rules can result in a permanent search ban. This search ban expires on {cooldown.strftime('%m/%d/%Y %I:%M:%S %p')} EST."
        customr = f"{interaction.guild.name} **__SEARCH BAN__**: Hello, I'm a staff member from RMR. Due to your frequent refusal to follow our search rules concerning ads, your ad posting privileges have been revoked and you've been given a search ban for {custom}. Please use this time to thoroughly review RMR's rules. Continued refusal to follow the server's search rules can result in a permanent search ban."
        if time.value == "custom":
            await member.send(customr)
            await jsonmaker.Configer.addwarning(self, member, interaction, customr)
            await ModUser.searchban(interaction, member, customr, interaction.guild, custom)
            await interaction.followup.send(
                f"{member.mention} has been search banned for {custom}\n(Note: the bot currently does not auto remove the role.)")
        else:
            await member.send(reason)
            await jsonmaker.Configer.addwarning(self, member, interaction, reason)
            await ModUser.searchban(interaction, member, customr, interaction.guild, time.value)
            await interaction.followup.send(
                f"{member.mention} has been search banned {time.value} ({cooldown.strftime('%m/%d/%Y %I:%M:%S %p')})\n(Note: the bot currently does not auto remove the role.)")


async def setup(bot: commands.Bot):
    await bot.add_cog(moderation(bot))
