import re
from abc import ABC
from datetime import datetime, timedelta
from time import sleep

import discord
from discord import client, app_commands
from discord.ext import commands
#from main import channels24

class ForumAutoMod(ABC):
    async def age(self, message, botmessage):
        check = re.search(
            r"\b(all character(s|'s) ([2-9][0-9]|18|19)|all character(s|'s) are ([2-9][0-9]|18|19)|([2-9][0-9]|18|19)\+ character(s|'s))\b",
            message.content, flags=re.IGNORECASE)
        if check is None:
            await botmessage.add_reaction("❓")
        else:
            await botmessage.add_reaction("🆗")
        print("age checked")

    async def tags(self, thread, forum, message):
        skip = ['New', 'Approved', 'Bump']
        matched = []
        count = 0
        for r in forum.available_tags:
            limitreg = re.compile(fr"(limit|limit.|no|dont|don't|)(.*?)({r})", flags=re.I)
            match = limitreg.search(message.content)
            if match:
                continue
            elif r.name in skip:
                pass
            elif count == 4:
                break
            else:
                tagreg = re.compile(rf"{r.name}", flags=re.I)
                match = tagreg.search(message.content)
                matcht = tagreg.search(thread.name)
                if match:
                    matched.append(r)
                    count += 1
                if matcht:
                    matched.append(r)
                    count += 1
        return matched

class forum(commands.Cog, name="forum"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        bot = self.bot
        forum = bot.get_channel(thread.parent_id)
        tag = None
        msg: discord.Message = await thread.fetch_message(thread.id)
        matched = await ForumAutoMod.tags(self, thread, forum, msg)
        if matched:
            fm = ', '.join([x.name for x in matched])
            for a in forum.available_tags:
                if a.name == "New":
                    print("tag added")
                    matched.append(a)
            await thread.add_tags(*matched, reason=f"Automod applied {fm}")
            botmessage = await thread.send(
                f"Thank you for posting, you may bump every 3 days with the </bump:1084936906241998909> command and users can request to DM in your comments."
                "\n\n"
                f"Automod has added: `{fm}` to your post. You can edit your tags by right-clicking the thread!")
        else:
            for a in forum.available_tags:
                if a.name == "New":
                    print("tag added")
                    await thread.add_tags(a, reason="new post")
            botmessage = await thread.send(
                f"Thank you for posting, you may bump every 3 days with the </bump:1084936906241998909> command and users can request to DM in your comments.")
        await ForumAutoMod().age(msg, botmessage)



    @app_commands.command(name="bump")
    async def bump(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        bot = self.bot
        thread: discord.Thread = interaction.channel
        bcheck = datetime.utcnow() + timedelta(hours=-70)
        messages = thread.history(limit=300, after=bcheck, oldest_first=False)
        count = 0

        if thread.owner_id == interaction.user.id:
            async for m in messages:
                if m.author.id == bot.application_id:
                    count += 1
                    if count == 2:
                        lm = m.jump_url
                        pm = m.created_at
                        await interaction.followup.send(
                            f"Your last bump was within the 72 hours cooldown period in {interaction.channel.mention} and was removed."
                            f"\nLast bump: {discord.utils.format_dt(pm, style='f')}timediff: {discord.utils.format_dt(pm, style='R')}")
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




async def setup(bot: commands.Bot):
    await bot.add_cog(forum(bot))