import logging
import jsonmaker
import discord
from discord import app_commands
from discord.ext import commands
from discord.app_commands import Choice
from datetime import datetime
import adefs
from abc import ABC, abstractmethod
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, column
import typing
from discord.app_commands import Choice
from datetime import datetime, timedelta
import pytz
import db

Session = sessionmaker(bind=db.engine)
session = Session()

class advert(ABC):

    @abstractmethod
    async def logadvert(ctx, msg, warning, lc):
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

    async def sendadvertuser(ctx, msg, warning):
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
            await ctx.followup.send("Can't DM user")
            pass

    async def increasewarnings(ctx, user):
        try:
            exists = session.query(db.warnings).filter_by(uid=user.id).first()
            if exists is not None:
                try:
                    exists.check += 1
                    session.commit()
                    return exists.check
                except:
                    session.rollback()
                    session.close()
                    logging.error("Couldn't access/add to database. (increase warnings)")
            else:
                try:
                    tr = db.warnings(member.id, 1)
                    session.add(tr)
                    session.commit()
                    exists = session.query(db.warnings).filter_by(uid=user.id).first()
<<<<<<< Updated upstream
                    return exists.check
                except:
                    session.rollback()
                    session.close()
                    logging.error("Couldn't access/add to database. (increase warnings)")
        except:
            await ctx.followup.send("Database is down, user has been warned but not logged. Try (admin) ?reload to fix the db.")
=======
                    return exists.swarnings
                except Exception as e:
                    print(e)
                    session.rollback()
                    session.close()
                    logging.error("Couldn't access/add to database. (increase warnings)")
        except Exception as e:
            await ctx.channel.send(f"{e}")
            await ctx.user.send("Database is down, user has been warned but not logged. Try (admin) ?reload to fix the db.")
>>>>>>> Stashed changes
            session.close()
    async def resetcooldown(self, message, timeincrement):
        tz = pytz.timezone('US/Eastern')
        now = datetime.now(tz)
        cd = now + timedelta(days=timeincrement)
        jsonmaker.Cooldown.add(self, message.author.id, message.channel.id, cd)
    @abstractmethod
    async def addreason(self, value):
        match value:
            case "age":
                warn = "Your advert failed to include character ages. We require both ages of your characters and your partner. It is recommended to add a general disclaimer."
            case "e72":
                warn = "You have posted too early in the channel, this channel has a 72 hour cooldown."
            case "e24":
                warn = "You have posted too early in the channel, this channel has a 24 hour cooldown."
            case "form":
                warn = "Your advert's format is incorrect. Potential causes: Double spacing, spacing between list items, more than 10 list items, using a font that is not Discord's default font."
            case "temp":
                warn = "Your advert did not follow the template."
            case "dup":
                warn = "Your advert was posted in other channels, we only allow unique adverts to be posted in multiple channels."
            case "pic":
                warn = "You have too many pictures within your advert. We allow up to 5 (FORUMS ONLY)."
            case default:
                pass
        return warn

