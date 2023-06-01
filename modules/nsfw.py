import json
import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime

import discord
from dateutil.relativedelta import relativedelta
from discord import app_commands
from discord.ext import commands
from sqlalchemy.orm import sessionmaker

import db

Session = sessionmaker(bind=db.engine)
session = Session()

class NSFW(ABC):
    @abstractmethod
    async def check(user, channel):
        count = 0
        with open('config/history.json', 'r') as f:
            history = json.load(f)
        for a in history:
            if count > 5:
                await channel.send("More than 5 messages, search the user for the rest.")
                return
            if history[a]['author'] == user.id:
                await channel.send(f"[Lobby History] {user.mention}({user.id}) `{history[a]['created']}`\n"
                                   f"{history[a]['content']}")
                count += 1
    @abstractmethod
    async def idcheck(user, channel):
        count = 0
        print("checking")
        verification = re.compile(r"\*\*USER ID VERIFICATION\*\*", flags=re.IGNORECASE)
        uuid = re.compile(fr"\b{user.id}\b", flags=re.MULTILINE)
        with open('config/history.json', 'r') as f:
            history = json.load(f)
        for a in history:
            if history[a]['author'] == 987662623187288094:
                vmatch = bool(verification.search(history[a]['content']))
                umatch = bool(uuid.search(history[a]['content']))
                if vmatch is True:
                    if umatch is True:
                        await channel.send(f"[USER ID CHECK]{user.mention} `{history[a]['created']}`\n"
                                       f"{history[a]['content']}")

class AgeCalc(ABC):
    @abstractmethod
    def agechecker(self, arg1, arg2):
        age = arg1
        dob = str(arg2)
        dob_object = datetime.strptime(dob, "%m/%d/%Y")
        today = datetime.now()
        a = relativedelta(today, dob_object)
        age_calculate = a.years - int(age)
        return age_calculate

    def regex(arg2):
        try:
            datetime.strptime(arg2, '%m/%d/%Y')
            dob = str(arg2)
            dob_object = re.search(r"([0-1]?[0-9])/([0-3]?[0-9])/([0-2][0-9][0-9][0-9])", dob)
            month = dob_object.group(1).zfill(2)
            day = dob_object.group(2).zfill(2)
            year = dob_object.group(3)
            fulldob = f"{month}/{day}/{year}"
            return fulldob
        except ValueError:
            return False

    def agecheckfail(arg1):
        bot = commands.Bot
        from datetime import datetime, timedelta
        dob = str(arg1)
        dob_object = datetime.strptime(dob, "%m/%d/%Y")
        today = datetime.now()
        leapyear = ((today - dob_object) / 365.25) / 4
        deltad = leapyear - timedelta(days=1)
        agechecker = ((today - dob_object) - deltad) / 365
        age_output = str(agechecker).split()[0]
        return age_output

    async def removemessage(ctx, bot, user):
        c = session.query(db.config).filter_by(guild=ctx.guild.id).first()
        channel = bot.get_channel(c.lobby)
        messages = channel.history(limit=100)
        count = 0
        async for message in messages:
            if message.author == user or user in message.mentions and count < 10:
                count += 1
                print(message.id)
                await message.delete()

    async def addroles(interaction, guildid, user):
        roles = [432722113456111616]
        for role in roles:
            r = interaction.guild.get_role(role)
            await user.add_roles(r)
        else:
            print("Finished adding")


class dblookup(ABC):

    @abstractmethod
    def dobsave(self, userid: discord.Member, dob):
        exists = session.query(db.user).filter_by(uid=userid.id).first()
        if exists is not None:
            return True
        else:
            try:
                tr = db.user(userid.id, dob)
                session.add(tr)
                session.commit()

            except:
                logging.error("Database error, rolled back")
                session.rollback()
                session.close()
            return False

    @abstractmethod
    async def dobsaveid(self, userid: int, dob):
        exists = session.query(db.user).filter_by(uid=userid).first()
        if exists is not None:
            pass
        else:
            try:
                tr = db.user(userid, dob)
                session.add(tr)
                session.commit()
            except:
                print("Database error, rolled back")
                session.rollback()
                session.close()

    @abstractmethod
    def dobcheck(self, userid: discord.Member, dob):
        exists = session.query(db.user).filter_by(uid=userid.id).first()
        if exists.dob == dob:
            return True
        else:
            return False

    @abstractmethod
    def idcheckchecker(self, userid: discord.Member):
        exists = session.query(db.idcheck).filter_by(uid=userid.id).first()
        if exists is not None:
            if exists.check == True:
                print("idcheck: true")
                return True
            else:
                print("idcheck: False")
                return False
        else:
            return False

    @abstractmethod
    def idcheckeradd(self, userid: int):
        idchecker = session.query(db.idcheck).filter_by(uid=userid).first()
        if idchecker is not None:
            idchecker.check = True
            session.commit()
        else:
            try:
                idcheck = db.idcheck(userid, True)
                session.add(idcheck)
                session.commit()
            except:
                session.rollback()
                session.close()
                logging.exception("failed to  log to database")

    @abstractmethod
    def idcheckerremove(self, userid: int):
        idchecker = session.query(db.idcheck).filter_by(uid=userid).first()
        if idchecker is not None:
            idchecker.check = False
            session.commit()
        else:
            try:
                idcheck = db.idcheck(userid, False)
                session.add(idcheck)
                session.commit()
            except:
                session.rollback()
                session.close()
                logging.exception("failed to  log to database")


