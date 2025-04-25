import logging
import re

import discord
from dateutil.relativedelta import relativedelta

import databases.current
from classes.databaseController import *


class AgeCalculations(ABC):

    @staticmethod
    @abstractmethod
    def prefix(age):
        for n, y in {18: 21, 21: 25, 25: 1000}.items():
            if n <= int(age) < y:
                return f"{n}a"

    @staticmethod
    @abstractmethod
    def check_date_of_birth(userdata, dob):
        if userdata is None or userdata.date_of_birth is None:
            print("None found")
            return True
        return Encryption().decrypt(userdata.date_of_birth) == dob

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
    async def id_check_or_id_verified(user: discord.Member, guild, channel, send_message=True, age=None, dob=None):
        userinfo: databases.current.IdVerification = VerificationTransactions.get_id_info(user.id)
        idlog = ConfigData().get_key_int(guild.id, "idlog")
        idchannel = guild.get_channel(idlog)
        if userinfo is None:
            return False
        if userinfo.idverified is True and userinfo.verifieddob is not None and send_message is True:
            await channel.send(
                    f"[Info] {user.mention} has previously ID verified: {userinfo.verifieddob.strftime('%m/%d/%Y')}")
            logging.debug(f"{user} has previously ID verified: {userinfo.verifieddob.strftime('%m/%d/%Y')}")
            return False
        if userinfo.idcheck is True:
            await idchannel.send(
                    f"[Info] {user.mention} is on the ID list with reason: {userinfo.reason}. Please ID the user "
                    f"before letting them through."
                    f"\n[DEBUG] age: {age} dob: {dob} (please remove this after verification if underage)")
            logging.debug(
                    f"{user} is on the ID list with reason: {userinfo.reason}. Please ID the user before letting them "
                    f"through.")
            return True
        return False

    @staticmethod
    @abstractmethod
    async def id_check(guild, user: discord.Member, age, dob):
        userinfo: databases.current.IdVerification = VerificationTransactions.get_id_info(user.id)
        print(guild.id)
        idlog = ConfigData().get_key_int(guild.id, "idlog")
        idchannel = guild.get_channel(idlog)
        if userinfo is None:
            return False
        if userinfo.idcheck is True:
            await idchannel.send(
                    f"[Info] {user.mention} is on the ID list with reason: {userinfo.reason}. Please ID the user before "
                    f"letting them through."
                    f"lobby debug: age: {age} dob: {dob} (please remove this after verification)")
            return True
        return False

    @staticmethod
    @abstractmethod
    async def infocheck(interaction: discord.Interaction, age: str, dateofbirth: str, channel: discord.TextChannel,
                        location="Lobby"):
        agevalid = re.match(r'[0-9]*$', age)
        if agevalid is None:
            await interaction.response.send_message('Please fill in your age in numbers.', ephemeral=True)
            await channel.send(
                    f"{interaction.user.mention} failed in verification at age: {age} {dateofbirth}")
            return False
        try:
            dateofbirth = await AgeCalculations.add_slashes_to_dob(dateofbirth)
        except Exception as e:
            logging.info(f"failed slashes to dob: {e}")


        redob = r"(((0?[0-9])|(1[012]))([\/|\-|.])((0?[1-9])|([12][0-9])|(3[01]))([\/|\-|.])((20[012]\d|19\d\d)|(1\d|2[0123])))"
        dobvalid = re.match(redob, dateofbirth)

        if dobvalid is None:
            await interaction.response.send_message(
                    'Please fill in your date of birth as with the format: mm/dd/yyyy.', ephemeral=True)
            await channel.send(
                    f"[{location} info] {interaction.user.mention} failed in verification at date of birth: {age} {dateofbirth}")
            return None
        dateofbirth = AgeCalculations.regex(dateofbirth)
        return dateofbirth

    @staticmethod
    @abstractmethod
    async def add_slashes_to_dob(dateofbirth):
        if "/" not in dateofbirth or "-" not in dateofbirth or "." not in dateofbirth:
            deconstruct = re.search(r"(((0[0-9])|(1[012])|(0?[0-9]))((0[1-9])|([12][0-9])|(3[01])|(0?[1-9]))((20[012]\d|19\d\d)|(1\d|2[0123])))", dateofbirth)
            dateofbirth = f"{deconstruct.group(3)}/{deconstruct.group(6)}/{deconstruct.group(10)}"
        return dateofbirth

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
    def dob_to_age(dob):
        dob_object = datetime.strptime(dob, "%m/%d/%Y")
        today = datetime.now()
        age_output = relativedelta(today, dob_object)
        return age_output.years

    @staticmethod
    @abstractmethod
    def regex(date_of_birth):
        try:
            date_of_birth = date_of_birth.replace("-", "/").replace(".", "/")
            datetime.strptime(date_of_birth, "%m/%d/%Y")
            dob = str(date_of_birth)
            dob_object = re.search(r"([0-1]?[0-9])/([0-3]?[0-9])/([0-2][0-9][0-9][0-9])", dob)
            month = dob_object.group(1).zfill(2)
            day = dob_object.group(2).zfill(2)
            year = dob_object.group(3)
            fulldob = f"{month}/{day}/{year}"
            return fulldob
        except AttributeError or TypeError:
            return "AttributeError"
        except ValueError:
            return "ValueError"

    @staticmethod
    @abstractmethod
    async def validatedob(arg2, interaction):
        dob = AgeCalculations.regex(arg2)
        if dob == "AttributeError":
            await interaction.followup.send("Please fill in the date of birth field.")
            return False
        if dob == "ValueError":
            await interaction.followup.send("Please fill the dob in with the format: mm/dd/yyyy")
            return False
