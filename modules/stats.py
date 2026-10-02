"""Admin statistics with charts: interest messages, adverts, moderator approvals and website cross-posting."""
import asyncio
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from typing import Iterable

import discord
from discord import app_commands
from discord.ext import commands

import classes.Charts as Charts
import classes.permissions as permissions
from classes.automod import AutoMod
from databases.transactions.AdvertisementTransactions import AdvertisementTransactions
from databases.transactions.ApprovalTransactions import ApprovalTransactions
from databases.transactions.InterestTransactions import InterestTransactions

Days = app_commands.Range[int, 1, 365]


class Stats(commands.GroupCog, name="stats") :
	"""Admin only. Replies are ephemeral: some charts name members."""

	def __init__(self, bot: commands.Bot) :
		self.bot = bot

	@app_commands.command(name="interests", description="ADMIN: interest messages sent to advert authors")
	@app_commands.guild_only()
	@permissions.check_app_roles_admin()
	async def interests(self, interaction: discord.Interaction, days: Days = 30) :
		await interaction.response.defer(ephemeral=True)
		records = InterestTransactions().get_since(interaction.guild.id, days)
		if not records :
			await interaction.followup.send(f"No interest messages in the last {days} days.", ephemeral=True)
			return
		delivered = [r for r in records if r.delivered]
		reported = [r for r in records if r.reported_at is not None]
		day_list = _days(days)
		chart = await asyncio.to_thread(
			Charts.daily, f"Interest messages, last {days} days", day_list,
			{
				"Delivered"  : _per_day(day_list, (r.created_at for r in delivered)),
				"DMs closed" : _per_day(day_list, (r.created_at for r in records if not r.delivered)),
			},
			"interests.png",
		)
		embed = discord.Embed(
			title=f"Interest messages: last {days} days",
			description=f"**{len(records)}** sent · **{len(delivered)}** delivered ({_percent(len(delivered), len(records))}) · "
			            f"**{len(records) - len(delivered)}** to closed DMs · **{len(reported)}** reported",
			color=discord.Color.blurple(),
		)
		embed.add_field(name="Most contacted adverts", value=_top(Counter(r.thread_id for r in records), "<#{}>"))
		embed.add_field(name="Most active senders", value=_top(Counter(r.sender_id for r in records), "<@{}>"))
		embed.set_image(url=f"attachment://{chart.filename}")
		await interaction.followup.send(embed=embed, file=chart, ephemeral=True)

	@app_commands.command(name="adverts", description="ADMIN: adverts posted in the search forums")
	@app_commands.guild_only()
	@permissions.check_app_roles_admin()
	async def adverts(self, interaction: discord.Interaction, days: Days = 30) :
		await interaction.response.defer(ephemeral=True)
		since = datetime.now(timezone.utc) - timedelta(days=days)
		forums = AutoMod.config(interaction.guild.id)
		# An advert's id is its message's snowflake, which holds when it was posted.
		posted = [a for a in AdvertisementTransactions().get_by_forums(forums)
		          if discord.utils.snowflake_time(a.id) >= since]
		if not posted :
			await interaction.followup.send(f"No adverts posted in the last {days} days.", ephemeral=True)
			return
		day_list = _days(days)
		by_forum = {}
		for forum_id in forums :
			in_forum = [a for a in posted if a.forum_id == forum_id]
			if in_forum :
				by_forum[_channel_name(interaction.guild, forum_id)] = _per_day(
					day_list, (discord.utils.snowflake_time(a.id) for a in in_forum))
		chart = await asyncio.to_thread(Charts.daily, f"Adverts posted, last {days} days", day_list, by_forum, "adverts.png")
		removed = sum(1 for a in posted if a.deleted is not None)
		bumps = sum(1 for a in ApprovalTransactions().get_by_guild(interaction.guild.id, days) if a.uid == self.bot.user.id)
		embed = discord.Embed(
			title=f"Adverts: last {days} days",
			description=f"**{len(posted)}** posted · **{len(posted) - removed}** still up · **{removed}** removed · "
			            f"**{bumps}** auto-approved bumps",
			color=discord.Color.blurple(),
		)
		per_forum = Counter(a.forum_id for a in posted)
		embed.add_field(name="Per forum", value="\n".join(f"<#{forum}>: {count}" for forum, count in per_forum.most_common()))
		embed.set_footer(text="Counts the adverts the bot has a record of (posted since the website cross-posting, or "
		                      "found by its hourly check).")
		embed.set_image(url=f"attachment://{chart.filename}")
		await interaction.followup.send(embed=embed, file=chart, ephemeral=True)

	@app_commands.command(name="approvals", description="ADMIN: advert approvals over time and per moderator")
	@app_commands.guild_only()
	@permissions.check_app_roles_admin()
	async def approvals(self, interaction: discord.Interaction, days: Days = 30) :
		await interaction.response.defer(ephemeral=True)
		records = ApprovalTransactions().get_by_guild(interaction.guild.id, days)
		if not records :
			await interaction.followup.send(f"No approvals in the last {days} days.", ephemeral=True)
			return
		# Auto-approved bumps are logged with the bot as approver.
		by_moderators = [r for r in records if r.uid != self.bot.user.id]
		auto = [r for r in records if r.uid == self.bot.user.id]
		day_list = _days(days)
		over_time = await asyncio.to_thread(
			Charts.daily, f"Approvals, last {days} days", day_list,
			{
				"By moderators"       : _per_day(day_list, (r.created_at for r in by_moderators)),
				"Auto-approved bumps" : _per_day(day_list, (r.created_at for r in auto)),
			},
			"approvals.png",
		)
		embed = discord.Embed(
			title=f"Approvals: last {days} days",
			description=f"**{len(by_moderators)}** by moderators · **{len(auto)}** auto-approved bumps",
			color=discord.Color.green(),
		)
		embed.set_image(url=f"attachment://{over_time.filename}")
		embeds, files = [embed], [over_time]
		top = Counter(r.uid for r in by_moderators).most_common(10)
		if top :
			per_moderator = await asyncio.to_thread(
				Charts.ranking, f"Approvals per moderator, last {days} days",
				[_member_name(interaction.guild, uid) for uid, _ in top], [count for _, count in top],
				"moderators.png",
			)
			embeds.append(discord.Embed(color=discord.Color.green()).set_image(url=f"attachment://{per_moderator.filename}"))
			files.append(per_moderator)
		await interaction.followup.send(embeds=embeds, files=files, ephemeral=True)

	@app_commands.command(name="website", description="ADMIN: adverts cross-posted to the website")
	@app_commands.guild_only()
	@permissions.check_app_roles_admin()
	async def website(self, interaction: discord.Interaction, days: Days = 30) :
		await interaction.response.defer(ephemeral=True)
		since = datetime.now(timezone.utc) - timedelta(days=days)
		adverts = AdvertisementTransactions().get_by_forums(AutoMod.config(interaction.guild.id))
		if not adverts :
			await interaction.followup.send("The bot has no adverts on record yet.", ephemeral=True)
			return
		up = [a for a in adverts if a.deleted is None]
		consented = [a for a in up if a.consent_at is not None]
		published = [a for a in up if a.published_at is not None]
		waiting = [a for a in consented if a.published_at is None]
		removed = [a for a in adverts if a.deleted is not None and a.published_at is not None and _utc(a.deleted) >= since]
		day_list = _days(days)
		chart = await asyncio.to_thread(
			Charts.daily, f"Website cross-posting, last {days} days", day_list,
			{
				"Consent given" : _per_day(day_list, (a.consent_at for a in adverts if a.consent_at is not None)),
				"Published"     : _per_day(day_list, (a.published_at for a in adverts if a.published_at is not None)),
			},
			"website.png", False,
		)
		embed = discord.Embed(title="Website cross-posting", color=discord.Color.blurple())
		embed.add_field(
			name="Adverts up now",
			value=f"**{len(up)}** adverts\n"
			      f"**{len(consented)}** gave consent ({_percent(len(consented), len(up))})\n"
			      f"**{len(published)}** on the website\n"
			      f"**{len(waiting)}** waiting for approval\n"
			      f"**{len(up) - len(consented)}** haven't answered",
		)
		embed.add_field(name=f"Last {days} days", value=f"**{len(removed)}** removed from the website")
		embed.set_image(url=f"attachment://{chart.filename}")
		await interaction.followup.send(embed=embed, file=chart, ephemeral=True)


