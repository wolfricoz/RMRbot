"""The functions in this file are used to log items"""

import logging

from discord.ext import commands

from classes.Support.discord_tools import send_message
from databases.transactions.ConfigData import ConfigData


def get_discord_channel(bot: commands.Bot, channel_id: int):
    """Gets a discord channel."""
    return bot.get_channel(channel_id)


async def automod_log(bot: commands.Bot, guildid, message: str, channel="dev", message_type="Error"):
    """Logs automod actions to a channel; only the Error type is logged as an error."""
    level = logging.ERROR if message_type.lower() == "error" else logging.INFO
    logging.log(level, f"[Automod {message_type}] {message}")
    channel = get_discord_channel(bot, ConfigData().get_key_int(guildid, channel))
    try:
        await send_message(channel, f"[Automod {message_type}] {message}")
    except Exception as e:
        logging.error(e)



