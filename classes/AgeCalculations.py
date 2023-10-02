import re
from abc import ABC, abstractmethod
from datetime import datetime

import discord
from dateutil.relativedelta import relativedelta

import databases.current
from classes.databaseController import *

class AgeCalculations(ABC):


    @staticmethod
    @abstractmethod
    def check_date_of_birth(userdata, dob):
        if userdata is None or userdata.dob is None:
            print("None found")
            return True
        return userdata.dob.strftime("%m/%d/%Y") == dob
    @staticmethod
    @abstractmethod
    async def check_history(user, channel):
        count = 0
        hf = []
        with open('config/history.json', 'r') as f:
            history = json.load(f)
        for a in history:
            if count > 5:
                await channel.send(f"{user.mention} More than 5 messages, search the user for the rest.")
                break
            if history[a]['author'] == user.id:
                hf.append(f"{user.mention}({user.id}) Posted at: `{history[a]['created']}`\n"
                          f"{history[a]['content']}")
                count += 1
        if count > 0:
            lh = "\n".join(hf)
            await channel.send(f"```[Lobby History]``` {lh}")

    @staticmethod
    @abstractmethod
    async def id_check_or_id_verified(user: discord.Member, channel):
        userinfo: databases.current.IdVerification = UserTransactions.get_user_id_info(user.id)
        if userinfo is None:
            print("user info none")
            return False
        if userinfo.idverified is True and userinfo.verifieddob is not None:
            print("ID found")
            await channel.send(f"{user.mention} has previously ID verified: {userinfo.verifieddob.strftime('%m/%d/%Y')}")
            return False
        if userinfo.idcheck is True:
            print("id check")
            await channel.send(
                f"{user.mention} is on the ID list with reason: {userinfo.reason}. Please ID the user before letting them through.")
            return True
        print("None of the above")
        return False




    @staticmethod
    @abstractmethod
    async def infocheck(interaction, age, dateofbirth, channel):
        agevalid = re.match(r'[0-9]*$', age)
        if agevalid is None:
            await interaction.response.send_message('Please fill in your age in numbers.', ephemeral=True)
            await channel.send(
                    f"{interaction.user.mention} failed in verification at age: {age} {dateofbirth}")
            return False
        redob = r"(((0[0-9])|(1[012]))([\/|\-|.])((0[1-9])|([12][0-9])|(3[01]))([\/|\-|.])((20[012]\d|19\d\d)|(1\d|2[0123])))"
        dobvalid = re.match(redob, dateofbirth)
        if dobvalid is None:
            await interaction.response.send_message(
                    'Please fill in your date of birth as with the format: mm/dd/yyyy.', ephemeral=True)
            await channel.send(
                    f"{interaction.user.mention} failed in verification at date of birth: {age} {dateofbirth}")
            return False
        return True

    @staticmethod
    @abstractmethod
    def agechecker(age: int, date_of_birth: str):
        dob = str(date_of_birth)
        dob_object = datetime.strptime(dob, "%m/%d/%Y")
        a = relativedelta(datetime.now(), dob_object)
        age_calculate = a.years - int(age)
        return age_calculate, a.years

    @staticmethod
    @abstractmethod
    def regex(arg2):
        dob = str(arg2)
        dob_object = re.search(r"([0-1]?[0-9])/([0-3]?[0-9])/([0-2][0-9][0-9][0-9])", dob)
        month = dob_object.group(1).zfill(2)
        day = dob_object.group(2).zfill(2)
        year = dob_object.group(3)
        fulldob = f"{month}/{day}/{year}"
        return fulldob

    @staticmethod
    @abstractmethod
    async def removemessage(ctx, bot, user):
        c = session.query(db.config).filter_by(guild=ctx.guild.id).first()
        channel = bot.get_channel(c.lobby)
        messages = channel.history(limit=100)
        format = re.compile(r"failed to follow the format", flags=re.MULTILINE)
        notify = re.compile(r"has been notified", flags=re.MULTILINE)
        count = 0
        async for message in messages:
            if message.author == user or user in message.mentions and count < 10:
                count += 1
                await message.delete()
        channel = bot.get_channel(c.modlobby)
        messages = channel.history(limit=100)
        count = 0
        async for message in messages:
            if user in message.mentions and count < 5:
                if message.author.bot:
                    format_match = format.search(message.content)
                    notify_match = notify.search(message.content)
                    if format_match is not None:
                        pass
                    elif notify_match is not None:
                        pass
                    else:
                        count += 1
                        await message.delete()
