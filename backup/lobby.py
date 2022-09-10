import discord
from discord.ext import commands
from abc import ABC, abstractmethod
import db
import adefs
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, column




Session = sessionmaker(bind=db.engine)
session = Session()

class agecalc(ABC):
    @abstractmethod
    def agechecker(self, arg1, arg2):
        from datetime import datetime, timedelta
        age = arg1
        print(age)
        dob = str(arg2)
        print(dob)
        dob_object = datetime.strptime(dob, "%m/%d/%Y")
        today = datetime.now()
        leapyear = ((today - dob_object) / 365.25) / 4
        deltad = leapyear - timedelta(days=1)
        agechecker = ((today - dob_object) - deltad) / 365
        age_output = str(agechecker).split()[0]
        age_calculate = int(age_output) - int(age)
        print(age_calculate)
        return age_calculate

class dblookup(ABC):

    @abstractmethod
    def dobsave(self, userid: discord.Member, dob):
        exists = session.query(db.user).filter_by(uid=userid.id).first()
        if exists is not None:
            pass
        else:
            tr = db.user(userid.id, dob)
            session.add(tr)
            session.commit()

    def dobcheck(self, userid: discord.Member, dob):
        exists = session.query(db.user).filter_by(uid=userid.id).first()
        if exists.dob == dob:
            return True
        else:
            return False