class nsfw(commands.GroupCog, name="nsfw"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="submit", description="Submits your age and dob to enter the NSFW section")
    async def submit(self, interaction: discord.Interaction, age: int, dateofbirth: str):
        """Command to let users through the lobby, checks ages and logs them."""
        user = interaction.user
        await interaction.response.defer(ephemeral=True)
        c = session.query(db.config).filter_by(guild=interaction.guild.id).first()
        a = session.query(db.permissions).filter_by(guild=interaction.guild.id).first()
        agelog = 1096571810067251200
        about = "<#1096076040725610556>"
        regdob = AgeCalc.regex(dateofbirth)
        if regdob is False:
            await interaction.followup.send("[DOB ERROR] Please use the mm/dd/yyyy format.")
            return
        bot = self.bot
        channel = bot.get_channel(agelog)
        modchannel = bot.get_channel(1108369258032935062)
        if dblookup.idcheckchecker(self, user) is True:
            embed = discord.Embed(title="Manual ID check",
                                  description=f"user {user.mention} was flagged for manual ID check."
                                              f"\n\n"
                                              f"No roles have been changed.")
            embed.set_footer(text=f"Debug: USERID: {user.id}, AGE: {age} DOB: {regdob}")
            await modchannel.send(f"<@&{a.admin}>", embed=embed)
            await interaction.followup.send("A staff member will contact you shortly.")
        else:
            if AgeCalc.agechecker(self, age, regdob) == 0:
                try:
                    dbl = dblookup.dobsave(self, user, regdob)
                    if dbl is False:
                        await channel.send(f"{user.mention} ({user.id}) has given a new date of birth as none was present in the database.")
                        await NSFW.check(interaction.user, channel)
                        await NSFW.idcheck(interaction.user, channel)
                except:
                    logging.critical(f"Failed to add user to DB: {user.id} {dateofbirth}")
                    await interaction.followup.send(f"[ERROR] error: dbadd. Please open a ticket.")
                if dblookup.dobcheck(self, user, regdob) is True:
                    # Role adding
                    await AgeCalc.addroles(interaction, interaction.guild.id, user)
                    embed = discord.Embed(title=f"{user} successfully verified",
                                          description=f"Age: {age}\n"
                                                      f"Date of birth: {regdob}")
                    embed.set_footer(text=f"USERID: {user.id}")
                    await channel.send(embed=embed)
                    await interaction.followup.send(f"[Success] Welcome to the NSFW section. please read {about}")
                else:
                    u = session.query(db.user).filter_by(uid=user.id).first()

                    embed = discord.Embed(title="Dob Mismatch",
                                          description=f"User {user.mention}\'s dob ({regdob}) does not match a previously given dob ({u.dob}). \n \n To check previously given ages or edit them use: /dblookup or /agefix"
                                                      f"\n\n"
                                                      f"No roles have been changed."
                                          )
                    embed.set_footer(text=f"Debug: USERID: {user.id}, AGE: {age} DOB: {regdob}")
                    await modchannel.send(f"<@&{a.admin}>", embed=embed)
                    await interaction.followup.send("A staff member will contact you shortly.")
            else:

                embed = discord.Embed(title="Age Mismatch",
                                      description=f"User {user.mention}\'s age does not match and has been timed out. User gave {age} but dob indicates {AgeCalc.agecheckfail(regdob)}"
                                                  f"\n\n"
                                                  f"No roles have been changed."
                                      )
                embed.set_footer(text=f"Debug: USERID: {user.id}, AGE: {age} DOB: {regdob}")
                await modchannel.send(f"<@&{a.admin}>", embed=embed)
                await interaction.followup.send("A staff member will contact you shortly.")
        session.close()


async def setup(bot: commands.Bot):
    await bot.add_cog(nsfw(bot))
