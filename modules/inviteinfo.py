"""Checks the users invite info when they join and logs it"""
from datetime import datetime

import discord
from discord.ext import commands

from classes.databaseController import ConfigData


class inviteInfo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def find_invite_by_code(self, invite_list, code):
        """makes an invite dictionary"""
        for inv in invite_list:
            if inv.code == code:
                return inv

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """reads invite dictionary, and outputs user info"""
        try:
            infochannel = ConfigData().get_key_int(member.guild.id, 'inviteinfo')
        except KeyError:
            infochannel = None
        if infochannel is None:
            return
        invites_before_join = self.bot.invites[member.guild.id]
        invites_after_join = await member.guild.invites()

        for invite in invites_before_join:
            if invite.uses < self.find_invite_by_code(invites_after_join, invite.code).uses:
                embed = discord.Embed(description=f"""Member {member} Joined!
Invite Code: **{invite.code}**
Code created by: {invite.inviter} ({invite.inviter.id})
account created at: {member.created_at.strftime("%m/%d/%Y")}
Member joined at {datetime.now().strftime("%m/%d/%Y")}
""")

                try:
                    embed.set_image(url=member.avatar.url)
                except:

                    pass

                embed.set_footer(text=f"USERID: {member.id}")
                channel = self.bot.get_channel(infochannel)

                await channel.send(embed=embed)

                self.bot.invites[member.guild.id] = invites_after_join

                return

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """removes member's invites"""
        self.bot.invites[member.guild.id] = await member.guild.invites()


async def setup(bot):
    """Adds cog to the bot"""
    await bot.add_cog(inviteInfo(bot))
