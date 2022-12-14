import logging
import traceback

from discord import app_commands
import discord
from discord.ext import commands
from abc import ABC, abstractmethod
import db
import adefs
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, column
from datetime import datetime, timedelta
import re
import typing
import logging

Session = sessionmaker(bind=db.engine)
session = Session()

class agecalc(ABC):
    @abstractmethod
    def agechecker(self, arg1, arg2):
        age = arg1
        dob = str(arg2)
        dob_object = datetime.strptime(dob, "%m/%d/%Y")
        today = datetime.now()
        leapyear = ((today - dob_object) / 365.25) / 4
        deltad = leapyear - timedelta(days=1)
        agechecker = ((today - dob_object) - deltad) / 365
        age_output = str(agechecker).split()[0]
        age_calculate = int(age_output) - int(age)
        print(age_calculate)
        return age_calculate
    def regex(arg2):
        dob = str(arg2)
        dob_object = re.search(r"([0-1]?[0-9])\/([0-3]?[0-9])\/([0-2][0-9][0-9][0-9])", dob)
        month = dob_object.group(1).zfill(2)
        day = dob_object.group(2).zfill(2)
        year = dob_object.group(3)
        fulldob = f"{month}/{day}/{year}"
        return fulldob
    def agecheckfail(arg1):
        bot = commands.Bot
        from datetime import datetime, timedelta
        dob = str(arg1)
        dob_object = datetime.strptime(dob, "%m/%d/%Y")
        today = datetime.now()
        leapyear = ((today - dob_object) / 365.25) / 4
        deltad = leapyear - timedelta(days=1)
        agechecker = ((today - dob_object) - deltad) / 365
        print(agechecker)
        age_output = str(agechecker).split()[0]
        return age_output
    async def removemessage(ctx, bot, user):
        c = session.query(db.config).filter_by(guild=ctx.guild.id).first()
        print(c.lobby)
        channel = bot.get_channel(c.lobby)
        messages = channel.history(limit=100)
        count = 0
        async for message in messages:
            if message.author == user or user in message.mentions and count < 10:
                count += 1
                print(message.id)
                await message.delete()

class dblookup(ABC):

    @abstractmethod
    def dobsave(self, userid: discord.Member, dob):
        exists = session.query(db.user).filter_by(uid=userid.id).first()
        if exists is not None:
            pass
        else:
            try:
                tr = db.user(userid.id, dob)
                session.add(tr)
                session.commit()
            except:
                logging.exception("Database error, rolled back")
                session.rollback()
                session.close()
    @abstractmethod
    async def dobsaveid(self, userid: int, dob):
        exists = session.query(db.user).filter_by(uid=userid).first()
        if exists is not None:
            pass
        else:
            try:
                tr = db.user(userid, dob)
                session.add(tr)
                session.commit()
            except:
                print("Database error, rolled back")
                session.rollback()
                session.close()
    @abstractmethod
    def dobcheck(self, userid: discord.Member, dob):
        exists = session.query(db.user).filter_by(uid=userid.id).first()
        if exists.dob == dob:
            return True
        else:
            return False
    @abstractmethod
    def idcheckchecker(self, userid: discord.Member):
        exists = session.query(db.idcheck).filter_by(uid=userid.id).first()
        print(exists.uid)
        print(exists.check)
        if exists is not None:
            if exists.check == True:
                return True
            else:
                return False
        else:
            return False
    @abstractmethod
    def idcheckeradd(self, userid:int):
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
    @abstractmethod
    def idcheckerremove(self, userid:int):
        idchecker = session.query(db.idcheck).filter_by(uid=userid).first()
        if idchecker is not None:
            idchecker.check = False
            session.commit()
        else:
            try:
                idcheck = db.idcheck(userid, False)
                session.add(idcheck)
                session.commit()
            except:
                session.rollback()
                session.close()
                logging.exception("failed to  log to database")


