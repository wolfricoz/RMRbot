"""The functions in this file are used to log items"""

import logging

from discord.ext import commands

from classes.databaseController import ConfigData


def get_discord_channel(bot: commands.Bot, channel_id: int):
    """Gets a discord channel."""
    return bot.get_channel(channel_id)


async def automod_log(bot: commands.Bot, guildid, message: str, channel="dev"):
    """Logs automod failures to a channel."""
    logging.error(f"[Automod Error] {message}")
    channel = get_discord_channel(bot, ConfigData().get_key_int(guildid, channel))
    try:
        await channel.send(f"[Automod Error] {message}")
    except Exception as e:
        logging.error(e)


async def automod_approval_log(bot: commands.Bot, guildid, message: str, channel="dev"):
    """Logs automod approvals to a channel."""
    logging.info(f"[Automod Approval] {message}")
    channel = get_discord_channel(bot, ConfigData().get_key_int(guildid, channel))
    try:
        await channel.send(f"[Automod Approval] {message}")
    except Exception as e:
        logging.error(e)
