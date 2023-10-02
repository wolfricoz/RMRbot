from datetime import datetime

import discord
from discord.ext import commands

from classes.databaseController import ConfigTransactions


# the base for a cog.
class inviteInfo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Your first app command!
    def find_invite_by_code(self, invite_list, code):
        # makes an invite dictionary
        for inv in invite_list:
            if inv.code == code:
                return inv

    # this has to become its own cog, rewrite to become dynamic.
    @commands.Cog.listener()
    async def on_member_join(self, member):
        # reads invite dictionary, and outputs user info
        infochannel = ConfigTransactions.config_unique_get(member.guild.id, 'inviteinfo')
        if infochannel is None:
            return
        invites_before_join = self.bot.invites[member.guild.id]
        invites_after_join = await member.guild.invites()

        for invite in invites_before_join:
            if invite.uses < self.find_invite_by_code(invites_after_join, invite.code).uses:
                embed = discord.Embed(description=f"""Member {member} Joined
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
                channel = self.bot.get_channel(1155647574288642060)
                await channel.send(embed=embed)

                self.bot.invites[member.guild.id] = invites_after_join

                return

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        self.bot.invites[member.guild.id] = await member.guild.invites()


async def setup(bot):
    await bot.add_cog(inviteInfo(bot))
