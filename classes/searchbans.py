import logging
from datetime import datetime, timedelta

import discord
import pytz

from classes.databaseController import ConfigData, TimersTransactions

def get_cooldown_time(count) -> int:
    cooldowns = {
        3: 24,
        6: 24*7,
        9: 24*30,
        12: 24*60,
    }
    return cooldowns.get(count, 0)


async def remove(member: discord.Member, role, timer):
    """removes role from user and removes timer"""
    await member.remove_roles(role)
    TimersTransactions.remove_timer(timer)
    logging.debug(f"Removed searchban from {member.name}")

async def add_search_ban(member: discord.Member, guild, reason: str, removal_time: int):
    """Adds a search ban to a member and starts a timer"""
    role_id = ConfigData().get_key_int(guild.id, 'posttimeout')
    search_ban_role = guild.get_role(role_id)
    await member.add_roles(search_ban_role)
    TimersTransactions.add_timer(member.id, guild.id, reason, removal_time)
    logging.debug(f"Added searchban to {member.name}")

async def warning_count_check(interaction, member: discord.Member, guild, count: int):
    """Checks if a user has reached the warning count and adds a search ban if they have"""
    tz = pytz.timezone("US/Eastern")
    cooldown_time = get_cooldown_time(count)
    if cooldown_time == 0:
        # No cooldown needed
        return
    cooldown = datetime.now(tz=tz) + timedelta(hours=cooldown_time)
    reason = f"{interaction.guild.name} **__SEARCH BAN__**: Hello, I'm a staff member from RMR. Due to your frequent refusal to follow our search rules concerning ads, your ad posting privileges have been revoked and you've been given a search ban of {cooldown_time / 24} day(s). Please use this time to thoroughly review RMR's rules. Continued refusal to follow the server's search rules can result in a permanent search ban.\n\n This search ban expires on:\n {cooldown.strftime('%m/%d/%Y')}"
    await member.send(reason)
    await add_search_ban(member, guild, reason, cooldown_time)
