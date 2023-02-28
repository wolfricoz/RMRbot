import logging

from discord.ext import commands
import db
from sqlalchemy.orm import sessionmaker
import re

Session = sessionmaker(bind=db.engine)
session = Session()


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # Enforces lobby format
        bot = self.bot
        dobreg = re.compile(r"([0-9][0-9]) (1[0-2]|0?[0-9]|1)/([0-3]?[0-9])/([0-2][0-9][0-9][0-9])")
        match = dobreg.search(message.content)
        if message.guild is None:
            return
        if message.author.bot:
            return
        # Searches the config for the lobby for a specific guild
        p = session.query(db.permissions).filter_by(guild=message.guild.id).first()
        c = session.query(db.config).filter_by(guild=message.guild.id).first()
        # Checks if user is a staff member.
        if message.author.get_role(p.mod) is None and message.author.get_role(
                p.admin) is None and message.author.get_role(p.trial) is None:
            # Checks if channel is the lobby
            if message.channel.id == c.lobby:
                # Checks if message matches the regex
                if match:
                    waitmessage = f"{message.author.mention} Thank you for submitting your age! " \
                                  f"One of our staff members will let you through into the main server once they are available. " \
                                  f"Please be patient, as our lobby is handled manually."
                    channel = bot.get_channel(c.modlobby)
                    lobby = bot.get_channel(c.lobby)
                    await message.add_reaction("🤖")
                    # Checks the ages in the message, and acts based upon it.
                    if int(match.group(1)) < 18:
                        await channel.send(
                            f"<@&{p.lobbystaff}> {message.author.mention} has given an age under the age of 18: {message.content} (User has been added to ID list)")
                        idchecker = session.query(db.idcheck).filter_by(uid=message.author.id).first()
                        if idchecker is not None:
                            idchecker.check = True
                            session.commit()
                        else:
                            try:
                                idcheck = db.idcheck(message.author.id, True)
                                session.add(idcheck)
                                session.commit()
                            except:
                                session.rollback()
                                session.close()
                                logging.exception("failed to  log to database")
                    if int(match.group(1)) >= 18 and not int(match.group(1)) > 20:
                        await channel.send(
                            f"<@&{p.lobbystaff}> user has given age. You can let them through with `?18a {message.author.mention} {message.content}`")
                        await lobby.send(waitmessage)
                    elif int(match.group(1)) >= 21 and not int(match.group(1)) > 24:
                        await channel.send(
                            f"<@&{p.lobbystaff}> user has given age. You can let them through with `?21a {message.author.mention} {message.content}`")
                        await lobby.send(waitmessage)
                    elif int(match.group(1)) >= 25:
                        await channel.send(
                            f"<@&{p.lobbystaff}> user has given age. You can let them through with `?25a {message.author.mention} {message.content}`")
                        await lobby.send(waitmessage)
                    return
                else:
                    channel = bot.get_channel(c.modlobby)
                    await channel.send(f"{message.author.mention} failed to follow the format: {message.content}")
                    await message.channel.send(
                        f"{message.author.mention} Please use format age mm/dd/yyyy "
                        f"\n Example: `122 01/01/1900` "
                        f"\n __**Do not round up your age**__ ")
                    await message.delete()
                    return
        else:
            pass

async def setup(bot):
    await bot.add_cog(Events(bot))