"""This cog is meant for every warning related command"""
import re
from io import BytesIO

import certifi
import discord
import pycurl
from discord import app_commands
from discord.ext import commands

import classes.automod as automod
import classes.permissions as permissions
from classes.Support.discord_tools import send_response


# the base for a cog.
class Utility(commands.Cog) :
	def __init__(self, bot) :
		self.bot = bot

	@app_commands.command(name="giveawayusers")
	@permissions.check_app_roles()
	async def forumusers(self, interaction: discord.Interaction) :
		"""Get a list of forum users"""
		forums = automod.AutoMod.config(interaction.guild.id)
		users = []
		for x in forums :
			forum: discord.ForumChannel = interaction.guild.get_channel(int(x))
			if forum is None :
				print(f"Forum channel {x} not found.")
				continue
			if not isinstance(forum, discord.ForumChannel) :
				print(f"Channel {x} is not a forum channel. it is a {forum.type}")
				continue
			print(f"Forum: {forum.name}")
			for thread in forum.threads :
				try :
					if thread.owner.name not in users :
						users.append(thread.owner.name)
				except AttributeError :
					await interaction.channel.send(f"Thread has no owner: {thread.jump_url} in {forum.name}")
		rmrwebsite = BytesIO()
		c = pycurl.Curl()
		c.setopt(c.URL, "https://roleplaymeets.com/api/getpostsusernames")
		c.setopt(c.WRITEDATA, rmrwebsite)
		c.setopt(c.CAINFO, certifi.where())
		c.perform()
		c.close()
		rmrwebsite = rmrwebsite.getvalue().decode("utf-8").replace('[', "").replace(']', "").replace('"', "").split(',')
		with open("forumusers.txt", "w") as f :
			f.write("Forum users: \n")
			f.write("\n".join([x for x in users]))
			f.write("\n\nRoleplay Meets Website Users: \n")
			f.write("\n".join([x for x in rmrwebsite]))

		await interaction.response.send_message(f"Here are all users in the forums:", file=discord.File("forumusers.txt"))

	# @app_commands.command(name="archive_all")
	# async def forumarchive(self, interaction: discord.Interaction) :
	# 	await send_response(interaction, "starting the forum manager! The forum will be cleaned.")
	# 	archived_thread: discord.Thread
	# 	channel: discord.ForumChannel
	# 	regex = re.compile(f"search", flags=re.IGNORECASE)
	# 	channels = [
	# 		channel
	# 		for guild in self.bot.guilds
	# 		for channel in guild.channels
	# 		if channel.type == discord.ChannelType.forum and regex.search(channel.name)
	# 	]
	# 	for forum in channels :
	# 		for thread in forum.threads :
	# 			print(f"archiving {thread.name}")
	# 			await thread.edit(archived=True)
	# 			print(thread.archived)
	# 			print(thread.archive_timestamp)


async def setup(bot) :
	"""Sets up the cog"""
	await bot.add_cog(Utility(bot))