def _days(days: int) -> list[date] :
	"""The last days, oldest first, ending today (UTC)."""
	today = datetime.now(timezone.utc).date()
	return [today - timedelta(days=offset) for offset in range(days - 1, -1, -1)]


def _per_day(day_list: list[date], moments: Iterable[datetime]) -> list[int] :
	counts = Counter(_utc(moment).date() for moment in moments)
	return [counts.get(day, 0) for day in day_list]


def _utc(moment: datetime) -> datetime :
	"""MariaDB returns timestamps without a timezone; like the rest of the bot, they are treated as UTC."""
	return moment.replace(tzinfo=timezone.utc) if moment.tzinfo is None else moment.astimezone(timezone.utc)


def _percent(part: int, whole: int) -> str :
	return f"{part / whole:.0%}" if whole else "0%"


def _top(counts: Counter, mention: str, limit: int = 5) -> str :
	return "\n".join(f"{mention.format(key)}: {count}" for key, count in counts.most_common(limit)) or "None"


def _channel_name(guild: discord.Guild, channel_id: int) -> str :
	channel = guild.get_channel(channel_id)
	return channel.name if channel else str(channel_id)


def _member_name(guild: discord.Guild, user_id: int) -> str :
	member = guild.get_member(user_id)
	return member.display_name if member else str(user_id)


async def setup(bot: commands.Bot) :
	await bot.add_cog(Stats(bot))
