"""The functions in this file are used to log items"""

import logging

from discord.ext import commands

from classes.Support.discord_tools import send_message
from classes.databaseController import ConfigData


def get_discord_channel(bot: commands.Bot, channel_id: int):
    """Gets a discord channel."""
    return bot.get_channel(channel_id)


async def automod_log(bot: commands.Bot, guildid, message: str, channel="dev", message_type="Error"):
    """Logs automod failures to a channel."""
    logging.error(f"[Automod {message_type}] {message}")
    channel = get_discord_channel(bot, ConfigData().get_key_int(guildid, channel))
    try:
        await send_message(channel, f"[Automod {message_type}] {message}")
    except Exception as e:
        logging.error(e)



