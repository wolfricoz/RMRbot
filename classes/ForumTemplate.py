"""The title rule and header template automod checks new adverts against, per automod forum. Staff can give a forum
its own regexes and removal messages with /config template; a forum without them uses the defaults below.

Config keys, all optional, per forum: HEADER-<forum id> and TITLE-<forum id> (regexes), HEADERMSG-<forum id> and
TITLEMSG-<forum id> (the DM sent when the check fails). Regexes are searched case-insensitively. A header regex with a
named group `age` (e.g. (?P<age>\\d+)) also gets the under-18 alert to the advertmod channel.

Matching uses the `regex` package rather than `re`: `re` can't be stopped and holds the GIL, so a staff regex that
backtracks catastrophically would freeze the whole bot, even in a worker thread. `regex` takes a timeout and releases
the GIL; on a timeout the advert passes and the automodlog channel is told to fix the regex."""
import asyncio
import logging
from dataclasses import dataclass

import regex

import discord

from classes.Support.discord_tools import send_message
from databases.transactions.ConfigData import ConfigData

DEFAULT_HEADER = (r"^\`{0,3}\.?\s*\.?\s*\.?\s*All\s*character'?s?\s*are:?\s*\(?\s*(?P<age>[1-9][0-9])\s*\)?"
                  r"([\S\n\t\v ]*)[-|—]{5,100}")
DEFAULT_HEADER_MESSAGE = """Your advert has been removed because it does not have a header or your header does not follow the template below. Please re-post with a (correct) header.
```text
All characters are (ages)+
(optional) Tags: (Your tags here!)
(optional) Pairings: (Your pairings here!)
(Any other information you want to stand out!)
-----------------------------------
(Your advert here)
```
Common Errors:
* This goes in the body of your post above your advert, not in the title.
* You may have altered 'all characters are', this will cause it to fail as I look for this specifically.
* You may have forgotten the line of dashes (-)
* It is highly recommended to only change the information in the (brackets)
You can use this website to check your header: https://regex101.com/r/HYkkf9/2
This rule went in to effect on the 01/01/2024. If you have any questions, please open a ticket!
"""
DEFAULT_TITLE = r'^[\[\(\{][^\]\)\}]{1,10}[4\/x][^\]\)\}]{1,10}[\]\)\}]'
DEFAULT_TITLE_MESSAGE = """Your advert has been removed because it does not follow our title format. Please re-post with the correct format.
This often errors on:
* You may have forgotten the brackets
* You haven't included the pairings in your title
* You may have included the pairings in the body of your post, not the title

Here is an example of a title that should work:
```text
[pairing/pairing] title here
Example: [m/m] Hi I am looking for a partner
```
If you've looked through the steps above and still have questions, please open a ticket!
"""

# Config key prefix -> default, for each part of a template.
FIELDS = {
	"HEADER"    : DEFAULT_HEADER,
	"HEADERMSG" : DEFAULT_HEADER_MESSAGE,
	"TITLE"     : DEFAULT_TITLE,
	"TITLEMSG"  : DEFAULT_TITLE_MESSAGE,
}
# The config column holds up to 1980 characters.
MAX_LENGTH = 1980
# Seconds a regex may take on one advert.
TIME_LIMIT = 2


class TimedOut :
	"""Returned by ForumTemplate.search when the regex took longer than TIME_LIMIT."""


@dataclass
class ForumTemplate :
	"""The regexes and removal messages one forum's adverts are checked with."""
	header: str
	header_message: str
	title: str
	title_message: str
	# Field name -> whether staff set it for this forum (False: the default).
	custom: dict[str, bool]

	@staticmethod
	def key(field: str, forum_id: int) -> str :
		return f"{field}-{forum_id}"

	@classmethod
	def for_forum(cls, guild_id: int, forum_id: int) -> "ForumTemplate" :
		values = {}
		custom = {}
		for field, default in FIELDS.items() :
			try :
				value = ConfigData().get_key_or_none(guild_id, cls.key(field, forum_id))
			except KeyError :
				# Config not loaded for this guild.
				value = None
			values[field] = value or default
			custom[field] = bool(value)
		return cls(values["HEADER"], values["HEADERMSG"], values["TITLE"], values["TITLEMSG"], custom)

	@staticmethod
	async def search(pattern: str, text: str) -> regex.Match | None | type[TimedOut] :
		"""Case-insensitive search, stopped after TIME_LIMIT seconds. Runs in a worker thread with the GIL released,
		so the bot keeps running meanwhile."""
		try :
			return await asyncio.to_thread(regex.search, pattern, text, regex.IGNORECASE, timeout=TIME_LIMIT,
			                               concurrent=True)
		except TimeoutError :
			return TimedOut

	@staticmethod
	def validate(pattern: str) -> str | None :
		"""Why the pattern isn't a valid regex, or None when it is."""
		try :
			regex.compile(pattern, regex.IGNORECASE)
		except regex.error as e :
			return str(e)
		return None

	@staticmethod
	def age(match: regex.Match) -> int | None :
		"""The age the header's `age` group captured, if the regex has one."""
		if "age" not in match.re.groupindex :
			return None
		age = match.group("age")
		return int(age) if age and age.isnumeric() else None

	@staticmethod
	async def report_timeout(thread: discord.Thread, check: str) :
		"""Tells the automodlog channel a forum's regex took too long, so staff can fix it."""
		message = (f"[Automod Error] The {check} regex of {thread.parent.mention if thread.parent else thread.parent_id} "
		           f"took longer than {TIME_LIMIT} seconds on {thread.jump_url}, so the advert was let through. "
		           f"Please simplify it with /config template.")
		logging.error(message)
		try :
			channel = thread.guild.get_channel(ConfigData().get_key_int(thread.guild.id, "automodlog"))
			await send_message(channel, message)
		except Exception as e :
			logging.error(e)
