"""Modal for the NSFW section, similar to lobby but is fully automatic"""
from abc import ABC, abstractmethod
from datetime import datetime

import discord

from classes.AgeCalculations import AgeCalculations
from classes.databaseController import UserTransactions, ConfigData, VerificationTransactions


class NsfwFunctions(ABC):
    @staticmethod
    @abstractmethod
    async def log(user, guild, age, dob):
        lobbylog = ConfigData().get_key(guild.id, "nsfwlog")
        channel = guild.get_channel(int(lobbylog))

        embed = discord.Embed(title=f"{user.name}", description=f"Age: {age} \n"
                                                                f"DOB: {dob} \n")
        embed.set_footer(text=f"UID: {user.id}")

        await channel.send(embed=embed)

    @staticmethod
    @abstractmethod
    async def add_roles_user(user, guild):
        confrole = ConfigData().get_key_int(guild.id, "NSFW")
        roles = guild.get_role(confrole)


        await user.add_roles(roles)


class NsfwVerifyModal(discord.ui.Modal):
    # Our modal classes MUST subclass `discord.ui.Modal`,
    # but the title can be whatever you want.
    title = "Verify your age"
    custom_id = "NsfwVerify"
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
        userdata = UserTransactions.get_user(interaction.user.id)
        modlobby = ConfigData().get_key_int(interaction.guild.id, "lobbymod")
        channel = interaction.guild.get_channel(modlobby)
        age = self.age.value
        # validates inputs with regex
        if await AgeCalculations.infocheck(interaction, age, self.dateofbirth.value, channel, "NSFW") is False:
            return
        dob = self.dateofbirth.value.replace("-", "/").replace(".", "/")

        print(dob)
        # Checks if date of birth and age match
        if int(age) < 18:
            await channel.send(
                    f"[Info] User {interaction.user.mention}\'s gave an age below 18 and was added to the ID list.\n"
                    f"[NSFW Debug] Age: {age} dob {dob}")
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
                    f"[NSFW Debug] Age: {age} dob {dob}")
            await interaction.response.send_message(
                    f'A staff member will contact you within 24 hours, please wait patiently.',
                    ephemeral=True)
            return
        # Checks if user has a date of birth in the database, and if the date of births match.
        if AgeCalculations.check_date_of_birth(userdata, dob) is False:
            await channel.send(
                    f"[Info] User {interaction.user.mention}\'s date of birth does not match. Given: {dob} Recorded: {userdata.dob.strftime('%m/%d/%Y')}\n"
                    f"[NSFW Debug] Age: {age} dob {dob}")
            await interaction.response.send_message(
                    f'A staff member will contact you within 24 hours, please wait patiently.',
                    ephemeral=True)
            return

        # Check if user needs to ID or has previously ID'd
        if await AgeCalculations.id_check_or_id_verified(interaction.user, interaction.guild, channel):
            await interaction.response.send_message(
                    f'A staff member will contact you within 24 hours, please wait patiently.', ephemeral=True)
            return
        # Check Chat History
        await AgeCalculations.check_history(interaction.user, channel)
        # Automatically processes users if all checks pass.
        await NsfwFunctions.add_roles_user(interaction.user, interaction.guild)
        await interaction.response.send_message(
                f"Thank you for submitting your age and dob! You've been granted access to the NSFW section",
                ephemeral=True)
        # log data
        await NsfwFunctions.log(interaction.user, interaction.guild, self.age.value, self.dateofbirth.value)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        print(error)
        await interaction.response.send_message('Oops! Something went wrong.\n'
                                                f'{error}')
        raise error
