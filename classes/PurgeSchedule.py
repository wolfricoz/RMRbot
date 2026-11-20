"""When the yearly search forum purges are announced and run.

A purge date is a day and month that repeats every year; it happens at midnight US/Eastern, the timezone the rest of
the bot uses. The announcement goes out 7 days before. A purge the bot missed because it was offline still runs when it
comes back, for up to 3 days; after that the date waits for next year. These are plain functions of "now" so they can
be checked without Discord or a database.
"""
from datetime import date, datetime, timedelta, timezone

import pytz

TZ = pytz.timezone("US/Eastern")
ANNOUNCE_BEFORE = timedelta(days=7)
CATCH_UP = timedelta(days=3)
# How far back a missed purge is still reported, on the first check after the bot starts.
REPORT_MISSED = timedelta(days=30)


def is_valid_date(day: int, month: int) -> bool:
	"""Whether the day and month exist every year; 29-2 doesn't."""
	try :
		date(2001, month, day)
	except (TypeError, ValueError) :
		return False
	return True


def occurrence(day: int, month: int, year: int) -> datetime:
	"""Midnight US/Eastern on the day, in UTC."""
	return TZ.localize(datetime(year, month, day)).astimezone(timezone.utc)


def next_occurrence(day: int, month: int, now: datetime) -> datetime:
	"""The first purge after now."""
	this_year = occurrence(day, month, now.astimezone(TZ).year)
	return this_year if this_year > now else occurrence(day, month, this_year.astimezone(TZ).year + 1)


def latest_occurrence(day: int, month: int, now: datetime) -> datetime:
	"""The last purge at or before now."""
	this_year = occurrence(day, month, now.astimezone(TZ).year)
	return this_year if this_year <= now else occurrence(day, month, this_year.astimezone(TZ).year - 1)


def as_utc(moment: datetime | None) -> datetime | None:
	"""Timestamps read back without a timezone are UTC, which is how they are stored."""
	if moment is None or moment.tzinfo is not None :
		return moment
	return moment.replace(tzinfo=timezone.utc)


def should_announce(day: int, month: int, announced_at: datetime | None, now: datetime) -> bool:
	"""True once the next purge is 7 days or less away and it hasn't been announced yet."""
	upcoming = next_occurrence(day, month, now)
	if upcoming - now > ANNOUNCE_BEFORE :
		return False
	announced_at = as_utc(announced_at)
	# An announcement from before this window was for an earlier purge.
	return announced_at is None or announced_at < upcoming - ANNOUNCE_BEFORE


def purge_status(day: int, month: int, created_at: datetime | None, last_purged_at: datetime | None,
                 now: datetime) -> str | None:
	"""Returns "due" when the latest purge hasn't run yet, "missed" when it is too late to catch up, else None."""
	latest = latest_occurrence(day, month, now)
	created_at, last_purged_at = as_utc(created_at), as_utc(last_purged_at)
	# Dates added after their day has passed start next year.
	if created_at is not None and latest < created_at :
		return None
	if last_purged_at is not None and last_purged_at >= latest :
		return None
	return "due" if now - latest <= CATCH_UP else "missed"


def discord_time(moment: datetime, style: str) -> str:
	return f"<t:{int(moment.timestamp())}:{style}>"


def announcement_text(when: datetime, forum_mentions: list[str], help_channel_id: int | None) -> str:
	"""The announcement posted 7 days before a purge."""
	forums = ", ".join(forum_mentions) if forum_mentions else "the search forums"
	questions = f"Open a ticket in <#{help_channel_id}>." if help_channel_id else "Open a ticket with the staff team."
	return (
		"@everyone\n"
		f"## 📢 Search forum purge: {discord_time(when, 'F')} ({discord_time(when, 'R')})\n"
		f"All adverts in {forums} will be removed during the scheduled purge.\n\n"
		"**Your advert won't be lost.** The bot will DM you a copy, so make sure you can receive DMs from this server.\n\n"
		"**You can repost straight away** once the purge has finished. Reposted adverts go through approval again, "
		"just like new ones.\n\n"
		"We purge a few times a year to keep the search forums fresh and give everyone an equal chance to be seen. "
		f"Questions? {questions}"
	)


def format_date(day: int, month: int) -> str:
	"""e.g. 1 April."""
	return f"{day} {date(2001, month, day).strftime('%B')}"
