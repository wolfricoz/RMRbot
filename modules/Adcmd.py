import discord
from discord.ext import commands
from datetime import datetime
import adefs
from abc import ABC, abstractmethod
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, column
import typing

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
            await ctx.send("Can't DM user")
            pass

    async def increasewarnings(ctx, user):
        exists = session.query(db.warnings).filter_by(uid=user.id).first()
        if exists is not None:
            exists.swarnings += 1
            session.commit()
            return exists.swarnings
        else:
            tr = db.warnings(member.id, 1)
            session.add(tr)
            session.commit()
            exists = session.query(db.warnings).filter_by(uid=user.id).first()
            return exists.swarnings


class searchcommands(commands.Cog, name="adcommands"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    '''Search Commands'''

    @commands.command()
    @adefs.check_db_roles()
    async def adages(self, ctx, msg: discord.Message):
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        await ctx.message.delete()
        adchannel = bot.get_channel(763058339088957548)
        user = msg.author
        #adds warning to database
        swarnings = await advert.increasewarnings(ctx, user)
        warning = """Hello, I'm a staff member of **Roleplay Meets Reborn**. The advert you have posted in {} has failed to mention the ages of the characters you intend to use in your roleplay, as required by our sixth search rule. This includes both the characters you intend to write and the characters you want your writing partner to write. Due to this, your advert has been removed. __**Please include the ages of all characters or a general disclaimer**__, such as: "all characters are 18+", in the future. Characters under the age of 18 are not allowed to be advertised within our server.

The ages must be displayed on the advertisement on discord.

If you have any more questions, our staff team is always available to help you.
<#977720278396305418>""".format(msg.channel.mention)
        await adchannel.send(
            f"{ctx.message.author.mention} has warned {user.mention} for failing to include character ages to their adverts in {msg.channel.mention}\n userId: {user.id} Warning Count: {swarnings}")
        #Logs the advert and sends it to the user.
        await advert.logadvert(ctx, msg, warning, loggingchannel)
        await advert.sendadvertuser(ctx, msg, warning)


    @commands.command(aliases=['adtl', 'adlong'])
    @adefs.check_db_roles()
    async def adtoolong(self, ctx, msg: discord.Message):
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        await ctx.message.delete()
        adchannel = bot.get_channel(763058339088957548)
        user = msg.author
        # adds warning to database
        swarnings = await advert.increasewarnings(ctx, user)
        warning = """Hello, I'm a staff member of **Roleplay Meets: Reborn**. I'm reaching out to you regarding your ad in {}. It's been removed because: **your advert was over 600 characters (your advert: {})**. Please repost it in the appropriate channel.

        If you have any questions regarding adverts or the rules, don't hesitate to ask. Thank you for your cooperation!
        <#977720278396305418>""".format(msg.channel.mention, len(msg.content))
        await adchannel.send(
            f"{ctx.message.author.mention} has warned {user.mention} for posting an advert that was too long  in {msg.channel.mention}\n userId: {user.id}\nCharacter Count: {len(msg.content)} Warning Count: {swarnings}")
        # Logs the advert and sends it to the user.
        await advert.logadvert(ctx, msg, warning, loggingchannel)
        await advert.sendadvertuser(ctx, msg, warning)


    @commands.command(aliases=['adts', 'adshort'])
    @adefs.check_db_roles()
    async def adtooshort(self, ctx, msg: discord.Message):
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        await ctx.message.delete()
        adchannel = bot.get_channel(763058339088957548)
        user = msg.author
        # adds warning to database
        swarnings = await advert.increasewarnings(ctx, user)
        warning = """Hello, I'm a staff member of **Roleplay Meets: Reborn**. I'm reaching out to you regarding your ad in {}. It's been removed because: **your advert was under 600 characters (your advert: {})**. Please repost it in the appropriate channel.

        If you have any questions regarding adverts or the rules, don't hesitate to ask. Thank you for your cooperation!
        <#977720278396305418>""".format(msg.channel.mention, len(msg.content))
        await adchannel.send(
            f"{ctx.message.author.mention} has warned {user.mention} for posting an advert that was too short in  {msg.channel.mention}\n userId: {user.id} Character Count: {len(msg.content)} Warning Count: {swarnings}")
        # Logs the advert and sends it to the user.
        await advert.logadvert(ctx, msg, warning, loggingchannel)
        await advert.sendadvertuser(ctx, msg, warning)


    @commands.command(aliases=['spacing'])
    @adefs.check_db_roles()
    async def adspacing(self, ctx, msg: discord.Message):
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        await ctx.message.delete()
        adchannel = bot.get_channel(763058339088957548)
        user = msg.author
        # adds warning to database
        swarnings = await advert.increasewarnings(ctx, user)
        warning = """Hello, I'm a staff of Roleplay Meets: Reborn. I'm reaching out to you regarding your ad in {}. It's been removed for **having excessive spacing/long lists**. Please repost it with the appropriate fixes.

        Reasons your advert may have been removed:
        - Spacing between each list item
        - double spaces between paragraphs/sentences. 

        If you have any questions regarding adverts or the rules, don't hesitate to ask in <#977720278396305418>. 
        Thank you for your cooperation!""".format(msg.channel.mention)
        await adchannel.send(
            f"{ctx.message.author.mention} has warned {user.mention} for posting an advert that had excessive spacing  in {msg.channel.mention}\n userId: {user.id} Warning Count: {swarnings}")
        # Logs the advert and sends it to the user.
        await advert.logadvert(ctx, msg, warning, loggingchannel)
        await advert.sendadvertuser(ctx, msg, warning)


    @commands.command(aliases=['ad24'])
    @adefs.check_db_roles()
    async def adearly24(self, ctx, msg: discord.Message):
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        await ctx.message.delete()
        adchannel = bot.get_channel(763058339088957548)
        user = msg.author
        # adds warning to database
        swarnings = await advert.increasewarnings(ctx, user)
        warning = """Hello, I am a staff member of **Roleplay Meets: Reborn** . The advert you have posted within our {} has been posted too early, please wait 1 day(24 hours) between each posts.

        Repeatedly posting too early may lead to a search ban which means you can not post an advert for a certain time.

        If you have any questions regarding adverts or the rules, don't hesitate to ask in <#977720278396305418>. 
        Thank you for your cooperation!""".format(msg.channel.mention)
        await adchannel.send(
            f"{ctx.message.author.mention} has warned {user.mention} for posting an advert that was too early (24h)  in {msg.channel.mention}\n userId: {user.id} Warning Count: {swarnings}")
        # Logs the advert and sends it to the user.
        await advert.logadvert(ctx, msg, warning, loggingchannel)
        await advert.sendadvertuser(ctx, msg, warning)

    @commands.command(aliases=['ad72'])
    @adefs.check_db_roles()
    async def adearly72(self, ctx, msg: discord.Message):
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        await ctx.message.delete()
        adchannel = bot.get_channel(763058339088957548)
        user = msg.author
        # adds warning to database
        swarnings = await advert.increasewarnings(ctx, user)
        warning = """Hello, I am a staff member of **Roleplay Meets: Reborn** . The advert you have posted within our {} has been posted too early, please wait 3 days(72 hours) between each posts.

        Repeatedly posting too early may lead to a search ban which means you can not post an advert for a certain time.

        If you have any questions regarding adverts or the rules, don't hesitate to ask in <#977720278396305418>. 
        Thank you for your cooperation!""".format(msg.channel.mention)
        await adchannel.send(
            f"{ctx.message.author.mention} has warned {user.mention} for posting an advert that was too early (72h)  {msg.channel.mention}\n userId: {user.id} Warning Count: {swarnings}")
        # Logs the advert and sends it to the user.
        await advert.logadvert(ctx, msg, warning, loggingchannel)
        await advert.sendadvertuser(ctx, msg, warning)


    @commands.command(aliases=['adt'])
    @adefs.check_db_roles()
    async def adtemplate(self, ctx, msg: discord.Message):
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        await ctx.message.delete()
        adchannel = bot.get_channel(763058339088957548)
        user = msg.author
        # adds warning to database
        swarnings = await advert.increasewarnings(ctx, user)
        warning = """Hello, I am a staff member of **Roleplay Meets: Reborn** . The advert you have posted within our {} does not match the template within the channel, the template can be found in the **channel pins**. 

        Please be sure to provide all information that the template requests, as failure to abide by the template will result in your post being deleted!

        If you have any questions regarding adverts or the rules, don't hesitate to ask in <#977720278396305418>. 
        Thank you for your cooperation!""".format(msg.channel.mention)
        await adchannel.send(
            f"{ctx.message.author.mention} has warned {user.mention} for posting an advert that failed to follow the template in {msg.channel.mention}\n userId: {user.id} Warning Count: {swarnings}")
        # Logs the advert and sends it to the user.
        await advert.logadvert(ctx, msg, warning, loggingchannel)
        await advert.sendadvertuser(ctx, msg, warning)

    @commands.command(aliases=['adc'])
    @adefs.check_db_roles()
    async def adcustom(self, ctx, msg: discord.Message, *, message):
        "Gives the user a custom warning"
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        await ctx.message.delete()
        adchannel = bot.get_channel(763058339088957548)
        user = msg.author
        # adds warning to database
        swarnings = await advert.increasewarnings(ctx, user)
        await adchannel.send(
            f"{ctx.message.author.mention} has warned {user.mention} with a custom warning in {msg.channel.mention} with reason: {message}\n userId: {user.id} Warning Count: {swarnings}")
        # Logs the advert and sends it to the user.
        await advert.logadvert(ctx, msg, message, loggingchannel)
        await advert.sendadvertuser(ctx, msg, message)

    @commands.command(aliases=['add'])
    @adefs.check_db_roles()
    async def addup(self, ctx, msg: discord.Message, *args: str):
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        await ctx.message.delete()
        adchannel = bot.get_channel(763058339088957548)
        user = msg.author
        # adds warning to database
        swarnings = await advert.increasewarnings(ctx, user)
        dupchannels = ', '.join(args)
        warning = """Hello, I am a staff member of **Roleplay Meets Reborn**, the advert you have posted in {} is a duplicate of what you've posted in {} and has been removed. Please don't repost the same advert in multiple channels! You can repost every 24 hours in quick search channels and every 72 hours in regular search channels or you can make changes to your advert and post it in **another** channel.

        If you have any questions regarding adverts or the rules, don't hesitate to ask in <#977720278396305418>. 
        Thank you for your cooperation!""".format(dupchannels, msg.channel.mention)
        await adchannel.send(
            f"{ctx.message.author.mention} has warned {user.mention} for posted multiple adverts in: {dupchannels} with the original being in  {msg.channel.mention}\n userId: {user.id} Warning Count: {swarnings}")
        # Logs the advert and sends it to the user.
        await advert.logadvert(ctx, msg, warning, loggingchannel)
        await advert.sendadvertuser(ctx, msg, warning)

    @commands.command(aliases=['adl', 'list'])
    @adefs.check_db_roles()
    async def adlist(self, ctx, msg: discord.Message):
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        await ctx.message.delete()
        adchannel = bot.get_channel(763058339088957548)
        user = msg.author
        # adds warning to database
        swarnings = await advert.increasewarnings(ctx, user)
        warning = """Hello, I'm a **bot** of Roleplay Meets: Reborn. I'm reaching out to you regarding your ad in {}. It's been removed for **long lists**. Please repost it with the appropriate fixes.

        Reasons your advert may have been removed:
        - Spacing between each list item
        - More than 10 items **total** in your lists. All lists are counted to this.
        - Excessively long lists, we suggest using google docs for very long lists.

        If you have any questions regarding adverts or the rules, don't hesitate to ask in <#977720278396305418>. 
        Thank you for your cooperation!""".format(msg.channel.mention)
        await adchannel.send(
            f"{ctx.message.author.mention} has warned {user.mention} for posting an advert that had excessive lists in {msg.channel.mention}\n userId: {user.id} Warning Count: {swarnings}")
        # Logs the advert and sends it to the user.
        await advert.logadvert(ctx, msg, warning, loggingchannel)
        await advert.sendadvertuser(ctx, msg, warning)

    @commands.command(aliases=['adpic', 'pictures'])
    @adefs.check_db_roles()
    async def adpictures(self, ctx, msg: discord.Message):
        "Warn users who have more than 3 images in their advert"
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        await ctx.message.delete()
        adchannel = bot.get_channel(763058339088957548)
        user = msg.author
        # adds warning to database
        swarnings = await advert.increasewarnings(ctx, user)
        warning = f"""Hello, I'm a **bot** of Roleplay Meets: Reborn. I'm reaching out to you regarding your ad in {msg.channel.mention}. It's been removed for **having more than 3 images**. Please repost it with the appropriate fixes.

        If you have any questions regarding adverts or the rules, don't hesitate to ask in <#977720278396305418>. 
        Thank you for your cooperation!"""
        await adchannel.send(
            f"{ctx.message.author.mention} has warned {user.mention} for posting an advert that had more than 3 images in {msg.channel.mention}\n userId: {user.id} Warning Count: {swarnings}")
        # Logs the advert and sends it to the user.
        await advert.logadvert(ctx, msg, warning, loggingchannel)
        await advert.sendadvertuser(ctx, msg, warning)

    @commands.command(aliases=['ft'])
    @adefs.check_db_roles()
    async def forumtest(self, ctx, msg: discord.Message):
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        await ctx.message.delete()
        adchannel = bot.get_channel(763058339088957548)
        user = msg.author
        # adds warning to database
        swarnings = await advert.increasewarnings(ctx, user)
        warning = """Test""".format(msg.channel.mention)
        await adchannel.send(
            f"{ctx.message.author.mention} has warned {user.mention} Test {msg.channel.mention}\n userId: {user.id} Warning Count: {swarnings}")
        # Logs the advert and sends it to the user.
        await advert.logadvert(ctx, msg, warning, loggingchannel)
        await advert.sendadvertuser(ctx, msg, warning)


    # allows staff to remove user's warnings
    @commands.command(aliases=["warnrem"])
    @adefs.check_admin_roles()
    async def adwarningremove(self, ctx, user : discord.Member, number: int = 1):
        bot = self.bot
        await ctx.message.delete()
        exists = session.query(db.warnings).filter_by(uid=user.id).first()
        try:
            exists.swarnings -= number
            session.commit()
            await ctx.send(f"<@{exists.uid}> now has {exists.swarnings} warnings (removed: {number})")
        except:
            await ctx.send("Can't edit user's warnings")
#allows staff to change user's warnings
    @commands.command(aliases=["warnset"])
    @adefs.check_admin_roles()
    async def adwarningset(self, ctx, user : discord.Member, number: int):
        bot = self.bot
        await ctx.message.delete()
        exists = session.query(db.warnings).filter_by(uid=user.id).first()
        try:
            exists.swarnings = number
            session.commit()
            await ctx.send(f"<@{exists.uid}> now has {exists.swarnings} warnings (set to: {number} by {ctx.message.author.mention})")
        except:
            await ctx.send("Can't edit user's warnings")

# PURGES ALL WARNINGS FROM DB. Only usable by dev.
    @commands.command(aliases=[])
    @adefs.check_admin_roles()
    async def adwarningreset(self, ctx):
        bot = self.bot
        await ctx.message.delete()
        if ctx.message.author.id == 188647277181665280:
            for member in ctx.guild.members:
                exists = session.query(db.warnings).filter_by(uid=user.id).first()
                if exists is not None:
                    exists.swarnings = 0
                    continue
                else:
                    continue
            await ctx.send("All warnings reset.")
        else:
            ctx.send("This is a developer only command")
#looks up user's warnings
    @commands.command(aliases=["warncheck"])
    @adefs.check_db_roles()
    async def warnlookup(self, ctx, user:discord.Member):
        bot = self.bot
        await ctx.message.delete()
        exists = session.query(db.warnings).filter_by(uid=user.id).first()
        embed = discord.Embed(title=f"{user}'s warnings", description=f"""User ID: {user.id}
Warning count: {exists.swarnings}""")
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(searchcommands(bot))