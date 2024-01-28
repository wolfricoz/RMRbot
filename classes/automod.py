"""This module is used to handle the automod for the forums."""
import logging
import os.path
import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import discord
import pytz

from classes.AutomodComponents import AutomodComponents
from classes.Support.LogTo import automod_log, automod_approval_log
from classes.databaseController import ConfigData


class ForumAutoMod(ABC):
    """This class is used to handle the automod for the forums."""

    @staticmethod
    @abstractmethod
    def config(guildid):
        """This function is used to get the config for the forums."""
        data = ConfigData().get_key(guildid, "FORUM")
        return data

    @staticmethod
    @abstractmethod
    async def info(forum, thread, msg):
        """This to remind users about the bumping rules"""
        # This module needs to be fixed; keeps adding too much tags.
        matched = await AutomodComponents.tags(thread, forum, msg)
        await ForumAutoMod.checktags(thread)
        # applies the new tag
        for a in forum.available_tags:
            if a.name == "New":
                await thread.add_tags(a, reason="new post")
        botmessage = await thread.send(
                f"Thank you for posting, you may bump every 3 days with the /forum bump command or simply type bump and users can request to DM in your comments."
                f"\n\n"
                f"To close the advert, please use /forum close")
        if len(thread.applied_tags) >= 5:
            print("too many tags")
            return botmessage
        if matched:
            count = 0
            maxtags = 5 - len(thread.applied_tags)
            counted_tags = []
            for x in matched:
                if x in thread.applied_tags:
                    continue
                if count >= maxtags:
                    break
                counted_tags.append(x)
                count += 1

            fm = ', '.join([x.name for x in counted_tags])

            # print(f"[debugging] adding tags to {thread.name}: {matched} ({len(matched)}), {len(thread.applied_tags)}, reason: new post")
            await thread.add_tags(*counted_tags, reason=f"Automod applied {fm}")
            await thread.send(
                    f"Automod has added: `{fm}` to your post. You can edit your tags by right-clicking the thread!")

        return botmessage

    @staticmethod
    @abstractmethod
    async def bump(bot, interaction):
        """This function is used to bump the post."""
        utc = pytz.UTC
        thread: discord.Thread = interaction.channel
        dcheck = datetime.now() + timedelta(hours=-60)
        bcheck = dcheck.replace(tzinfo=utc)
        messages = thread.history(after=bcheck, oldest_first=False)
        count = 0
        user_count = 0
        if thread.owner_id != interaction.user.id:
            await interaction.followup.send("You can't bump another's post.")
            return
        if interaction.channel.type != discord.ChannelType.public_thread:
            return
        async for m in messages:
            if m.author.id == bot.application_id:
                count += 1
            if count == 1:
                pm = m.created_at.replace(tzinfo=utc)
                if abs(pm - bcheck).total_seconds() / 3600 <= 70:
                    print("72 hours has passed")
                    break

                timeinfo = f"last bump: {round(abs(pm - bcheck).total_seconds() / 3600, 2)} hours ago"
                logging.info(timeinfo)
                try:
                    await interaction.user.send(
                            f"Your last bump was within the 72 hours cooldown period in {interaction.channel.mention}, please wait {timeinfo} hours before bumping again."
                            f"\nLast bump: {discord.utils.format_dt(pm, style='f')}timediff: {discord.utils.format_dt(pm, style='R')}")
                except discord.Forbidden:
                    await interaction.channel.send(
                            f"Your last bump was within the 72 hours cooldown period in {interaction.channel.mention}, please wait {timeinfo} hours before bumping again."
                            f"\nLast bump: {discord.utils.format_dt(pm, style='f')}timediff: {discord.utils.format_dt(pm, style='R')}")

                await automod_log(bot, interaction.guild_id, f"User tried to bump too soon in {interaction.channel.mention}: {timeinfo}", "automodlog")
                await interaction.followup.send(f"You've bumped too soon, please wait {timeinfo} hours before bumping again.")
                return
            if m.author.id == interaction.user.id:
                user_count += 1

        forum = bot.get_channel(thread.parent_id)
        og = await thread.fetch_message(thread.id)
        og_time = og.created_at.replace(tzinfo=utc)
        try:
            if og_time is not None and og_time <= bcheck and user_count <= 0 or og_time is None and user_count <= 0:
                await AutomodComponents.change_tags_approve(forum, thread)
                await interaction.channel.send("Post successfully bumped and automatically approved")
                await automod_approval_log(bot, interaction.guild_id, f"User bumped post in {interaction.channel.mention} and was automatically approved", "automodlog")
                return
        except Exception as e:
            logging.error(e)
        await AutomodComponents.change_tags_bump(forum, thread)

        await interaction.channel.send("Post successfully bumped and awaiting manual review")
        await interaction.followup.send("You've successfully bumped your post")

    @staticmethod
    @abstractmethod
    async def duplicate(thread: discord.Thread, bot, originalmsg: discord.Message):
        """This function is used to check for duplicate posts."""
        forums = ForumAutoMod.config(thread.guild.id)
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
                return checkdup

    @staticmethod
    @abstractmethod
    async def reminder(thread: discord.Thread, guildid):
        """This function is used to remind users about the bumping rules."""
        reminder = ConfigData().get_key_or_none(guildid, "REMINDER")
        if reminder is None:
            return
        embed = discord.Embed(title="Rule Reminder", description=reminder)
        try:
            await thread.send(embed=embed)
        except discord.NotFound:
            print(f"thread not found, {thread}")

    @staticmethod
    @abstractmethod
    async def checktags(thread):
        """This function is used to check the tags."""
        tags = thread.applied_tags
        remove = ["new", "approved", "bump"]
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
    async def check_header(message: discord.Message, thread: discord.Thread) -> bool | None:
        """This function is used to check the header."""
        header = re.match(r"(All character'?s? are \(?[1-9][0-9])([\S\n\t\v ]*)([-|—]{5,100})", message.content, flags=re.IGNORECASE)
        pattern = re.compile(r'\bsearch\b', re.IGNORECASE)
        search = pattern.search(thread.parent.name)
        if search is None:
            return
        if header is None:
            await message.author.send(
                    """Your advert has been removed because it does not have a header. Please re-post with a header.
```text
All characters are (ages)+
(optional) Tags:
(optional) Pairings:
(Any other information you want to stand out!)
-----------------------------------
Your advert here
```

You can use this website to check your header: https://regex101.com/r/HYkkf9/2
This rule went in to effect on the 01/01/2024. If you have any questions, please open a ticket!
""")
            await thread.delete()
            return True

    @staticmethod
    @abstractmethod
    def approval_log(interaction):
        """This function is used to log the approval."""
        file_name = f"config/approvals{datetime.now().strftime('%m-%y')}.txt"
        if os.path.isfile(file_name) is False:
            with open(file_name, 'w') as f:
                f.write('Advert Approvals')
        with open(file_name, 'a') as f:
            f.write(
                    f"\n{datetime.now().strftime('%m/%d/%Y %I:%M %p')}: {interaction.user} has approved post '{interaction.channel}'")

    @staticmethod
    @abstractmethod
    async def get_message(thread: discord.Thread):
        """Loops through the history of the channel and retrieves the message"""
        if thread.type != discord.ChannelType.public_thread:
            return False
        messages = thread.history(limit=10, oldest_first=True)
        async for message in messages:
            if message.id == thread.id:
                return message
        else:
            return thread.starter_message
