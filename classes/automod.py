import json
import os.path
import re
from abc import ABC
from datetime import datetime, timedelta

import discord

from classes.AutomodComponents import AutomodComponents


class ForumAutoMod(ABC):

    def config(self, guildid):
        with open(f'jsons/{guildid}.json') as f:
            data = json.load(f)
            return data

    async def age(self, message, botmessage):
        check = re.search(
            r"\b(all character(s|'s) ([2-9][0-9]|18|19)|all character(s|'s) are ([2-9][0-9]|18|19)|([2-9][0-9]|18|19)\+ character(s|'s))\b",
            message.content, flags=re.IGNORECASE)
        if check is None:
            await botmessage.add_reaction("❓")
        else:
            await botmessage.add_reaction("🆗")
        print("age checked")

    async def info(self, forum, thread, msg):

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

    async def bump(self, interaction):
        bot = self.bot
        thread: discord.Thread = interaction.channel
        bcheck = datetime.utcnow() + timedelta(hours=-70)
        messages = thread.history(limit=300, after=bcheck, oldest_first=False)
        count = 0
        modchannel = bot.get_channel(763058339088957548)
        if thread.owner_id == interaction.user.id:
            async for m in messages:
                if m.author.id == bot.application_id:
                    count += 1
                    if count == 2:
                        lm = m.jump_url
                        pm = m.created_at
                        await interaction.user.send(
                            f"Your last bump was within the 72 hours cooldown period in {interaction.channel.mention} and was removed."
                            f"\nLast bump: {discord.utils.format_dt(pm, style='f')}timediff: {discord.utils.format_dt(pm, style='R')}")
                        await modchannel.send(
                            f"{interaction.user.mention} tried to bump within the 72 hours cooldown period in {interaction.channel.mention}."
                            f"\nLast bump: {discord.utils.format_dt(pm, style='f')}timediff: {discord.utils.format_dt(pm, style='R')}"
                        )
                        return
            forum = bot.get_channel(thread.parent_id)
            if interaction.channel.type == discord.ChannelType.public_thread:
                for a in forum.available_tags:
                    if a.name == "Bump":
                        await thread.add_tags(a)
                        await interaction.channel.send("Post successfully bumped")
                    if a.name == "Approved":
                        await thread.remove_tags(a)
                await interaction.followup.send("You've successfully bumped your post")
        else:
            await interaction.followup.send("You can't bump another's post.")

    async def duplicate(self, thread: discord.Thread, bot):
        forums = ForumAutoMod().config(thread.guild.id)
        originalmsg = await thread.fetch_message(thread.id)
        if thread.owner_id == 188647277181665280:
            return
        for c in forums['forums']:
            forum = bot.get_channel(c)
            checkdup = await AutomodComponents.check_duplicate(forum, thread, originalmsg)
            if checkdup:
                await thread.owner.send(
                    f"Hi, I am a bot of {thread.guild.name}. Your latest advertisement is too similar to {checkdup.channel.mention}; since 07/01/2023 you're only allowed to have the same advert up once. \n\n"
                    f"If you wish to bump your advert, do /forum bump on your advert, if you wish to move then please use /forum close")
                await thread.delete()
                return True

    async def reminder(self, thread: discord.Thread, guildid):
        with open(f'jsons/{guildid}.json', 'r') as f:
            conf = json.load(f)

        embed = discord.Embed(title="Rule Reminder", description=conf['reminder'])
        await thread.send(embed=embed)

    async def checktags(self, thread):
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

    def approval_log(self, interaction):
        if os.path.isfile('config/approvals.txt') is False:
            with open('config/approvals.txt', 'w') as f:
                f.write('Advert Approvals')
        with open('config/approvals.txt', 'a') as f:
            f.write(f"\n{datetime.now().strftime('%m/%d/%Y %I:%M %p')}: {interaction.user} has approved post '{interaction.channel}'")