class searchcommands(commands.GroupCog, name="ad"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    '''Search Commands'''
    @app_commands.command(name="ages", description="adcommand: use this when someone fails to include ages")
    @adefs.check_slash_db_roles()
    async def ages(self, interaction:discord.Interaction, message_link: str) -> None:
        await interaction.response.defer(ephemeral=True)
        link = message_link.split('/')
        try:
            print("channel")
            server = self.bot.get_guild(int(link[4]))
            channel = server.get_channel(int(link[5]))
            message_link = await channel.fetch_message(int(link[6]))
            await advert.resetcooldown(self, message_link, 0)
        except:
            print("thread")
            server = self.bot.get_guild(int(link[4]))
            thread = server.get_thread(int(link[5]))
            message_link = await thread.fetch_message(int(link[6]))
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        adchannel = bot.get_channel(763058339088957548)
        user = message_link.author
        print(user)
        #adds warning to database
        swarnings = await advert.increasewarnings(interaction, user)
        warning = """Hello, I'm a staff member of **Roleplay Meets Reborn**. The advert you have posted in {} has failed to mention the ages of the characters you intend to use in your roleplay, as required by our sixth search rule. This includes both the characters you intend to write and the characters you want your writing partner to write. Due to this, your advert has been removed. __**Please include the ages of all characters or a general disclaimer**__, such as: "all characters are 18+", in the future. Characters under the age of 18 are not allowed to be advertised within our server.

The ages must be displayed on the advertisement on discord.

If you have any more questions, our staff team is always available to help you.
<#977720278396305418>""".format(message_link.channel.mention)
        await adchannel.send(
            f"{interaction.user.mention} has warned {user.mention} for failing to include character ages to their adverts in {message_link.channel.mention}\n userId: {user.id} Warning Count: {swarnings}")
        #Logs the advert and sends it to the user.
        await advert.logadvert(interaction, message_link, warning, loggingchannel)
        await advert.sendadvertuser(interaction, message_link, warning)
        await interaction.followup.send(f"{message_link.author.mention} successfully warned")

#     @app_commands.command(name="toolong", description="adcommand: use this when an advert is over 600 characters")
#     @adefs.check_slash_db_roles()
#     async def toolong(self, interaction:discord.Interaction, message_link: str) -> None:
#         await interaction.response.defer(ephemeral=True)
#         link = message_link.split('/')
#         try:
#             print("channel")
#             server = self.bot.get_guild(int(link[4]))
#             channel = server.get_channel(int(link[5]))
#             msg = await channel.fetch_message(int(link[6]))
# 
#         except:
#             print("thread")
#             server = self.bot.get_guild(int(link[4]))
#             thread = server.get_thread(int(link[5]))
#             msg = await thread.fetch_message(int(link[6]))
#         bot = self.bot
#         loggingchannel = bot.get_channel(997282508523704350)
#         adchannel = bot.get_channel(763058339088957548)
#         user = msg.author
#         # adds warning to database
#         swarnings = await advert.increasewarnings(interaction, user)
#         warning = """Hello, I'm a staff member of **Roleplay Meets: Reborn**. I'm reaching out to you regarding your ad in {}. It's been removed because: **your advert was over 600 characters (your advert: {})**. Please repost it in the appropriate channel.
#
# If you have any questions regarding adverts or the rules, don't hesitate to ask. Thank you for your cooperation!
# <#977720278396305418>""".format(msg.channel.mention, len(msg.content))
#         await adchannel.send(
#             f"{interaction.user.mention} has warned {user.mention} for posting an advert that was too long  in {msg.channel.mention}\n userId: {user.id}\nCharacter Count: {len(msg.content)} Warning Count: {swarnings}")
#         # Logs the advert and sends it to the user.
#         await advert.logadvert(interaction, msg, warning, loggingchannel)
#         await advert.sendadvertuser(interaction, msg, warning)
#         await interaction.followup.send(f"{msg.author.mention} successfully warned")
#
#
#     @app_commands.command(name="tooshort", description="adcommand: use this when an advert is under 600 characters")
#     @adefs.check_slash_db_roles()
#     async def tooshort(self, interaction:discord.Interaction, message_link: str) -> None:
#         await interaction.response.defer(ephemeral=True)
#         link = message_link.split('/')
#         try:
#             print("channel")
#             server = self.bot.get_guild(int(link[4]))
#             channel = server.get_channel(int(link[5]))
#             msg = await channel.fetch_message(int(link[6]))
# 
#         except:
#             print("thread")
#             server = self.bot.get_guild(int(link[4]))
#             thread = server.get_thread(int(link[5]))
#             msg = await thread.fetch_message(int(link[6]))
#         bot = self.bot
#         loggingchannel = bot.get_channel(997282508523704350)
#         adchannel = bot.get_channel(763058339088957548)
#         user = msg.author
#         # adds warning to database
#         swarnings = await advert.increasewarnings(interaction, user)
#         warning = """Hello, I'm a staff member of **Roleplay Meets: Reborn**. I'm reaching out to you regarding your ad in {}. It's been removed because: **your advert was under 600 characters (your advert: {})**. Please repost it in the appropriate channel.
#
# If you have any questions regarding adverts or the rules, don't hesitate to ask. Thank you for your cooperation!
# <#977720278396305418>""".format(msg.channel.mention, len(msg.content))
#         await adchannel.send(
#             f"{interaction.user.mention} has warned {user.mention} for posting an advert that was too short in  {msg.channel.mention}\n userId: {user.id} Character Count: {len(msg.content)} Warning Count: {swarnings}")
#         # Logs the advert and sends it to the user.
#         await advert.logadvert(interaction, msg, warning, loggingchannel)
#         await advert.sendadvertuser(interaction, msg, warning)
#         await interaction.followup.send(f"{msg.author.mention} successfully warned")

    @app_commands.command(name="early24", description="adcommand: Use this when an advert was posted too early in quick search channels")
    @adefs.check_slash_db_roles()
    async def early24(self, interaction:discord.Interaction, message_link: str) -> None:
        await interaction.response.defer(ephemeral=True)
        link = message_link.split('/')
        try:
            print("channel")
            server = self.bot.get_guild(int(link[4]))
            channel = server.get_channel(int(link[5]))
            msg = await channel.fetch_message(int(link[6]))
        except:
            print("thread")
            server = self.bot.get_guild(int(link[4]))
            thread = server.get_thread(int(link[5]))
            msg = await thread.fetch_message(int(link[6]))
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        adchannel = bot.get_channel(763058339088957548)
        user = msg.author
        # adds warning to database
        swarnings = await advert.increasewarnings(interaction, user)
        warning = """Hello, I am a staff member of **Roleplay Meets: Reborn** . The advert you have posted within our {} has been posted too early, please wait 1 day(24 hours) between each posts.

Repeatedly posting too early may lead to a search ban which means you can not post an advert for a certain time.

If you have any questions regarding adverts or the rules, don't hesitate to ask in <#977720278396305418>. 
Thank you for your cooperation!""".format(msg.channel.mention)
        await adchannel.send(
            f"{interaction.user.mention} has warned {user.mention} for posting an advert that was too early (24h)  in {msg.channel.mention}\n userId: {user.id} Warning Count: {swarnings}")
        # Logs the advert and sends it to the user.
        await advert.logadvert(interaction, msg, warning, loggingchannel)
        await advert.sendadvertuser(interaction, msg, warning)
        await interaction.followup.send(f"{msg.author.mention} successfully warned")

    @app_commands.command(name="early72", description="adcommand: Use this when an advert was posted too early in normal search channels")
    @adefs.check_slash_db_roles()
    async def early72(self, interaction: discord.Interaction, message_link: str) -> None:
        await interaction.response.defer(ephemeral=True)
        link = message_link.split('/')
        try:
            print("channel")
            server = self.bot.get_guild(int(link[4]))
            channel = server.get_channel(int(link[5]))
            msg = await channel.fetch_message(int(link[6]))

        except:
            print("thread")
            server = self.bot.get_guild(int(link[4]))
            thread = server.get_thread(int(link[5]))
            msg = await thread.fetch_message(int(link[6]))
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        adchannel = bot.get_channel(763058339088957548)
        user = msg.author
        # adds warning to database
        swarnings = await advert.increasewarnings(interaction, user)
        warning = """Hello, I am a staff member of **Roleplay Meets: Reborn** . The advert you have posted within our {} has been posted too early, please wait 3 days(72 hours) between each posts.

Repeatedly posting too early may lead to a search ban which means you can not post an advert for a certain time.

If you have any questions regarding adverts or the rules, don't hesitate to ask in <#977720278396305418>. 
Thank you for your cooperation!""".format(msg.channel.mention)
        await adchannel.send(
            f"{interaction.user.mention} has warned {user.mention} for posting an advert that was too early (72h)  {msg.channel.mention}\n userId: {user.id} Warning Count: {swarnings}")
        # Logs the advert and sends it to the user.
        await advert.logadvert(interaction, msg, warning, loggingchannel)
        await advert.sendadvertuser(interaction, msg, warning)
        await interaction.followup.send(f"{msg.author.mention} successfully warned")


    @app_commands.command(name="template", description="adcommand: Use this when an advert fails to follow the template")
    @adefs.check_slash_db_roles()
    async def template(self, interaction:discord.Interaction, message_link: str) -> None:
        await interaction.response.defer(ephemeral=True)
        link = message_link.split('/')
        try:
            print("channel")
            server = self.bot.get_guild(int(link[4]))
            channel = server.get_channel(int(link[5]))
            msg = await channel.fetch_message(int(link[6]))

        except:
            print("thread")
            server = self.bot.get_guild(int(link[4]))
            thread = server.get_thread(int(link[5]))
            msg = await thread.fetch_message(int(link[6]))
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        adchannel = bot.get_channel(763058339088957548)
        user = msg.author
        # adds warning to database
        swarnings = await advert.increasewarnings(interaction, user)
        warning = """Hello, I am a staff member of **Roleplay Meets: Reborn** . The advert you have posted within our {} does not match the template within the channel, the template can be found in the **channel pins**. 

Please be sure to provide all information that the template requests, as failure to abide by the template will result in your post being deleted!

If you have any questions regarding adverts or the rules, don't hesitate to ask in <#977720278396305418>. 
Thank you for your cooperation!""".format(msg.channel.mention)
        await adchannel.send(
            f"{interaction.user.mention} has warned {user.mention} for posting an advert that failed to follow the template in {msg.channel.mention}\n userId: {user.id} Warning Count: {swarnings}")
        # Logs the advert and sends it to the user.
        await advert.logadvert(interaction, msg, warning, loggingchannel)
        await advert.sendadvertuser(interaction, msg, warning)
        await interaction.followup.send(f"{msg.author.mention} successfully warned")

    @app_commands.command(name="custom", description="adcommand: Use this when you need to give a custom warning, or multiple at once.")
    @adefs.check_slash_db_roles()
    async def custom(self, interaction:discord.Interaction, message_link: str, *, warning:str) -> None:
        await interaction.response.defer(ephemeral=True)
        link = message_link.split('/')
        try:
            print("channel")
            server = self.bot.get_guild(int(link[4]))
            channel = server.get_channel(int(link[5]))
            msg = await channel.fetch_message(int(link[6]))

        except Exception as e:
            print(e)
            print("thread")
            server = self.bot.get_guild(int(link[4]))
            thread = server.get_thread(int(link[5]))
            msg = await thread.fetch_message(int(link[6]))
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        adchannel = bot.get_channel(763058339088957548)
        user = msg.author
        # adds warning to database
        swarnings = await advert.increasewarnings(interaction, user)
        await adchannel.send(
            f"{interaction.user.mention} has warned {user.mention} with a custom warning in {msg.channel.mention} with reason: {warning}\n userId: {user.id} Warning Count: {swarnings}")
        # Logs the advert and sends it to the user.
        await advert.logadvert(interaction, msg, warning, loggingchannel)
        await advert.sendadvertuser(interaction, msg, warning)
        await interaction.followup.send(f"{msg.author.mention} successfully warned")

    @app_commands.command(name="duplicate", description="adcommand: Use this when an advert is posted in multiple channels")
    @adefs.check_slash_db_roles()
    async def duplicate(self, interaction:discord.Interaction, message_link: str, *, args:str) -> None:
        await interaction.response.defer(ephemeral=True)
        link = message_link.split('/')
        try:
            print("channel")
            server = self.bot.get_guild(int(link[4]))
            channel = server.get_channel(int(link[5]))
            msg = await channel.fetch_message(int(link[6]))

        except:
            print("thread")
            server = self.bot.get_guild(int(link[4]))
            thread = server.get_thread(int(link[5]))
            msg = await thread.fetch_message(int(link[6]))
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        adchannel = bot.get_channel(763058339088957548)
        user = msg.author
        # adds warning to database
        swarnings = await advert.increasewarnings(interaction, user)
        sargs= args.split(" ")
        dupchannels = ', '.join(sargs)
        warning = """Hello, I am a staff member of **Roleplay Meets Reborn**, the advert you have posted in {} is a duplicate of what you've posted in {} and has been removed. Please don't repost the same advert in multiple channels! You can repost every 24 hours in quick search channels and every 72 hours in regular search channels or you can make changes to your advert and post it in **another** channel.

If you have any questions regarding adverts or the rules, don't hesitate to ask in <#977720278396305418>. 
Thank you for your cooperation!""".format(dupchannels, msg.channel.mention)
        await adchannel.send(
            f"{interaction.user.mention} has warned {user.mention} for posted multiple adverts in: {dupchannels} with the original being in  {msg.channel.mention}\n userId: {user.id} Warning Count: {swarnings}")
        # Logs the advert and sends it to the user.
        await advert.logadvert(interaction, msg, warning, loggingchannel)
        await advert.sendadvertuser(interaction, msg, warning)
        await interaction.followup.send(f"{msg.author.mention} successfully warned")

    @app_commands.command(name="format", description="adcommand: Use this when an advert has long lists, excessive spacing, non-standard text.")
    @adefs.check_slash_db_roles()
    async def format(self, interaction:discord.Interaction, message_link: str) -> None:
        await interaction.response.defer(ephemeral=True)
        link = message_link.split('/')
        try:
            print("channel")
            server = self.bot.get_guild(int(link[4]))
            channel = server.get_channel(int(link[5]))
            msg = await channel.fetch_message(int(link[6]))

        except:
            print("thread")
            server = self.bot.get_guild(int(link[4]))
            thread = server.get_thread(int(link[5]))
            msg = await thread.fetch_message(int(link[6]))
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        adchannel = bot.get_channel(763058339088957548)
        user = msg.author
        # adds warning to database
        swarnings = await advert.increasewarnings(interaction, user)
        warning = """Hello, I am a staff member of Roleplay Meets: Reborn. I am reaching out to you regarding your ad in {}. It has been removed due to **improper formatting.** Please review our Search Rules, specifically S8: Excessive Adverts and repost your ad with the appropriate fixes. 

Reasons your advert may have been removed include:
- Spacing between each list item
- Double spaces between paragraphs and/or sentences
- Having more than 10 items **total** in your lists. Lists **are** counted cumulatively or having an excessively long list
- Using a font that is not Discord's default font

If your advert has excessive lists, we do recommend using forums in order to share your lists, be they fandoms, potential pairings, genres, or other items you may want to list. If you have any questions regarding adverts or the rules, please do not hesitate to open up a ticket through <#977720278396305418>. Thank you for your cooperation!""".format(msg.channel.mention)
        await adchannel.send(
            f"{interaction.user.mention} has warned {user.mention} for posting an advert that failed to follow formatting guidelines in {msg.channel.mention}\n userId: {user.id} Warning Count: {swarnings}")
        # Logs the advert and sends it to the user.
        await advert.logadvert(interaction, msg, warning, loggingchannel)
        await advert.sendadvertuser(interaction, msg, warning)
        await interaction.followup.send(f"{msg.author.mention} successfully warned")

    @app_commands.command(name="website", description="adcommand: Use this when a link is not allowed or suspicious.")
    @adefs.check_slash_db_roles()
    async def website(self, interaction:discord.Interaction, message_link: str) -> None:
        await interaction.response.defer(ephemeral=True)
        link = message_link.split('/')
        try:
            print("channel")
            server = self.bot.get_guild(int(link[4]))
            channel = server.get_channel(int(link[5]))
            msg = await channel.fetch_message(int(link[6]))

        except:
            print("thread")
            server = self.bot.get_guild(int(link[4]))
            thread = server.get_thread(int(link[5]))
            msg = await thread.fetch_message(int(link[6]))
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        adchannel = bot.get_channel(763058339088957548)
        user = msg.author
        # adds warning to database
        swarnings = await advert.increasewarnings(interaction, user)
        warning = f"""Hello, I am a staff member of Roleplay Meets: Reborn. I am reaching out to you regarding your ad in {msg.channel.mention}. It has been removed due to **dangerous/inappropriate websites.**

Reasons your advert may have been removed include:
- You linked a porn website, which often carry dangerous advertisements riddled with viruses.
- You have linked to barbermonger, a website we do not allow on RMR.
- Staff has decided to not allow the link as we deem it suspicious and potentially harmful to our users.

The safety of our members is important to us and we appreciate your understanding in this matter. If you have any questions regarding adverts or the rules, please do not hesitate to open up a ticket through #ask-the-staff. Thank you for your cooperation!"""
        await adchannel.send(
            f"{interaction.user.mention} has warned {user.mention} for posting an advert that has a suspicious/prohibited link in {msg.channel.mention}\n userId: {user.id} Warning Count: {swarnings}")
        # Logs the advert and sends it to the user.
        await advert.logadvert(interaction, msg, warning, loggingchannel)
        await advert.sendadvertuser(interaction, msg, warning)
        await interaction.followup.send(f"{msg.author.mention} successfully warned")

    @app_commands.command(name="pictures", description="adcommand: Warn users who have more than 3 images")
    @adefs.check_slash_db_roles()
    async def pictures(self, interaction:discord.Interaction, message_link: str) -> None:
        await interaction.response.defer(ephemeral=True)
        link = message_link.split('/')
        try:
            print("channel")
            server = self.bot.get_guild(int(link[4]))
            channel = server.get_channel(int(link[5]))
            msg = await channel.fetch_message(int(link[6]))

        except:
            print("thread")
            server = self.bot.get_guild(int(link[4]))
            thread = server.get_thread(int(link[5]))
            msg = await thread.fetch_message(int(link[6]))
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        adchannel = bot.get_channel(763058339088957548)
        user = msg.author
        # adds warning to database
        swarnings = await advert.increasewarnings(interaction, user)
        warning = f"""Hello, I'm a **bot** of Roleplay Meets: Reborn. I'm reaching out to you regarding your ad in {msg.channel.mention}. It's been removed for **having more than 3 images**. Please repost it with the appropriate fixes.

    If you have any questions regarding adverts or the rules, don't hesitate to ask in <#977720278396305418>. 
    Thank you for your cooperation!"""
        await adchannel.send(
            f"{interaction.user.mention} has warned {user.mention} for posting an advert that had more than 3 images in {msg.channel.mention}\n userId: {user.id} Warning Count: {swarnings}")
        # Logs the advert and sends it to the user.
        await advert.logadvert(interaction, msg, warning, loggingchannel)
        await advert.sendadvertuser(interaction, msg, warning)
        await interaction.followup.send(f"{msg.author.mention} successfully warned")

    @app_commands.command(name="canonuapic", description="adcommand: Warn user which posted a picture with a canonically underaged character.")
    @adefs.check_slash_db_roles()
    async def uapictures(self, interaction:discord.Interaction, message_link: str) -> None:
        await interaction.response.defer(ephemeral=True)
        link = message_link.split('/')
        try:
            print("channel")
            server = self.bot.get_guild(int(link[4]))
            channel = server.get_channel(int(link[5]))
            msg = await channel.fetch_message(int(link[6]))

        except:
            print("thread")
            server = self.bot.get_guild(int(link[4]))
            thread = server.get_thread(int(link[5]))
            msg = await thread.fetch_message(int(link[6]))
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        adchannel = bot.get_channel(763058339088957548)
        user = msg.author
        # adds warning to database
        swarnings = await advert.increasewarnings(interaction, user)
        warning = f"""Hello, I'm a **bot** of Roleplay Meets: Reborn. I'm reaching out to you regarding your ad in {msg.channel.mention}. It's been removed for **posting an NSFW picture with a canonically underaged character**. Please repost without these images.

Roleplay Meets: Reborn no longer tolerates pictures of characters that have been aged up which are NSFW. Failure to comply further with this rule comes with dire consequences.

If you have any questions regarding adverts or the rules, don't hesitate to ask in #ask-the-staff. 
Thank you for your cooperation!"""
        await adchannel.send(
            f"{interaction.user.mention} has warned {user.mention} for posting an advert that had more than 3 images in {msg.channel.mention}\n userId: {user.id} Warning Count: {swarnings}")
        # Logs the advert and sends it to the user.
        await advert.logadvert(interaction, msg, warning, loggingchannel)
        await advert.sendadvertuser(interaction, msg, warning)
        await interaction.followup.send(f"{msg.author.mention} successfully warned")

    @app_commands.command(name="multi", description="adcommand: Use this when an advert fails to follow the template")
    @app_commands.choices(searchrule1=[
        Choice(name="ages", value="age"),
        Choice(name="early72", value="e72"),
        Choice(name="early24", value="e24"),
        Choice(name="format", value="form"),
        Choice(name="template", value="temp"),
        Choice(name="duplicate", value="dup"),
        Choice(name="pictures", value="pic"),
    ],
    searchrule2=[
        Choice(name="ages", value="age"),
        Choice(name="early72", value="e72"),
        Choice(name="early24", value="e24"),
        Choice(name="format", value="form"),
        Choice(name="template", value="temp"),
        Choice(name="duplicate", value="dup"),
        Choice(name="pictures", value="pic"),
    ],
    searchrule3=[
        Choice(name="ages", value="age"),
        Choice(name="early72", value="e72"),
        Choice(name="early24", value="e24"),
        Choice(name="format", value="form"),
        Choice(name="template", value="temp"),
        Choice(name="duplicate", value="dup"),
        Choice(name="pictures", value="pic"),
    ])
    @adefs.check_slash_db_roles()
    async def advanced(self, interaction:discord.Interaction, message_link: str, searchrule1: Choice[str], searchrule2: Choice[str] = None, searchrule3: Choice[str] = None) -> None:
        await interaction.response.defer(ephemeral=True)
        c = [searchrule1, searchrule2, searchrule3]
        values = []
        rules = ["Broken rules:"]
        for a in c:
            if a is not None:
                warn = await advert.addreason(self, a.value)
                rules.append(warn)
                values.append(a.name)
        urules = "\n- ".join(rules)
        uvalues = ", ".join(values)
        link = message_link.split('/')
        try:
            print("channel")
            server = self.bot.get_guild(int(link[4]))
            channel = server.get_channel(int(link[5]))
            msg = await channel.fetch_message(int(link[6]))

        except:
            print("thread")
            server = self.bot.get_guild(int(link[4]))
            thread = server.get_thread(int(link[5]))
            msg = await thread.fetch_message(int(link[6]))
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        adchannel = bot.get_channel(763058339088957548)
        user = msg.author
        # adds warning to database
        swarnings = await advert.increasewarnings(interaction, user)
        warning = f"""Hello, I am a staff member of Roleplay Meets: Reborn. I am reaching out to you regarding your ad in {msg.channel.mention}. It has been removed due to **improper formatting.** Please review our Search Rules, specifically S8: Excessive Adverts and repost your ad with the appropriate fixes.

{urules}

If your advert has excessive lists, we do recommend using forums in order to share your lists, be they fandoms, potential pairings, genres, or other items you may want to list. If you have any questions regarding adverts or the rules, please do not hesitate to open up a ticket through <#977720278396305418>. Thank you for your cooperation!"""
        await adchannel.send(
            f"{interaction.user.mention} has warned {user.mention} for posting an advert that failed to follow multiple rules({uvalues}) in {msg.channel.mention}\n userId: {user.id} Warning Count: {swarnings}")
        # Logs the advert and sends it to the user.
        await advert.logadvert(interaction, msg, warning, loggingchannel)
        await advert.sendadvertuser(interaction, msg, warning)
        await interaction.followup.send(f"{msg.author.mention} successfully warned")

    # allows staff to remove user's warnings
    @app_commands.command(name="warnremove", description="Adadmin: Remove a warning from a user")
    @adefs.check_slash_admin_roles()
    async def adwarningremove(self, ctx: discord.Interaction, user: discord.Member, number: int = 1) -> None:
        bot = self.bot
        await ctx.response.send_message(f"Attempting to edit data for user: {user}")
        exists = session.query(db.warnings).filter_by(uid=user.id).first()
        try:
            exists.swarnings -= number
            session.commit()
            await ctx.channel.send(f"<@{exists.uid}> now has {exists.swarnings} warnings (removed: {number})")
        except Exception as e:
            print(e)
            await ctx.channel.send("Can't edit user's warnings")
            session.rollback()
            session.close()
    @app_commands.command(name="warnadd", description="Adadmin: add a warning from a user")
    @adefs.check_slash_admin_roles()
    async def adwarningadd(self, ctx: discord.Interaction, user: discord.Member, number: int = 1):
        bot = self.bot
        await ctx.response.send_message(f"Attempting to edit data for user: {user}")
        exists = session.query(db.warnings).filter_by(uid=user.id).first()
        try:
            exists.swarnings += number
            session.commit()
            await ctx.channel.send(f"<@{exists.uid}> now has {exists.swarnings} warnings (added: {number})")
        except Exception as e:
            print(e)
            await ctx.channel.send("Can't edit user's warnings")
            session.rollback()
            session.close()
#allows staff to change user's warnings

    @app_commands.command(name="warnset", description="Adadmin: set the amount of warnings of a user")
    @adefs.check_slash_admin_roles()
    async def adwarningset(self, ctx: discord.Interaction, user: discord.Member, number: int):
        bot = self.bot
        await ctx.response.send_message(f"Attempting to edit data for user: {user}")
        exists = session.query(db.warnings).filter_by(uid=user.id).first()
        try:
            exists.swarnings = number
            session.commit()
            await ctx.channel.send(f"<@{exists.uid}> now has {exists.swarnings} warnings (set to: {number} by {ctx.message.author.mention})")
        except:
            await ctx.channel.send("Can't edit user's warnings")
            session.rollback()
            session.close()

# PURGES ALL WARNINGS FROM DB. Only usable by dev.
    @commands.command(aliases=[])
    @adefs.check_admin_roles()
    async def adwarningreset(self, ctx):
        bot = self.bot
        await ctx.message.delete()
        if ctx.message.author.id == 188647277181665280:
<<<<<<< Updated upstream
            for member in ctx.guild.members:
                exists = session.query(db.warnings).filter_by(uid=user.id).first()
=======
            records = session.query(db.warnings).all()
            for member in records:
                userid1 = str(member.uid).replace(",", "")
                userid2 = userid1.replace(")", "")
                userid3 = userid2.replace("(", "")
                exists = session.query(db.warnings).filter_by(uid=userid3).first()
>>>>>>> Stashed changes
                if exists is not None:
                    exists.swarnings = 0
                    print(f"{member} reset")
                    continue
                else:
                    print(f"{member} failed")
                    continue
            session.commit()
            await ctx.send("All warnings reset.")
        else:
            ctx.send("This is a developer only command")
#looks up user's warnings

    @app_commands.command(name="warncheck", description="Adadmin: checks user's search warnings")
    @adefs.check_slash_admin_roles()
    async def warnlookup(self, ctx, user:discord.Member):
        bot = self.bot
        await ctx.response.send_message(f"Attempting to edit look up data for user: {user}")
        exists = session.query(db.warnings).filter_by(uid=user.id).first()
        embed = discord.Embed(title=f"{user}'s warnings", description=f"""User ID: {user.id}
Warning count: {exists.check}""")
        await ctx.channel.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(searchcommands(bot))
