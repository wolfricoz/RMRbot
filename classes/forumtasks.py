import discord


class ForumTasks():

	def __init__(self, forum: discord.ForumChannel):
		# setting up the data all the underlying functions need to reduce api calls.
		self.forum = forum
		self.threads = forum.threads
		self.archived = forum.archived_threads(limit=None)
		self.members = [member.id for member in forum.guild.members]

	async def start(self):
		"""This starts the checking of the forum and will walk through all the tasks."""
		async for archived_thread in self.archived:
			pass

	async def recover_archived_posts(self):
		raise NotImplemented

	async def check_status_tag(self):
		raise NotImplemented

	async def cleanup_forum(self):
		raise NotImplemented

	async def check_user(self):
		raise NotImplemented

	async def check_post(self):
		raise NotImplemented
