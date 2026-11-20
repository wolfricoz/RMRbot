"""Modals for /config template: setting a forum's title and header template, and testing an advert against it."""
import logging

import discord

from classes.ForumTemplate import FIELDS, MAX_LENGTH, ForumTemplate, TimedOut
from databases.transactions.ConfigTransactions import ConfigTransactions


async def _report_error(interaction: discord.Interaction, error: Exception, what: str) :
	logging.error(f"{what} failed: {error}", exc_info=error)
	if interaction.response.is_done() :
		await interaction.followup.send("Oops! Something went wrong.", ephemeral=True)
		return
	await interaction.response.send_message("Oops! Something went wrong.", ephemeral=True)


class ForumTemplateModal(discord.ui.Modal, title="Forum template") :
	"""Edits one forum's template; a field left blank or at the default follows the default."""

	def __init__(self, forum: discord.ForumChannel) :
		super().__init__(timeout=None)
		self.forum = forum
		template = ForumTemplate.for_forum(forum.guild.id, forum.id)
		self.header = discord.ui.TextInput(label="Header regex", style=discord.TextStyle.long, required=False,
		                                   default=template.header, max_length=MAX_LENGTH)
		self.header_message = discord.ui.TextInput(label="Message when the header is wrong",
		                                           style=discord.TextStyle.long, required=False,
		                                           default=template.header_message, max_length=MAX_LENGTH)
		self.title_regex = discord.ui.TextInput(label="Title regex (.* allows any title)", style=discord.TextStyle.long,
		                                        required=False, default=template.title, max_length=MAX_LENGTH)
		self.title_message = discord.ui.TextInput(label="Message when the title is wrong",
		                                          style=discord.TextStyle.long, required=False,
		                                          default=template.title_message, max_length=MAX_LENGTH)
		for item in (self.header, self.header_message, self.title_regex, self.title_message) :
			self.add_item(item)

	async def on_submit(self, interaction: discord.Interaction) :
		values = {
			"HEADER"    : self.header.value.strip(),
			"HEADERMSG" : self.header_message.value.strip(),
			"TITLE"     : self.title_regex.value.strip(),
			"TITLEMSG"  : self.title_message.value.strip(),
		}
		# Checks every regex before saving anything, so a typo doesn't leave the template half changed.
		for field, label in (("HEADER", "header"), ("TITLE", "title")) :
			if not values[field] :
				continue
			error = ForumTemplate.validate(values[field])
			if error is not None :
				await interaction.response.send_message(
					f"The {label} regex is invalid ({error}); nothing was saved.\n```\n{values[field][:1800]}\n```",
					ephemeral=True)
				return
		changed = []
		for field, value in values.items() :
			key = ForumTemplate.key(field, self.forum.id)
			if not value or value == FIELDS[field].strip() :
				ConfigTransactions().config_unique_remove(interaction.guild.id, key)
				continue
			ConfigTransactions().config_unique_add(interaction.guild.id, key, value, overwrite=True)
			changed.append(field.lower())
		custom = ", ".join(changed) if changed else "none (all defaults)"
		await interaction.response.send_message(
			f"Template for {self.forum.mention} saved. Custom parts: {custom}.\n"
			f"Check it with `/config template forum:{self.forum.name} action:test`.",
			ephemeral=True)

	async def on_error(self, interaction: discord.Interaction, error: Exception) -> None :
		await _report_error(interaction, error, f"Template modal for {self.forum.id}")


class ForumTemplateTestModal(discord.ui.Modal, title="Test an advert") :
	"""Checks a sample advert against a forum's template without posting or removing anything."""

	advert_title = discord.ui.TextInput(label="Thread title", style=discord.TextStyle.short, max_length=100)
	advert = discord.ui.TextInput(label="Advert", style=discord.TextStyle.long, max_length=4000)

	def __init__(self, forum: discord.ForumChannel) :
		super().__init__(timeout=None)
		self.forum = forum

	async def on_submit(self, interaction: discord.Interaction) :
		template = ForumTemplate.for_forum(interaction.guild.id, self.forum.id)
		title = await ForumTemplate.search(template.title, self.advert_title.value)
		header = await ForumTemplate.search(template.header, self.advert.value)
		lines = [f"Results for {self.forum.mention}:",
		         f"Title: {self._result(title)}",
		         f"Header: {self._result(header)}"]
		if header not in (None, TimedOut) :
			age = ForumTemplate.age(header)
			if age is not None :
				lines.append(f"Characters' age: {age}{' (under 18: staff would be alerted)' if age < 18 else ''}")
			elif "age" not in header.re.groupindex :
				lines.append("The header regex has no `(?P<age>...)` group, so ages aren't checked.")
		await interaction.response.send_message("\n".join(lines), ephemeral=True)

	@staticmethod
	def _result(match) -> str :
		if match is TimedOut :
			return "regex took too long (the advert would be let through and staff told)"
		return "pass" if match is not None else "fail (the advert would be removed)"

	async def on_error(self, interaction: discord.Interaction, error: Exception) -> None :
		await _report_error(interaction, error, f"Template test modal for {self.forum.id}")
