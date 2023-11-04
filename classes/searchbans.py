import logging

import discord

from classes.databaseController import TimersTransactions


async def remove(member: discord.Member, role, timer):
    """removes role from user and removes timer"""
    await member.remove_roles(role)
    TimersTransactions.remove_timer(timer)
    logging.debug(f"Removed searchban from {member.name}")