class lobby(commands.GroupCog, name="lobby"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(aliases=['agelookup', 'lookup', 'alu'])
    @adefs.check_db_roles()
    async def dblookup(self, ctx, userid: discord.Member):
        try:
            exists = session.query(db.user).filter_by(uid=userid.id).first()
        except:
            await ctx.send(f"{userid.mention} has not been found")
        if exists is None:
            await ctx.send(f"{userid.mention} has not been found")
        else:
            await ctx.send(f"""__**DB LOOKUP**__
user: <@{exists.uid}>
UID: {exists.uid}
DOB: {exists.dob}""")
    @commands.command()
    @adefs.check_admin_roles()
    async def dbremove(self, ctx, userid: discord.Member):
        try:
            exists = session.query(db.user).filter_by(uid=userid.id).first()
            session.delete(exists)
            session.commit()
            await ctx.send("Removal complete")
        except:
            await ctx.send("Removal failed")
    @commands.command()
    @adefs.check_admin_roles()
    async def dbremoveid(self, ctx, userid: int):
        try:
            exists = session.query(db.user).filter_by(uid=userid).first()
            session.delete(exists)
            session.commit()
            await ctx.send("Removal complete")
        except:
            await ctx.send("Removal failed")


    @commands.command()
    @adefs.check_db_roles()
    async def test(self, ctx, user: discord.Member, arg1, arg2):
        await ctx.message.delete()
        await ctx.send(agecalc.regex(arg2))

    @commands.command(name="18a", usage="@user age mm/dd/yyyy", )
    @adefs.check_db_roles()
    async def _18a(self, ctx, user: discord.Member, arg1, arg2):
        """Command to let users through the lobby, checks ages and logs them."""
        c = session.query(db.config).filter_by(guild=ctx.guild.id).first()
        a = session.query(db.permissions).filter_by(guild=ctx.guild.id).first()
        lobbyid = c.lobby
        agelog = c.agelog
        modlobby = c.modlobby
        general = c.general
        regdob = agecalc.regex(arg2)
        bot = self.bot
        await ctx.message.delete()
        if dblookup.idcheckchecker(self, user) is True:
            await ctx.send(f"<@{a.admin}> user {user.mention} was flagged for manual ID check.")
        else:
            if agecalc.agechecker(self, arg1, regdob) == 0:
                dblookup.dobsave(self, user, regdob)
                print(dblookup.dobcheck(self, user, regdob))
                if dblookup.dobcheck(self, user, regdob) is True:
                    # Role adding
                    # await ctx.send('This user\'s age is correct')
                    agerole = discord.utils.get(ctx.guild.roles, name="18+")
                    rulesaccepted = discord.utils.get(ctx.guild.roles, name="Rules Accepted")
                    newuser = discord.utils.get(ctx.guild.roles, name="New User")
                    waiting = discord.utils.get(ctx.guild.roles, name="Waiting in Lobby")
                    rl = discord.utils.get(ctx.guild.roles, name="Rules Lobby")
                    await user.add_roles(agerole, rulesaccepted)
                    await user.remove_roles(newuser, waiting, rl)
                    # output for lobby ages
                    from datetime import datetime
                    username = user.mention
                    userid = user.id
                    userjoin = user.joined_at
                    userjoinformatted = userjoin.strftime('%m/%d/%Y %I:%M:%S %p')
                    executed = datetime.now().strftime('%m/%d/%Y %I:%M:%S %p')
                    print(userjoinformatted)
                    staff = ctx.author
                    try:
                        log = bot.get_channel(c.agelog)
                        await log.send(
                            f"user: {username}\n Age: {arg1} \n DOB: {arg2} \n User info:  UID: {userid} \n joined at: {userjoinformatted} \n \n executed: {executed} \n staff: {staff}")
                    except:
                        await ctx.send("Channel **agelobby** not set. Use ?config agelobby #channel to fix this.")

                    # welcomes them in general chat.
                    try:
                        general = bot.get_channel(general)
                        exists = session.query(db.config).filter_by(guild=ctx.guild.id).first()
                        if exists.guild == 395614061393477632:
                            await general.send(
                                f"Welcome to {ctx.guild.name}, {user.mention}! To get started, check out <#647867587207757864> and introduce yourself in <#973367490581262376>! If you have any questions feel free to ask in <#977720278396305418>. we hope you have a wonderful time!")
                        elif exists.guild == 780622396297183252:
                            await general.send(
                                f"Welcome to {ctx.guild.name}, {user.mention}! To get started, check out <#780622397816569891> and read our <#788116431224569957>! If you have any questions feel free to ask in <#780622397816569888>. we hope you have a wonderful time!")
                        else:
                            await general.send(
                                f"Welcome to {ctx.guild.name}, {user.mention}! If you have any questions feel free to ask a staff member. We hope you have a wonderful time!")
                    except:
                        await ctx.send("Channel **general** not set. Use ?config general #channel to fix this.")
                    # this deletes user info
                    await agecalc.removemessage(ctx, bot, user)
                else:
                    waiting = discord.utils.get(ctx.guild.roles, name="Waiting in Lobby")
                    await user.add_roles(waiting)
                    channel = bot.get_channel(925193288997298226)
                    try:
                        channel = bot.get_channel(c.modlobby)
                        u = session.query(db.user).filter_by(uid=user.id).first()

                        await channel.send(
                            f'<@&{a.admin}> User {user.mention}\'s dob ({regdob}) does not match a previously given dob ({u.dob}) and has been given Waiting in Lobby. \n \n To check previously given ages or edit them use: ?agelookup or ?agefix')
                    except:
                        await ctx.send("Channel **modlobby** not set. Use ?config modlobby #channel to fix this.")

            else:
                waiting = discord.utils.get(ctx.guild.roles, name="Waiting in Lobby")
                await user.add_roles(waiting)
                print(agecalc.agecheckfail(arg2))
                try:
                    channel = bot.get_channel(c.modlobby)
                    await channel.send(
                         f'<@&{a.admin}> User {user.mention}\'s age does not match and has been timed out. User gave {arg1} but dob indicates {agecalc.agecheckfail(arg2)}')
                except:
                    await ctx.send("Channel **modlobby** not set. Use ?config modlobby #channel to fix this.")

    @commands.command(name="21a")
    @adefs.check_db_roles()
    async def _21a(self, ctx, user: discord.Member, arg1, arg2, ):
        """Command to let users through the lobby, checks ages and logs them."""
        c = session.query(db.config).filter_by(guild=ctx.guild.id).first()
        a = session.query(db.permissions).filter_by(guild=ctx.guild.id).first()
        lobbyid = c.lobby
        agelog = c.agelog
        modlobby = c.modlobby
        general = c.general
        regdob = agecalc.regex(arg2)
        bot = self.bot
        await ctx.message.delete()
        if dblookup.idcheckchecker(self, user) is True:
            await ctx.send(f"<@{a.admin}> user {user.mention} was flagged for manual ID check.")
        else:
            if agecalc.agechecker(self, arg1, regdob) == 0:
                dblookup.dobsave(self, user, regdob)
                print(dblookup.dobcheck(self, user, regdob))
                if dblookup.dobcheck(self, user, regdob) is True:
                    # Role adding
                    # await ctx.send('This user\'s age is correct')
                    agerole = discord.utils.get(ctx.guild.roles, name="21+")
                    rulesaccepted = discord.utils.get(ctx.guild.roles, name="Rules Accepted")
                    newuser = discord.utils.get(ctx.guild.roles, name="New User")
                    waiting = discord.utils.get(ctx.guild.roles, name="Waiting in Lobby")
                    RL = discord.utils.get(ctx.guild.roles, name="Rules Lobby")
                    await user.add_roles(agerole, rulesaccepted)
                    await user.remove_roles(newuser, waiting, RL)
                    # output for lobby ages
                    from datetime import datetime
                    username = user.mention
                    userid = user.id
                    userjoin = user.joined_at
                    userjoinformatted = userjoin.strftime('%m/%d/%Y %I:%M:%S %p')
                    executed = datetime.now().strftime('%m/%d/%Y %I:%M:%S %p')
                    print(userjoinformatted)
                    staff = ctx.author
                    try:
                        log = bot.get_channel(c.agelog)
                        await log.send(
                            f"user: {username}\n Age: {arg1} \n DOB: {arg2} \n User info:  UID: {userid} \n joined at: {userjoinformatted} \n \n executed: {executed} \n staff: {staff}")
                    except:
                        await ctx.send("Channel **agelobby** not set. Use ?config agelobby #channel to fix this.")

                    # welcomes them in general chat.
                    try:
                        general = bot.get_channel(general)
                        exists = session.query(db.config).filter_by(guild=ctx.guild.id).first()
                        if exists.guild == 395614061393477632:
                            await general.send(
                                f"Welcome to {ctx.guild.name}, {user.mention}! To get started, check out <#647867587207757864> and introduce yourself in <#973367490581262376>! If you have any questions feel free to ask in <#977720278396305418>. we hope you have a wonderful time!")
                        elif exists.guild == 780622396297183252:
                            await general.send(
                                f"Welcome to {ctx.guild.name}, {user.mention}! To get started, check out <#780622397816569891> and read our <#788116431224569957>! If you have any questions feel free to ask in <#780622397816569888>. we hope you have a wonderful time!")
                        else:
                            await general.send(
                                f"Welcome to {ctx.guild.name}, {user.mention}! If you have any questions feel free to ask a staff member. We hope you have a wonderful time!")
                    except:
                        await ctx.send("Channel **general** not set. Use ?config general #channel to fix this.")

                    # this deletes user info
                    await agecalc.removemessage(ctx, bot, user)
                else:
                    waiting = discord.utils.get(ctx.guild.roles, name="Waiting in Lobby")
                    await user.add_roles(waiting)
                    channel = bot.get_channel(925193288997298226)
                    try:
                        channel = bot.get_channel(c.modlobby)
                        u = session.query(db.user).filter_by(uid=user.id).first()

                        await channel.send(
                            f'<@&{a.admin}> User {user.mention}\'s dob ({regdob}) does not match a previously given dob ({u.dob}) and has been given Waiting in Lobby. \n \n To check previously given ages or edit them use: ?agelookup or ?agefix')
                    except:
                        await ctx.send("Channel **modlobby** not set. Use ?config modlobby #channel to fix this.")

            else:
                waiting = discord.utils.get(ctx.guild.roles, name="Waiting in Lobby")
                await user.add_roles(waiting)
                print(agecalc.agecheckfail(arg2))
                try:
                    channel = bot.get_channel(c.modlobby)
                    await channel.send(
                         f'<@&{a.admin}> User {user.mention}\'s age does not match and has been timed out. User gave {arg1} but dob indicates {agecalc.agecheckfail(arg2)}')
                except:
                    await ctx.send("Channel **modlobby** not set. Use ?config modlobby #channel to fix this.")



    @commands.command(name="25a")
    @adefs.check_db_roles()
    async def _25a(self, ctx, user: discord.Member, arg1, arg2):
        """Command to let users through the lobby, checks ages and logs them."""
        c = session.query(db.config).filter_by(guild=ctx.guild.id).first()
        a = session.query(db.permissions).filter_by(guild=ctx.guild.id).first()
        lobbyid = c.lobby
        agelog = c.agelog
        modlobby = c.modlobby
        general = c.general
        regdob = agecalc.regex(arg2)
        print(regdob)
        bot = self.bot
        await ctx.message.delete()
        if dblookup.idcheckchecker(self, user) is True:
            await ctx.send(f"<@{a.admin}> user {user.mention} was flagged for manual ID check.")
        else:
            if agecalc.agechecker(self, arg1, regdob) == 0:
                dblookup.dobsave(self, user, regdob)
                print(dblookup.dobcheck(self, user, regdob))
                if dblookup.dobcheck(self, user, regdob) is True:
                    # Role adding
                    # await ctx.send('This user\'s age is correct')
                    agerole = discord.utils.get(ctx.guild.roles, name="25+")
                    rulesaccepted = discord.utils.get(ctx.guild.roles, name="Rules Accepted")
                    newuser = discord.utils.get(ctx.guild.roles, name="New User")
                    waiting = discord.utils.get(ctx.guild.roles, name="Waiting in Lobby")
                    RL = discord.utils.get(ctx.guild.roles, name="Rules Lobby")
                    await user.add_roles(agerole, rulesaccepted)
                    await user.remove_roles(newuser, waiting, RL)
                    # output for lobby ages
                    from datetime import datetime
                    username = user.mention
                    userid = user.id
                    userjoin = user.joined_at
                    userjoinformatted = userjoin.strftime('%m/%d/%Y %I:%M:%S %p')
                    executed = datetime.now().strftime('%m/%d/%Y %I:%M:%S %p')
                    print(userjoinformatted)
                    staff = ctx.author
                    try:
                        log = bot.get_channel(c.agelog)
                        await log.send(
                            f"user: {username}\n Age: {arg1} \n DOB: {arg2} \n User info:  UID: {userid} \n joined at: {userjoinformatted} \n \n executed: {executed} \n staff: {staff}")
                    except:
                        await ctx.send("Channel **agelobby** not set. Use ?config agelobby #channel to fix this.")

                    # welcomes them in general chat.
                    try:
                        general = bot.get_channel(c.general)
                        exists = session.query(db.config).filter_by(guild=ctx.guild.id).first()
                        if exists.guild == 395614061393477632:
                            await general.send(
                                f"Welcome to {ctx.guild.name}, {user.mention}! To get started, check out <#647867587207757864> and introduce yourself in <#973367490581262376>! If you have any questions feel free to ask in <#977720278396305418>. We hope you have a wonderful time!")
                        elif exists.guild == 780622396297183252:
                            await general.send(
                                f"Welcome to {ctx.guild.name}, {user.mention}! To get started, check out <#780622397816569891> and read our <#788116431224569957>! If you have any questions feel free to ask in <#780622397816569888>. We hope you have a wonderful time!")
                        else:
                            await general.send(
                                f"Welcome to {ctx.guild.name}, {user.mention}! If you have any questions feel free to ask a staff member. We hope you have a wonderful time!")

                    except:
                        await ctx.send("Channel **general** not set. Use ?config general #channel to fix this.")
                    # this deletes user info
                    await agecalc.removemessage(ctx, bot, user)
                else:
                    waiting = discord.utils.get(ctx.guild.roles, name="Waiting in Lobby")
                    await user.add_roles(waiting)
                    channel = bot.get_channel(925193288997298226)
                    try:
                        channel = bot.get_channel(c.modlobby)
                        u = session.query(db.user).filter_by(uid=user.id).first()

                        await channel.send(
                            f'<@&{a.admin}> User {user.mention}\'s dob ({regdob}) does not match a previously given dob ({u.dob}) and has been given Waiting in Lobby. \n \n To check previously given ages or edit them use: ?agelookup or ?agefix')
                    except:
                        await ctx.send("Channel **modlobby** not set. Use ?config modlobby #channel to fix this.")

            else:
                waiting = discord.utils.get(ctx.guild.roles, name="Waiting in Lobby")
                await user.add_roles(waiting)
                print(agecalc.agecheckfail(arg2))
                try:
                    channel = bot.get_channel(c.modlobby)
                    await channel.send(
                         f'<@&{a.admin}> User {user.mention}\'s age does not match and has been timed out. User gave {arg1} but dob indicates {agecalc.agecheckfail(arg2)}')
                except:
                    await ctx.send("Channel **modlobby** not set. Use ?config modlobby #channel to fix this.")

    @commands.command(name="returnlobby", aliases=['Returnlobby', 'return'])
    @adefs.check_db_roles()
    async def returnlobby(self, ctx, user: discord.Member):
        """Command sends users back to the lobby and removes roles"""
        bot = self.bot
        await ctx.message.delete()
        from datetime import datetime, timedelta
        agerole18 = discord.utils.get(ctx.guild.roles, name="18+")
        agerole21 = discord.utils.get(ctx.guild.roles, name="21+")
        agerole25 = discord.utils.get(ctx.guild.roles, name="25+")
        rulesaccepted = discord.utils.get(ctx.guild.roles, name="Rules Accepted")
        newuser = discord.utils.get(ctx.guild.roles, name="New User")
        waiting = discord.utils.get(ctx.guild.roles, name="Waiting in Lobby")
        RL = discord.utils.get(ctx.guild.roles, name="Rules Lobby")
        dmo = discord.utils.get(ctx.guild.roles, name="Open DMs")
        dmc = discord.utils.get(ctx.guild.roles, name="Closed DMs")
        dma = discord.utils.get(ctx.guild.roles, name="Ask To DM")
        NSFW = discord.utils.get(ctx.guild.roles, name="NSFW")
        searching = discord.utils.get(ctx.guild.roles, name="Searching")
        nsearching = discord.utils.get(ctx.guild.roles, name="Not Searching")
        output2 = await user.add_roles(newuser, waiting, RL)
        output = await user.remove_roles(agerole18, agerole21, agerole25, rulesaccepted, dma,dmo,dmc,NSFW,searching,nsearching)
        await ctx.send(f"{user.mention} has been moved back to the lobby by {ctx.message.author.mention}")
        print(output)
        print(output2)

    @commands.command()
    @adefs.check_db_roles()
    async def agecheck(self, ctx, arg1, ):
        bot = self.bot
        from datetime import datetime, timedelta
        dob = str(arg1)
        dob_object = datetime.strptime(dob, "%m/%d/%Y")
        today = datetime.now()
        leapyear = ((today - dob_object) / 365.25) / 4
        deltad = leapyear - timedelta(days=1)
        agechecker = ((today - dob_object) - deltad) / 365
        print(agechecker)
        age_output = str(agechecker).split()[0]
        await ctx.send('this users age is: {}'.format(age_output) + " years.")

    @commands.command()
    @adefs.check_admin_roles()
    async def agefix(self, ctx: commands.Context, user: discord.Member, age, dob):
        "Updates the database entry for an user in the server"
        c = session.query(db.config).filter_by(guild=ctx.guild.id).first()
        agelog = c.agelog
        channel = self.bot.get_channel(agelog)
        regdob = agecalc.regex(dob)
        await ctx.message.delete()
        userdata = session.query(db.user).filter_by(uid=user.id).first()
        userdata.dob = regdob
        session.commit()
        await ctx.send(f"Entry for {user} updated to: {age} {regdob}")
        await channel.send(f"""**USER UPDATED**
user: {user.mention}
Age: {age}
DOB: {dob}
User info:  UID: {user.id} 

Entry uppdated by: {ctx.author}""")

    @commands.command()
    @adefs.check_admin_roles()
    async def agefixid(self, ctx: commands.Context, userid: str, age: str, dob: str):
        "Updates the database entry for an user in the server when user ISN'T in the server"
        c = session.query(db.config).filter_by(guild=ctx.guild.id).first()
        agelog = c.agelog
        channel = self.bot.get_channel(agelog)
        regdob = agecalc.regex(dob)
        await ctx.message.delete()
        userdata = session.query(db.user).filter_by(uid=userid).first()
        userdata.dob = regdob
        session.commit()
        await ctx.send(f"Entry for {userid} updated to: {age} {regdob}")
        await channel.send(f"""**USER UPDATED**
(User not in server)
Age: {age}
DOB: {dob}
User info:  UID: {userid} 

Entry updated by: {ctx.author}""")

    @app_commands.command(name="ageadd", description="Add ages to the database")
    @adefs.check_slash_db_roles()
    async def ageadd(self, interaction: discord.Interaction, user: str, age:str, dob: str):
        await interaction.response.defer()
        c = session.query(db.config).filter_by(guild=interaction.guild.id).first()
        agelog = c.agelog
        channel = self.bot.get_channel(agelog)
        regdob = agecalc.regex(dob)
        await dblookup.dobsaveid(self, int(user), regdob)
        await channel.send(f"""**USER ADDED**
Age: {age}
DOB: {dob}
UID: {user} 

Entry updated by: {interaction.user}""")
        await interaction.followup.send(f"User was added to the database")

    @app_commands.command(name="idverify", description="approves user for ID verification.")
    @adefs.check_slash_db_roles()
    async def idverify(self, interaction: discord.Interaction, user: discord.Member, age:str, dob: str):
        await interaction.response.defer(ephemeral=True)
        c = session.query(db.config).filter_by(guild=interaction.guild.id).first()
        agelog = c.agelog
        channel = self.bot.get_channel(agelog)
        regdob = agecalc.regex(dob)
        try:
            userdata = session.query(db.user).filter_by(uid=user.id).first()
            userdata.dob = regdob
            idchecker = session.query(db.idcheck).filter_by(uid=user.id).first()
            if idchecker is not None:
                idchecker.check = False
                session.commit()
            else:
                try:
                    idcheck = db.idcheck(user.id, False)
                    session.add(idcheck)
                    session.commit()
                except:
                    session.rollback()
                    session.close()
                    logging.exception("failed to  log to database")
            await channel.send(f"""**USER ID VERIFICATION**
user: {user.mention}
Age: {age}
DOB: {dob}
UID: {user.id} 
**ID VERIFIED BY:** {interaction.user}""")
            await interaction.followup.send(f"Entry for {user} updated to: {age} {regdob}")
        except:
            session.rollback()
            session.close()
            await interaction.followup.send(f"Command failed: {traceback.format_exc()}")
    #TODO: make this a command to add
    @app_commands.command(name="idadd", description="add a user to manual ID list")
    @adefs.check_slash_db_roles()
    async def addverify(self, interaction: discord.Interaction, userid: str):
        await interaction.response.defer(ephemeral=True)
        dblookup.idcheckeradd(self, userid)
        await interaction.followup.send(f"Added user {userid} to the ID list")

    #TODO: make this a command to add
    @app_commands.command(name="idremove", description="remove a user to manual ID list")
    @adefs.check_slash_db_roles()
    async def addverify(self, interaction: discord.Interaction, userid: str):
        await interaction.response.defer(ephemeral=True)
        dblookup.idcheckerremove(self, userid)
        await interaction.followup.send(f"Removed user {userid} to the ID list")



async def setup(bot: commands.Bot):
    await bot.add_cog(lobby(bot))

session.commit()