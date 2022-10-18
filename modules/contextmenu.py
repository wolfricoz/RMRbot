import discord
from discord.ext import commands
from datetime import datetime
import adefs
from abc import ABC, abstractmethod
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, column
import typing
from discord import app_commands
import db

Session = sessionmaker(bind=db.engine)
session = Session()

class advert(ABC):
    @abstractmethod
    async def clogadvert(ctx, msg, warning, lc):
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

    async def csendadvertuser(ctx, msg, warning):
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

    async def cincreasewarnings(ctx, user):
        exists = session.query(db.warnings).filter_by(uid=user.id).first()
        try:
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
        except:
            print("Database error, rolled back")
            session.rollback()

class contextmenus(commands.Cog, name="contextmenus"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.adages = app_commands.ContextMenu(name="adages", callback=self.madages,)
        self.bot.tree.add_command(self.adages)
        self.adtl = app_commands.ContextMenu(name="adtoolongs", callback=self.madtl,)
        self.bot.tree.add_command(self.adtl)
        self.adts = app_commands.ContextMenu(name="adtooshort", callback=self.madts,)
        self.bot.tree.add_command(self.adts)
        self.adformat= app_commands.ContextMenu(name="adformat", callback=self.madformat,)
        self.bot.tree.add_command(self.adformat)
        self.ad24= app_commands.ContextMenu(name="adearly24", callback=self.made24,)
        self.bot.tree.add_command(self.ad24)
        #self.ad= app_commands.ContextMenu(name="adtooshorttest", callback=self.mad, )
        #self.bot.tree.add_command(self.ad)

#Max 5 per Message, Max 5 per Member
    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.adages.name, type=self.adages.type)
        self.bot.tree.remove_command(self.adtl.name, type=self.adtl.type)
        self.bot.tree.remove_command(self.adts.name, type=self.adts.type)
        self.bot.tree.remove_command(self.adformat.name, type=self.adformat.type)
        self.bot.tree.remove_command(self.ad24.name, type=self.ad24.type)
        #self.bot.tree.remove_command(self.ad.name, type=self.ad.type)


    async def madages(self, interaction: discord.Interaction, message: discord.Message) -> None:  # An annotation of discord.Message makes this a message command
        await interaction.response.defer(ephemeral=True)
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        adchannel = bot.get_channel(763058339088957548)
        user = message.author
        # adds warning to database
        swarnings = await advert.cincreasewarnings(interaction, user)
        warning = """Hello, I'm a staff member of **Roleplay Meets Reborn**. The advert you have posted in {} has failed to mention the ages of the characters you intend to use in your roleplay, as required by our sixth search rule. This includes both the characters you intend to write and the characters you want your writing partner to write. Due to this, your advert has been removed. __**Please include the ages of all characters or a general disclaimer**__, such as: "all characters are 18+", in the future. Characters under the age of 18 are not allowed to be advertised within our server.

The ages must be displayed on the advertisement on discord.

If you have any more questions, our staff team is always available to help you.
<#977720278396305418>""".format(message.channel.mention)
        await adchannel.send(
            f"{interaction.user.mention} has warned {user.mention} for failing to include character ages to their adverts in {message.channel.mention}\n userId: {user.id} Warning Count: {swarnings}")
        # Logs the advert and sends it to the user.
        await advert.clogadvert(interaction, message, warning, loggingchannel)
        await advert.csendadvertuser(interaction, message, warning)
        await interaction.followup.send("Success!")

    async def madtl(self, interaction: discord.Interaction,
                    message: discord.Message) -> None:  # An annotation of discord.Message makes this a message command
        await interaction.response.defer(ephemeral=True)
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        adchannel = bot.get_channel(763058339088957548)
        user = message.author
        # adds warning to database
        swarnings = await advert.cincreasewarnings(interaction, user)
        warning = """Hello, I'm a staff member of **Roleplay Meets: Reborn**. I'm reaching out to you regarding your ad in {}. It's been removed because: **your advert was over 600 characters (your advert: {})**. Please repost it in the appropriate channel.

If you have any questions regarding adverts or the rules, don't hesitate to ask. Thank you for your cooperation!
<#977720278396305418>""".format(message.channel.mention, len(message.content))
        await adchannel.send(
            f"{interaction.user.mention} has warned {user.mention} for posting an advert that was too long  in {message.channel.mention}\n userId: {user.id}\nCharacter Count: {len(message.content)} Warning Count: {swarnings}")
        # Logs the advert and sends it to the user.
        await advert.clogadvert(interaction, message, warning, loggingchannel)
        await advert.csendadvertuser(interaction, message, warning)
        await interaction.followup.send("Success!")

    async def madts(self, interaction: discord.Interaction,
                    message: discord.Message) -> None:  # An annotation of discord.Message makes this a message command
        await interaction.response.defer(ephemeral=True)
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        adchannel = bot.get_channel(763058339088957548)
        user = message.author
        # adds warning to database
        swarnings = await advert.cincreasewarnings(interaction, user)
        warning = """Hello, I'm a staff member of **Roleplay Meets: Reborn**. I'm reaching out to you regarding your ad in {}. It's been removed because: **your advert was under 600 characters (your advert: {})**. Please repost it in the appropriate channel.

If you have any questions regarding adverts or the rules, don't hesitate to ask. Thank you for your cooperation!
<#977720278396305418>""".format(message.channel.mention, len(message.content))
        await adchannel.send(
            f"{interaction.user.mention} has warned {user.mention} for posting an advert that was too short in  {message.channel.mention}\n userId: {user.id} Character Count: {len(message.content)} Warning Count: {swarnings}")
        # Logs the advert and sends it to the user.
        await advert.clogadvert(interaction, message, warning, loggingchannel)
        await advert.csendadvertuser(interaction, message, warning)
        await interaction.followup.send("Success!")

    async def madformat(self, interaction: discord.Interaction,
                    message: discord.Message) -> None:  # An annotation of discord.Message makes this a message command
        await interaction.response.defer(ephemeral=True)
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        adchannel = bot.get_channel(763058339088957548)
        user = message.author
        # adds warning to database
        swarnings = await advert.cincreasewarnings(interaction, user)
        warning = """Hello, I am a staff member of Roleplay Meets: Reborn. I am reaching out to you regarding your ad in {}. It has been removed due to **improper formatting.** Please review our Search Rules, specifically S8: Excessive Adverts and repost your ad with the appropriate fixes. 

Reasons your advert may have been removed include:
- Spacing between each list item
- Double spaces between paragraphs and/or sentences
- Having more than 10 items **total** in your lists. Lists **are** counted cumulatively or having an excessively long list
- Using a font that is not Discord's default font

If your advert has excessive lists, we do recommend using forums in order to share your lists, be they fandoms, potential pairings, genres, or other items you may want to list. If you have any questions regarding adverts or the rules, please do not hesitate to open up a ticket through <#977720278396305418>. Thank you for your cooperation!""".format(message.channel.mention)
        await adchannel.send(
            f"{interaction.user.mention} has warned {user.mention} for posting an advert that failed to follow formatting guidelines in {message.channel.mention}\n userId: {user.id} Warning Count: {swarnings}")
        # Logs the advert and sends it to the user.
        await advert.clogadvert(interaction, message, warning, loggingchannel)
        await advert.csendadvertuser(interaction, message, warning)
        await interaction.followup.send("Success!")

    async def made24(self, interaction: discord.Interaction,
                    message: discord.Message) -> None:  # An annotation of discord.Message makes this a message command
        await interaction.response.defer(ephemeral=True)
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        adchannel = bot.get_channel(763058339088957548)
        user = message.author
        # adds warning to database
        swarnings = await advert.cincreasewarnings(interaction, user)
        warning = """Hello, I am a staff member of **Roleplay Meets: Reborn** . The advert you have posted within our {} has been posted too early, please wait 1 day(24 hours) between each posts.

        Repeatedly posting too early may lead to a search ban which means you can not post an advert for a certain time.

        If you have any questions regarding adverts or the rules, don't hesitate to ask in <#977720278396305418>. 
        Thank you for your cooperation!""".format(message.channel.mention)
        await adchannel.send(
            f"{interaction.user.mention} has warned {user.mention} for posting an advert that was too early (24h)  in {message.channel.mention}\n userId: {user.id} Warning Count: {swarnings}")
        # Logs the advert and sends it to the user.
        await advert.clogadvert(interaction, message, warning, loggingchannel)
        await advert.csendadvertuser(interaction, message, warning)
        await interaction.followup.send("Success!")

    async def made72(self, interaction: discord.Interaction,
                    message: discord.Message) -> None:  # An annotation of discord.Message makes this a message command
        await interaction.response.defer(ephemeral=True)
        bot = self.bot
        loggingchannel = bot.get_channel(997282508523704350)
        adchannel = bot.get_channel(763058339088957548)
        user = message.author
        # adds warning to database
        swarnings = await advert.cincreasewarnings(interaction, user)
        warning = """Hello, I am a staff member of **Roleplay Meets: Reborn** . The advert you have posted within our {} has been posted too early, please wait 3 days(72 hours) between each posts.

        Repeatedly posting too early may lead to a search ban which means you can not post an advert for a certain time.

        If you have any questions regarding adverts or the rules, don't hesitate to ask in <#977720278396305418>. 
        Thank you for your cooperation!""".format(message.channel.mention)
        await adchannel.send(
            f"{interaction.user.mention} has warned {user.mention} for posting an advert that was too early (72h) in {message.channel.mention}\n userId: {user.id} Warning Count: {swarnings}")
        # Logs the advert and sends it to the user.
        await advert.clogadvert(interaction, message, warning, loggingchannel)
        await advert.csendadvertuser(interaction, message, warning)
        await interaction.followup.send("Success!")

async def setup(bot: commands.Bot):
    await bot.add_cog(contextmenus(bot))