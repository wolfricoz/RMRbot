from discord.ext.commands import Cog, GroupCog, Bot


class Website(GroupCog) :

	def __init__(self, bot: Bot) :
		self.bot = bot

	# The listeners are in forum.py - integrated with existing logic.


async def setup(bot: Bot) :
	await bot.add_cog(
		Website(bot),
	)
