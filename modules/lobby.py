import datetime
import re
from abc import ABC, abstractmethod

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

import classes.permissions as permissions
import databases.current
from classes.AgeCalculations import AgeCalculations
from classes.databaseController import UserTransactions, ConfigData, VerificationTransactions


class LobbyProcess(ABC):
    @staticmethod
    @abstractmethod
    async def approve_user(guild, user, dob, age, staff):
        # updates user's age if it exists, otherwise makes a new entry
        UserTransactions.update_user_dob(user.id, dob)
        # Adds roles to the user
        await LobbyProcess.add_roles_user(user, guild)
        # Removes roles from the user
        await LobbyProcess.remove_roles_user(user, guild)
        # check add the right age role
        await LobbyProcess.calculate_age_role(user, guild, age)
        # Log age and dob to lobbylog
        await LobbyProcess.log(user, guild, dob, age, staff)
        # fetches welcoming message and welcomes them in general channel
        await LobbyProcess.welcome(user, guild)
        # Cleans up the messages
        await LobbyProcess.clean_up(guild, user)

    @staticmethod
    @abstractmethod
    async def add_roles_user(user, guild):
        confroles = ConfigData().get_key(guild.id, "ADD")
        roles = []
        for role in confroles:
            verrole = guild.get_role(int(role))
            roles.append(verrole)
        await user.add_roles(*roles)

    @staticmethod
    @abstractmethod
    async def remove_roles_user(user, guild):
        confroles = ConfigData().get_key(guild.id, "REM")
        roles = []
        for role in confroles:
            verrole = guild.get_role(int(role))
            roles.append(verrole)
        await user.remove_roles(*roles)

    @staticmethod
    @abstractmethod
    async def calculate_age_role(user, guild, age):
        for n, y in {18: 21, 21: 25, 25: 1000}.items():
            if n <= int(age) < y:
                agerole = ConfigData().get_key(guild.id, str(n))
                agerole = guild.get_role(int(agerole))
                await user.add_roles(agerole)
                break

    @staticmethod
    @abstractmethod
    async def log(user, guild, age, dob, staff):
        lobbylog = ConfigData().get_key(guild.id, "lobbylog")
        channel = guild.get_channel(int(lobbylog))
        await channel.send(f"user: {user.mention}\n"
                           f"Age: {age} \n"
                           f"DOB: {dob} \n"
                           f"User info: \n"
                           f"UID: {user.id}  joined at: {user.joined_at.strftime('%m/%d/%Y %I:%M:%S %p')} executed: {datetime.datetime.now().strftime('%m/%d/%Y %I:%M:%S %p')} \n"
                           f"staff: {staff}")

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
                await message.delete()
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
        await channel.send(f"Welcome to {guild.name} {user.mention}! {message}")


