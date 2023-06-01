import json
import re
from abc import ABC
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands

import adefs
import jsonmaker


# from main import channels24

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


class forum(commands.GroupCog, name="forum"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        with open(f'jsons/{thread.guild.id}.json') as f:
            data = json.load(f)
        forums = data['forums']
        bot = self.bot
        forum = bot.get_channel(thread.parent_id)
        tag = None
        msg: discord.Message = await thread.fetch_message(thread.id)
        matched = await ForumAutoMod.tags(self, thread, forum, msg)
        if forum.id in forums:
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
            await ForumAutoMod().age(msg, botmessage)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.channel.type is discord.ChannelType.text:
            return
        with open(f'jsons/{message.guild.id}.json') as f:
            data = json.load(f)
        forums = data['forums']
        content = message.content
        dobreg = re.compile(r"bump|bumping", flags=re.IGNORECASE)
        match = dobreg.search(message.content)
        try:
            thread: discord.Thread = message.guild.get_thread(message.channel.id)
            forum: discord.ForumChannel = self.bot.get_channel(thread.parent_id)
        except:
            return

        if message.channel.type is discord.ChannelType.public_thread:
            if forum.id in forums:
                if match:
                    bot = self.bot
                    modchannel = bot.get_channel(763058339088957548)
                    thread: discord.Thread = message.channel
                    bcheck = datetime.utcnow() + timedelta(hours=-70)
                    messages = thread.history(limit=300, after=bcheck, oldest_first=False)
                    forum = bot.get_channel(thread.parent_id)
                    count = 0
                    if thread.owner_id == message.author.id:
                        async for m in messages:
                            if m.author.id == bot.application_id:
                                count += 1
                                if count == 2:
                                    lm = m.jump_url
                                    pm = m.created_at
                                    await message.author.send(
                                        f"Your last bump was within the 72 hours cooldown period in {message.channel.mention} and was removed."
                                        f"\nLast bump: {discord.utils.format_dt(pm, style='f')}timediff: {discord.utils.format_dt(pm, style='R')}"
                                        f"\nRepeated early bumps will result in your advert being taken down.")
                                    await message.delete()
                                    await modchannel.send(
                                        f"{message.author.mention} tried to bump within the 72 hours cooldown period in {message.channel.mention}."
                                        f"\nLast bump: {discord.utils.format_dt(pm, style='f')}timediff: {discord.utils.format_dt(pm, style='R')}")
                                    return

                        if message.channel.type == discord.ChannelType.public_thread:
                            for a in forum.available_tags:
                                if a.name == "Bump":
                                    await thread.add_tags(a)
                                    await message.channel.send("Post successfully bumped")
                                if a.name == "Approved":
                                    await thread.remove_tags(a)

                    else:
                        await message.channel.send(f"{message.author} You can't bump another's post.")


    @app_commands.command(name="bump", description="Bumps your post!")
    async def bump(self, interaction: discord.Interaction):
        with open(f'jsons/{interaction.guild.id}.json') as f:
            data = json.load(f)
        forums = data['forums']
        thread: discord.Thread = interaction.guild.get_thread(interaction.channel.id)
        forum: discord.ForumChannel = self.bot.get_channel(thread.parent_id)
        print(forum.id)
        print(forums)
        if forum.id in forums:
            await interaction.response.defer(ephemeral=True)
            await ForumAutoMod.bump(self, interaction)
        else:
            print('not in list')

    @app_commands.command(name="close", description="Removes your post from the forum and sends you a copy.")
    async def close(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        bot = self.bot
        thread: discord.Thread = interaction.channel
        count = 0
        # modchannel = bot.get_channel(763058339088957548)
        if interaction.channel.type == discord.ChannelType.public_thread:
            if thread.owner_id == interaction.user.id:
                async for m in thread.history(limit=1, oldest_first=True):
                    await interaction.user.send(f"{m.channel}"
                                                f"\n{m.content}"
                                                f"\n\nYour post has successfully been closed.")
                await thread.delete()
            else:
                await interaction.followup.send("[ERROR] You do not own this thread.")
        else:
            await interaction.followup.send("[ERROR] This channel is not a thread.")

    @app_commands.command(name="add", description="ADMIN: adds forum to the list to be moderated")
    @adefs.check_slash_admin_roles()
    async def add(self, interaction: discord.Interaction, forum: discord.ForumChannel) -> None:
        await interaction.response.defer(ephemeral=True)
        await jsonmaker.guildconfiger.addforum(interaction.guild.id, interaction, forum.id, 'forums')

    @app_commands.command(name="remove", description="ADMIN: removes forum to the list to be moderated")
    @adefs.check_slash_admin_roles()
    async def remove(self, interaction: discord.Interaction, forum: discord.ForumChannel) -> None:
        await interaction.response.defer(ephemeral=True)
        await jsonmaker.guildconfiger.remforum(interaction.guild.id, forum.id, 'forums')
        await interaction.followup.send("Successfully removed the forum")


async def setup(bot: commands.Bot):
    await bot.add_cog(forum(bot))
