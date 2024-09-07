import datetime
import re
from abc import ABC, abstractmethod

import discord
from discord.utils import get

from classes.AgeCalculations import AgeCalculations
from classes.databaseController import UserTransactions, ConfigData
from classes.queue import queue
from views.embeds.SendEmbed import send_embed


class LobbyProcess(ABC):
    @staticmethod
    @abstractmethod
    async def approve_user(guild, user, dob, age, staff):
        # checks if user is on the id list
        if await AgeCalculations.id_check(guild, user, age, dob):
            return
        # updates user's age if it exists, otherwise makes a new entry
        UserTransactions.update_user_dob(user.id, dob, guild.name)

        # check add the right age role
        queue().add(LobbyProcess.calculate_age_role(user, guild, age), priority=2)

        # changes user's roles; adds and removes
        queue().add(LobbyProcess.change_user_roles(user, guild), priority=2)

        # Log age and dob to lobbylog
        queue().add(LobbyProcess.log(user, guild, age, dob, staff), priority=2)

        # fetches welcoming message and welcomes them in general channel
        queue().add(LobbyProcess.welcome(user, guild), priority=2)

        # Cleans up the messages in the lobby and where the command was executed
        queue().add(LobbyProcess.clean_up(guild, user), priority=2)

    @staticmethod
    @abstractmethod
    async def change_user_roles(user, guild):
        confaddroles = ConfigData().get_key(guild.id, "ADD")
        add_roles = []
        for role in confaddroles:
            verrole = get(guild.roles, id=int(role))
            add_roles.append(verrole)
        confremroles = ConfigData().get_key(guild.id, "REM")
        rem_roles = []
        for role in confremroles:
            verrole = get(guild.roles, id=int(role))
            rem_roles.append(verrole)
        await user.remove_roles(*rem_roles)
        await user.add_roles(*add_roles)

    @staticmethod
    @abstractmethod
    async def calculate_age_role(user, guild, age):
        for n, y in {18: 21, 21: 25, 25: 1000}.items():
            if n <= int(age) < y:
                agerole = ConfigData().get_key_int(guild.id, str(n))
                agerole = guild.get_role(int(agerole))
                await user.add_roles(agerole)
                return

    @staticmethod
    @abstractmethod
    async def log(user, guild, age, dob, staff):
        lobbylog = ConfigData().get_key(guild.id, "lobbylog")
        channel = guild.get_channel(int(lobbylog))
        await channel.send(f"user: {user.mention}\n"
                           f"Age: {age} \n"
                           f"DOB: {dob} \n"
                           f"User info: \n"
                           f"UID: {user.id} \n"
                           f"Joined at: {user.joined_at.strftime('%m/%d/%Y %I:%M:%S %p')} \n"
                           f"Account created at: {user.created_at.strftime('%m/%d/%Y %I:%M:%S %p')} \n"
                           f"Executed at: {datetime.datetime.now().strftime('%m/%d/%Y %I:%M:%S %p')} \n"
                           f"Staff: {staff}")

    @staticmethod
    @abstractmethod
    async def clean_up(guild, user):
        lobby = ConfigData().get_key(guild.id, "lobby")
        lobbymod = ConfigData().get_key(guild.id, "lobbymod")
        channel = guild.get_channel(int(lobby))
        messages = channel.history(limit=100)
        notify = re.compile(r"Info", flags=re.IGNORECASE)
        count = 0
        async for message in messages:
            if message.author == user or user in message.mentions and count < 10:
                count += 1
                try:
                    await message.delete()
                except discord.NotFound:
                    pass
        channel = guild.get_channel(int(lobbymod))
        messages = channel.history(limit=100)
        count = 0
        async for message in messages:
            if user in message.mentions and count < 5:
                if message.author.bot:
                    notify_match = notify.search(message.content)
                    if notify_match is not None:
                        pass
                    else:
                        count += 1
                        await message.delete()

    @staticmethod
    @abstractmethod
    async def welcome(user: discord.Member, guild: discord.Guild):
        if ConfigData().get_key(guild.id, "welcome") == "DISABLED":
            return
        general = ConfigData().get_key(guild.id, "general")
        message = ConfigData().get_key(guild.id, "welcomemessage")
        channel = guild.get_channel(int(general))
        async for cmessage in channel.history(limit=20):
            if cmessage.author.bot and user in cmessage.mentions:
                print("welcome message already sent")
                return
        await channel.send(f"Welcome to {guild.name} {user.mention}! {message}")

    @staticmethod
    @abstractmethod
    async def age_log(age_log_channel, userid, dob, interaction, operation="added"):
        await age_log_channel.send(f"USER {operation.upper()}\n"
                                   f"DOB: {dob}\n"
                                   f"UID: {userid}\n"
                                   f"Entry updated by: {interaction.user.name}")
        await send_embed(interaction, title="updated user's date of birth", body=f"{operation} <@{userid}>({userid}) date of birth with dob: {dob}", location="channel")