class Lobby(commands.GroupCog):
    def __init__(self, bot):
        self.bot = bot
        self.index = 0
        self.bot.add_view(self.VerifyButton())
        self.bot.add_view(self.AgeButtons())

    class VerifyModal(discord.ui.Modal):
        # Our modal classes MUST subclass `discord.ui.Modal`,
        # but the title can be whatever you want.
        title = "Verify your age"
        custom_id = "verify"
        # This will be a short input, where the user can enter their name
        # It will also have a placeholder, as denoted by the `placeholder` kwarg.
        # By default, it is required and is a short-style input which is exactly
        # what we want.
        age = discord.ui.TextInput(
                label='age',
                placeholder='99',
                max_length=3,

        )

        # This is a longer, paragraph style input, where user can submit feedback
        # Unlike the name, it is not required. If filled out, however, it will
        # only accept a maximum of 300 characters, as denoted by the
        # `max_length=300` kwarg.
        dateofbirth = discord.ui.TextInput(
                label='Date of Birth (mm/dd/yyyy)',
                placeholder='mm/dd/yyyy',
                max_length=10
        )

        # Requires age checks, and then needs to send a message to the lobby channel; also make the lobby channel a config item.
        # Add in all the checks before it even gets to the lobby; age matches dob, dob already exists but diff?

        async def on_submit(self, interaction: discord.Interaction):
            userdata: databases.current.Users = UserTransactions.get_user(interaction.user.id)
            modlobby = ConfigData().get_key_int(interaction.guild.id, "lobbymod")
            channel = interaction.guild.get_channel(modlobby)
            age = self.age.value
            # validates inputs with regex
            if await AgeCalculations.infocheck(interaction, age, self.dateofbirth.value, channel) is False:
                return
            dob = self.dateofbirth.value.replace("-", "/").replace(".", "/")

            print(dob)
            # Checks if date of birth and age match
            if int(age) < 18:
                await channel.send(
                        f"[Info] User {interaction.user.mention}\'s gave an age below 18 and was added to the ID list.\n"
                        f"[Debug] Age: {age} dob {dob}")
                await interaction.response.send_message(
                        f'Unfortunately you are too young for our server. If you are 17 you may wait in the lobby.',
                        ephemeral=True)
                VerificationTransactions.set_idcheck_to_true(interaction.user.id,
                                                             f"{datetime.datetime.now(datetime.timezone.utc).strftime('%m/%d/%Y')}: User is under the age of 18")
                return
            # Checks if user is underaged
            agechecked, years = AgeCalculations.agechecker(age, dob)
            if agechecked != 0:
                await channel.send(
                        f"[Info] User {interaction.user.mention}\'s age does not match and has been timed out. User gave {age} but dob indicates {years}\n"
                        f"[Debug] Age: {age} dob {dob}")
                await interaction.response.send_message(
                        f'A staff member will contact you within 24 hours, please wait patiently.',
                        ephemeral=True)
                return
            # Checks if user has a date of birth in the database, and if the date of births match.
            if AgeCalculations.check_date_of_birth(userdata, dob) is False:
                await channel.send(
                        f"[Info] User {interaction.user.mention}\'s date of birth does not match. Given: {dob} Recorded: {userdata.dob.strftime('%m/%d/%Y')}\n"
                        f"[Debug] Age: {age} dob {dob}")
                await interaction.response.send_message(
                        f'A staff member will contact you within 24 hours, please wait patiently.',
                        ephemeral=True)
                return

            # Check if user needs to ID or has previously ID'd
            if await AgeCalculations.id_check_or_id_verified(interaction.user, interaction.guild, channel):
                await interaction.response.send_message(
                        f'A staff member will contact you within 24 hours, please wait patiently.', ephemeral=True)
                return
            # Check the age and send the right command/button based upon that.
            command_prefix = AgeCalculations.prefix(age)
            # Check Chat History
            await AgeCalculations.check_history(interaction.user, channel)
            # Sends the buttons and information to lobby channel
            await channel.send(
                    f"\n{interaction.user.mention} has given {age} {dob}. You can let them through with the buttons below"
                    f"\n"
                    f"[DEBUG] `?{command_prefix} {interaction.user.mention} {age} {dob}`",
                    view=Lobby.AgeButtons(age=age, dob=dob, user=interaction.user))

            await interaction.response.send_message(
                    f'Thank you for submitting your age and dob! We will let you through within 24 hours.',
                    ephemeral=True)

        async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
            print(error)
            await interaction.response.send_message('Oops! Something went wrong.\n'
                                                    f'{error}')
            raise error

    class VerifyButton(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        @discord.ui.button(label="Verify Here!", style=discord.ButtonStyle.red, custom_id="verify")
        async def test(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_modal(Lobby.VerifyModal())

    class AgeButtons(discord.ui.View):
        def __init__(self, age: int = None, dob: str = None, user: discord.Member = None):
            self.age = age
            self.dob = dob
            self.user = user
            super().__init__(timeout=None)

        @discord.ui.button(label="allow", style=discord.ButtonStyle.green, custom_id="allow")
        async def allow(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.age is None or self.dob is None or self.user is None:
                await interaction.response.send_message('Missing data, please use the command.', ephemeral=True)
                return
            button.disabled = True
            # Share this with the age commands
            await LobbyProcess.approve_user(interaction.guild, self.user, self.dob, self.age, interaction.user.name)

        @discord.ui.button(label="Manual ID Check", style=discord.ButtonStyle.red, custom_id="ID")
        async def manual_id(self, interaction: discord.Interaction, button: discord.ui.Button):
            if self.user is None:
                await interaction.response.send_message('Missing data, please manually report user to admins',
                                                        ephemeral=True)
            idcheck = ConfigData().get_key_int(interaction.guild.id, "idlog")
            admin = ConfigData().get_key(interaction.guild.id, "admin")
            idlog = interaction.guild.get_channel(idcheck)
            await idlog.send(
                    f"<@&{admin[0]}> {interaction.user.mention} has flagged {self.user.mention} for manual ID.")
            return

    @app_commands.command(name="button")
    @permissions.check_app_roles_admin()
    async def verify_button(self, interaction: discord.Interaction, text: str):
        await interaction.channel.send(text, view=self.VerifyButton())

    @app_commands.command()
    @app_commands.choices(operation=[Choice(name=x, value=x) for x in
                                     ['add', 'update', 'delete', 'get']])
    @permissions.check_app_roles_admin()
    async def database(self, interaction: discord.Interaction, operation: Choice['str'], userid: str, dob: str = None):

        await interaction.response.defer(ephemeral=True)
        match operation.value.upper():
            case "UPDATE":
                if await AgeCalculations.validatedob(dob, interaction) is False:
                    return
                UserTransactions.update_user_dob(userid, dob)
                await interaction.followup.send(f"<@{userid}>'s dob updated to: {dob}")
            case "DELETE":
                if UserTransactions.user_delete(userid) is False:
                    await interaction.followup.send(f"Can't find entry: <@{userid}>")
                    return
                await interaction.followup.send(f"Deleted entry: <@{userid}>")
            case "ADD":
                if await AgeCalculations.validatedob(dob, interaction) is False:
                    return
                UserTransactions.add_user_full(str(userid), dob)
                await interaction.followup.send(f"<@{userid}> added to the database with dob: {dob}")
            case "GET":
                user = UserTransactions.get_user(userid)
                await interaction.followup.send(f"**__USER INFO__**\n"
                                                f"user: <@{user.uid}>\n"
                                                f"dob: {user.dob.strftime('%m/%d/%Y')}")

    @app_commands.command(description="ID verifies user. process True will put the user through the lobby.")
    @app_commands.choices(process=[Choice(name=x, value=x) for x in
                                   ["True", "False"]])
    @permissions.check_app_roles_admin()
    async def idverify(self, interaction: discord.Interaction, process: Choice['str'],
                       user: discord.Member, dob: str):
        await interaction.response.defer(ephemeral=True)
        lobbylog = ConfigData().get_key_int(interaction.guild.id, "lobbylog")

        agelog = interaction.guild.get_channel(lobbylog)
        await AgeCalculations.validatedob(dob, interaction)
        print(f"matching time: {process.value.upper()}")
        match process.value.upper():
            case "TRUE":
                print("true")
                VerificationTransactions.idverify_update(user.id, dob)
                await interaction.followup.send(
                        f"{user.mention} has been ID verified with date of birth: {dob}")
                await agelog.send(f"""**USER ID VERIFICATION**
user: {user.mention}
DOB: {dob}
UID: {user.id} 
**ID VERIFIED BY:** {interaction.user}""")
                age = AgeCalculations.dob_to_age(dob)
                await LobbyProcess.approve_user(interaction.guild, user, dob, age, interaction.user.name)
            case "FALSE":
                VerificationTransactions.idverify_update(user.id, dob)
                await interaction.followup.send(
                        f"{user.mention} has been ID verified with date of birth: {dob}")
                await agelog.send(f"""**USER ID VERIFICATION**
user: {user.mention}
DOB: {dob}
UID: {user.id} 
**ID VERIFIED BY:** {interaction.user}""")
            # case "GET":
            #     user = VerificationTransactions.get_id_info(userid)
            #     if user is None:
            #         await interaction.followup.send("Not found")
            #         return
            #     await interaction.followup.send(f"**__USER INFO__**\n"
            #                                     f"user: <@{user.uid}>\n"
            #                                     f"Reason: {user.reason}\n"
            #                                     f"idcheck: {user.idcheck}\n"
            #                                     f"idverifier: {user.idverified}\n"
            #                                     f"verifieddob: {user.verifieddob}\n")

    @app_commands.command()
    @permissions.check_app_roles()
    async def returnlobby(self, interaction: discord.Interaction, user: discord.Member):
        await interaction.response.defer()
        add: list = ConfigData().get_key(interaction.guild.id, "add")
        rem: list = ConfigData().get_key(interaction.guild.id, "rem")
        returns: list = ConfigData().get_key(interaction.guild.id, "return")
        add.append(ConfigData().get_key_int(interaction.guild.id, "18"))
        add.append(ConfigData().get_key_int(interaction.guild.id, "21"))
        add.append(ConfigData().get_key_int(interaction.guild.id, "25"))
        rm = []
        ra = []
        for role in rem:
            r = interaction.guild.get_role(role)
            ra.append(r)
        for role in add + returns:
            r = interaction.guild.get_role(role)
            rm.append(r)
        await user.remove_roles(*rm, reason="returning to lobby")
        await user.add_roles(*ra, reason="returning to lobby")
        await interaction.followup.send(
                f"{user.mention} has been moved back to the lobby by {interaction.user.mention}")

    @app_commands.command()
    @permissions.check_app_roles()
    async def agecheck(self, interaction: discord.Interaction, dob: str):
        age = AgeCalculations.dob_to_age(dob)
        await interaction.response.send_message(f"As of today {dob} is {age} years old", ephemeral=True)

    @commands.command(name="18a")
    @permissions.check_roles()
    async def _18a(self, ctx: commands.Context, user: discord.Member, age: int, dob: str):
        dob = AgeCalculations.regex(dob)
        await LobbyProcess.approve_user(ctx.guild, user, dob, age, ctx.author.name)
        await ctx.message.delete()

    @commands.command(name="21a")
    @permissions.check_roles()
    async def _21a(self, ctx: commands.Context, user: discord.Member, age: int, dob: str):
        dob = AgeCalculations.regex(dob)
        await LobbyProcess.approve_user(ctx.guild, user, dob, age, ctx.author.name)
        await ctx.message.delete()

    @commands.command(name="25a")
    @permissions.check_roles()
    async def _25a(self, ctx: commands.Context, user: discord.Member, age: int, dob: str):
        dob = AgeCalculations.regex(dob)
        await LobbyProcess.approve_user(ctx.guild, user, dob, age, ctx.author.name)
        await ctx.message.delete()

    # Event

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        lobby = ConfigData().get_key_int(member.guild.id, "lobby")
        channel = member.guild.get_channel(lobby)
        lobbywelcome = ConfigData().get_key(member.guild.id, "lobbywelcome")
        await channel.send(f"Welcome {member.mention}! {lobbywelcome}", view=self.VerifyButton())


async def setup(bot):
    await bot.add_cog(Lobby(bot))
