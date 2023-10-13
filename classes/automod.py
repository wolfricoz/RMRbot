import json
import os.path
import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import discord
import pytz

from classes.AutomodComponents import AutomodComponents
from classes.databaseController import ConfigData

class ForumAutoMod(ABC):
    @staticmethod
    @abstractmethod
    def config(guildid):
        data = ConfigData().get_key(guildid, "FORUM")
        return data

    @staticmethod
    @abstractmethod
    async def age(message, botmessage):
        check = re.search(
                r"\b(all character(s|'s) ([2-9][0-9]|18|19)|all character(s|'s) are ([2-9][0-9]|18|19)|([2-9][0-9]|18|19)\+ character(s|'s))\b",
                message.content, flags=re.IGNORECASE)
        if check is None:
            await botmessage.add_reaction("❓")
        else:
            await botmessage.add_reaction("🆗")
        print("age checked")

    @staticmethod
    @abstractmethod
    async def info(forum, thread, msg):

        botmessage = None
        matched = await AutomodComponents.tags(thread, forum, msg)

        if matched:
            fm = ', '.join([x.name for x in matched])
            for a in forum.available_tags:
                if a.name == "New":
                    print("tag added")
                    matched.append(a)
            await thread.add_tags(*matched, reason=f"Automod applied {fm}")
            botmessage = await thread.send(
                    f"Thank you for posting, you may bump every 3 days with the /forum bump command or simply type bump and users can request to DM in your comments."
                    "\n\n"
                    f"Automod has added: `{fm}` to your post. You can edit your tags by right-clicking the thread!"
                    f"\n\n"
                    f"To close the advert, please use /forum close")
        else:
            for a in forum.available_tags:
                if a.name == "New":
                    print("tag added")
                    await thread.add_tags(a, reason="new post")
            botmessage = await thread.send(
                    f"Thank you for posting, you may bump every 3 days with the /forum bump command or simply type bump and users can request to DM in your comments."
                    f"\n\n"
                    f"To close the advert, please use /forum close")
        return botmessage
    @staticmethod
    @abstractmethod
    async def bump(bot, interaction):
        thread: discord.Thread = interaction.channel
        bcheck = datetime.now(pytz.UTC) + timedelta(hours=-70)
        messages = thread.history(limit=300, after=bcheck, oldest_first=False)
        count = 0
        user_count = 0
        if thread.owner_id != interaction.user.id:
            await interaction.followup.send("You can't bump another's post.")
            return
        if interaction.channel.type != discord.ChannelType.public_thread:
            return
        async for m in messages:
            print(m.id)
            if m.author.id == bot.application_id:
                count += 1
            if count == 1:
                lm = m.jump_url
                pm = m.created_at
                await interaction.user.send(
                        f"Your last bump was within the 72 hours cooldown period in {interaction.channel.mention} and was removed."
                        f"\nLast bump: {discord.utils.format_dt(pm, style='f')}timediff: {discord.utils.format_dt(pm, style='R')}")
                return
            if m.author.id == interaction.user.id:
                user_count += 1

        forum = bot.get_channel(thread.parent_id)
        og = await thread.fetch_message(thread.id)
        print(user_count)
        if og.edited_at is not None and og.edited_at <= bcheck and user_count <= 0 or og.edited_at is None and user_count <= 0:
            for a in forum.available_tags:
                if a.name == "Approved":
                    await thread.add_tags(a)
            await interaction.channel.send("Post successfully bumped and automatically approved")
            # await modchannel.send(f"`[Experimental]` Automatically approved bump of {interaction.channel.mention}. Post was not edited in the last 70 hours.")
            return
        for a in forum.available_tags:
            if a.name == "Bump":
                await thread.add_tags(a)
            if a.name == "Approved":
                await thread.remove_tags(a)
                await interaction.channel.send("Post successfully bumped and awaiting manual review")

        await interaction.followup.send("You've successfully bumped your post")

    @staticmethod
    @abstractmethod
    async def duplicate(thread: discord.Thread, bot):
        forums = ForumAutoMod.config(thread.guild.id)
        originalmsg = await thread.fetch_message(thread.id)
        if thread.owner_id == 188647277181665280:
            return
        for c in forums:
            forum = bot.get_channel(c)
            checkdup = await AutomodComponents.check_duplicate(forum, thread, originalmsg)
            if checkdup:
                await thread.owner.send(
                        f"Hi, I am a bot of {thread.guild.name}. Your latest advertisement is too similar to {checkdup.channel.mention}; since 07/01/2023 you're only allowed to have the same advert up once. \n\n"
                        f"If you wish to bump your advert, do /forum bump on your advert, if you wish to move then please use /forum close")
                await thread.delete()
                return True

    @staticmethod
    @abstractmethod
    async def reminder(thread: discord.Thread, guildid):
        reminder = ConfigData().get_key_or_none(guildid, "REMINDER")
        if reminder is None:
            return
        embed = discord.Embed(title="Rule Reminder", description=reminder)
        await thread.send(embed=embed)

    @staticmethod
    @abstractmethod
    async def checktags(thread):
        tags = thread.applied_tags
        remove = ["New", "Approved", "Bump"]
        found = False
        if len(tags) == 5:
            for tag in tags:
                if tag.name in remove:
                    await thread.remove_tags(tag)
                    found = True
            if not found:
                await thread.remove_tags(tags[0])

    @staticmethod
    @abstractmethod
    def approval_log(interaction):
        if os.path.isfile('config/approvals.txt') is False:
            with open('config/approvals.txt', 'w') as f:
                f.write('Advert Approvals')
        with open('config/approvals.txt', 'a') as f:
            f.write(
                f"\n{datetime.now().strftime('%m/%d/%Y %I:%M %p')}: {interaction.user} has approved post '{interaction.channel}'")
