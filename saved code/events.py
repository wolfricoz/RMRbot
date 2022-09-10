import discord
from discord import client
from discord.ext import commands
#from main import channels24

class events(commands.Cog, name="events"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def advertposted(self, message):
        bot = self.bot
        print(message)



def setup(bot: commands.Bot):
    bot.add_cog(events(bot))