class lobby(commands.Cog, name="Lobby"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    @adefs.check_db_roles()
    async def permtest(self, ctx):
        await ctx.send("works")

    @commands.command(aliases=['agelookup'])
    @adefs.check_db_roles()
    async def dblookup(self, ctx, userid: discord.Member):
        exists = session.query(db.user).filter_by(uid=userid.id).first()
        print(exists.uid)
        if exists is None:
            await ctx.send(f"{userid.mention} has not been found")
        else:
            await ctx.send(f"""__**DB LOOKUP**__
user: <@{exists.uid}>
UID: {exists.uid}
DOB: {exists.dob}""")
    @commands.command()
    @commands.has_any_role('Moderator', 'Trial Moderator', 'Administrator')
    @adefs.check_db_roles()
    async def dbremove(self, ctx, userid: discord.Member):
        exists = session.query(db.user).filter_by(uid=userid.id).first()
        session.delete(exists)
        session.commit()




    @commands.command(name="18a", usage="@user age mm/dd/yyyy", )
    @adefs.check_db_roles()
    async def _18a(self, ctx, user: discord.Member, arg1, arg2):
        """Command to let users through the lobby, checks ages and logs them."""
        c = session.query(db.config).filter_by(guild=ctx.guild.id).first()
        lobbyid = c.lobby
        agelog = c.agelog
        modlobby = c.modlobby
        general = c.general
        bot  = self.bot
        await ctx.message.delete()
        if agecalc.agechecker(self, arg1, arg2) == 0:
            dblookup.dobsave(self, user, arg2)
            if dblookup.dobcheck(self, user, arg2) is True:
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
                    await general.send(
                        "Welcome to Roleplay Meets: Reborn, {}! To get started, check out <#647867587207757864> and introduce yourself in <#973367490581262376>! If you have any questions feel free to ask in <#977720278396305418>. we hope you have a wonderful time!".format(
                            user.mention))
                except:
                    await ctx.send("Channel **general** not set. Use ?config general #channel to fix this.")
                # this deletes user info
                messages = ctx.channel.history(limit=100)
                count = 0
                async for message in messages:
                    if message.author == user or user in message.mentions and count < 10:
                        count += 1
                        await message.delete()
            else:
                waiting = discord.utils.get(ctx.guild.roles, name="Waiting in Lobby")
                await user.add_roles(waiting)
                try:
                    channel = bot.get_channel(c.modlobby)
                    await channel.send(
                        f'<@&407496040690876416> User {user.mention}\'s dob does not match a previously given dob and has been given Waiting in Lobby. \n \n To check previously given ages or edit them use: ?agelookup or ?agefix')
                except:
                    await ctx.send("Channel **modlobby** not set. Use ?config modlobby #channel to fix this.")
        else:
            waiting = discord.utils.get(ctx.guild.roles, name="Waiting in Lobby")
            await user.add_roles(waiting)
            try:
                channel = bot.get_channel(c.modlobby)
                await channel.send(
                    '<@&407496040690876416> User {}\'s age does not match and has been timed out.'.format(user.mention))
            except:
                await ctx.send("Channel **modlobby** not set. Use ?config modlobby #channel to fix this.")
            await ctx.message.delete()



    @commands.command(name="21a")
    @adefs.check_db_roles()
    async def _21a(self, ctx, user: discord.Member, arg1, arg2, ):
        """Command to let users through the lobby, checks ages and logs them."""
        c = session.query(db.config).filter_by(guild=ctx.guild.id).first()
        lobbyid = c.lobby
        agelog = c.agelog
        modlobby = c.modlobby
        general = c.general
        print(general)
        bot = self.bot
        await ctx.message.delete()
        if agecalc.agechecker(self, arg1, arg2) == 0:
            dblookup.dobsave(self, user, arg2)
            if dblookup.dobcheck(self, user, arg2) is True:
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
                    await general.send(
                        "Welcome to Roleplay Meets: Reborn, {}! To get started, check out <#647867587207757864> and introduce yourself in <#973367490581262376>! If you have any questions feel free to ask in <#977720278396305418>. we hope you have a wonderful time!".format(
                            user.mention))
                except:
                    await ctx.send("Channel **general** not set. Use ?config general #channel to fix this.")

                # this deletes user info
                messages = ctx.channel.history(limit=100)
                count = 0
                async for message in messages:
                    if message.author == user or user in message.mentions and count < 10:
                        count += 1
                        await message.delete()
            else:
                waiting = discord.utils.get(ctx.guild.roles, name="Waiting in Lobby")
                await user.add_roles(waiting)
                try:
                    channel = bot.get_channel(c.modlobby)
                    await channel.send(
                        f'<@&407496040690876416> User {user.mention}\'s dob does not match a previously given dob and has been given Waiting in Lobby. \n \n To check previously given ages or edit them use: ?agelookup or ?agefix')
                except:
                    await ctx.send("Channel **modlobby** not set. Use ?config modlobby #channel to fix this.")

        else:
            waiting = discord.utils.get(ctx.guild.roles, name="Waiting in Lobby")
            await user.add_roles(waiting)
            try:
                channel = bot.get_channel(c.modlobby)
                await channel.send(
                    '<@&407496040690876416> User {}\'s age does not match and has been timed out.'.format(user.mention))
            except:
                await ctx.send("Channel **modlobby** not set. Use ?config modlobby #channel to fix this.")
            await ctx.message.delete()


    @commands.command(name="25a")
    @adefs.check_db_roles()
    async def _25a(self, ctx, user: discord.Member, arg1, arg2, ):
        """Command to let users through the lobby, checks ages and logs them."""
        c = session.query(db.config).filter_by(guild=ctx.guild.id).first()
        lobbyid = c.lobby
        agelog = c.agelog
        modlobby = c.modlobby
        general = c.general
        bot = self.bot
        await ctx.message.delete()
        if agecalc.agechecker(self, arg1, arg2) == 0:
            dblookup.dobsave(self, user, arg2)
            if dblookup.dobcheck(self, user, arg2) is True:
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
                    general = bot.get_channel(general)
                    await general.send(
                        "Welcome to Roleplay Meets: Reborn, {}! To get started, check out <#647867587207757864> and introduce yourself in <#973367490581262376>! If you have any questions feel free to ask in <#977720278396305418>. we hope you have a wonderful time!".format(
                            user.mention))
                except:
                    await ctx.send("Channel **general** not set. Use ?config general #channel to fix this.")
                # this deletes user info
                messages = ctx.channel.history(limit=100)
                count = 0
                async for message in messages:
                    if message.author == user or user in message.mentions and count < 10:
                        count += 1
                        await message.delete()
            else:
                waiting = discord.utils.get(ctx.guild.roles, name="Waiting in Lobby")
                await user.add_roles(waiting)
                channel = bot.get_channel(925193288997298226)
                try:
                    channel = bot.get_channel(c.modlobby)
                    await channel.send(
                        f'<@&407496040690876416> User {user.mention}\'s dob does not match a previously given dob and has been given Waiting in Lobby. \n \n To check previously given ages or edit them use: ?agelookup or ?agefix')
                except:
                    await ctx.send("Channel **modlobby** not set. Use ?config modlobby #channel to fix this.")

        else:
            waiting = discord.utils.get(ctx.guild.roles, name="Waiting in Lobby")
            await user.add_roles(waiting)
            try:
                channel = bot.get_channel(c.modlobby)
                await channel.send(
                    '<@&407496040690876416> User {}\'s age does not match and has been timed out.'.format(user.mention))
            except:
                await ctx.send("Channel **modlobby** not set. Use ?config modlobby #channel to fix this.")
            await ctx.message.delete()

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
    @commands.has_any_role('Moderator', 'Trial Moderator', 'Administrator')
    async def test(self, ctx, user: discord.Member):
        """Command sends users back to the lobby and removes roles"""
        await ctx.message.delete()
        bot = self.bot
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
        output2 = await user.remove_roles(newuser, waiting, RL)
        output = await user.add_roles(agerole18, agerole21, agerole25, rulesaccepted, dma,dmo,dmc,NSFW,searching,nsearching)

        await ctx.send(f"{user.mention} has been given test roles by {ctx.message.author.mention}")
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
    @adefs.check_db_roles()
    async def agefix(self, ctx: commands.Context, user: discord.Member, age, dob):
        c = session.query(db.config).filter_by(guild=ctx.guild.id).first()
        agelog = c.agelog
        channel = self.bot.get_channel(agelog)
        await ctx.message.delete()
        userdata = session.query(db.user).filter_by(uid=user.id).first()
        userdata.dob = dob
        session.commit()
        await channel.send(f"""user: {user.mention}
Age: {age}
DOB: {dob}
User info:  UID: {user.id} 

Entry uppdated by: {ctx.author}""")


async def setup(bot: commands.Bot):
    await bot.add_cog(lobby(bot))

session.commit()