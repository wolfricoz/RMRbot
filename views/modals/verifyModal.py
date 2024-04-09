import datetime
import logging

import discord

import databases.current
from classes.AgeCalculations import AgeCalculations
from classes.databaseController import UserTransactions, ConfigData, VerificationTransactions
from views.buttons.agebuttons import AgeButtons


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
            label='Current Age (Do not round up or down)',
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
        idlog = ConfigData().get_key_int(interaction.guild.id, "idlog")
        admin = ConfigData().get_key(interaction.guild.id, "admin")
        channel = interaction.guild.get_channel(modlobby)
        idchannel = interaction.guild.get_channel(idlog)
        age = int(self.age.value)
        # validates inputs with regex
        if await AgeCalculations.infocheck(interaction, self.age.value, self.dateofbirth.value, channel) is False:
            return
        dob = self.dateofbirth.value.replace("-", "/").replace(".", "/")
        # Checks if date of birth and age match
        if age < 18:
            await channel.send(
                    f"[Info] User {interaction.user.mention}\'s gave an age below 18 and was added to the ID list.\n"
                    f"[Lobby Debug] Age: {age} dob {dob}")
            await interaction.response.send_message(
                    f'Unfortunately you are too young for our server. If you are 17 you may wait in the lobby.',
                    ephemeral=True)
            VerificationTransactions.set_idcheck_to_true(interaction.user.id,
                                                         f"{datetime.datetime.now(datetime.timezone.utc).strftime('%m/%d/%Y')}: User is under the age of 18")
            logging.debug(f"userid: {interaction.user.id} gave an age below 18 and was added to the ID list. Age given: {age}. Dob is NOT logged")
            return
        # Checks if user is underaged
        agechecked, years = AgeCalculations.agechecker(age, dob)
        logging.debug(f"userid: {interaction.user.id} age: {age} dob: {dob}")
        if agechecked == 1 or agechecked == -1:
            await channel.send(
                    f"[Info] <@&{admin[0]}> User {interaction.user.mention}\'s age does not match. "
                    f"User gave {age} but dob indicates {years}. User may retry.\n")
            await interaction.response.send_message(
                    f'It seems your age does not match the date of birth you provided. Please try again. Please use '
                    f'your CURRENT age.',
                    ephemeral=True)
            return
        if agechecked > 1 or agechecked < -1:
            await idchannel.send(
                    f"[Info] <@&{admin[0]}> User {interaction.user.mention}\'s age does not match and has been timed "
                    f"out. User gave {age} but dob indicates {years}\n"
                    f"[Lobby Debug] Age: {age} dob {dob}")
            await interaction.response.send_message(
                    f'A staff member will contact you soon, please wait patiently.',
                    ephemeral=True)
            return
        # Checks if user has a date of birth in the database, and if the date of births match.
        if AgeCalculations.check_date_of_birth(userdata, dob) is False:
            await idchannel.send(
                    f"[Info] <@&{admin[0]}> User {interaction.user.mention}\'s date of birth does not match. Given: {dob} Recorded: {userdata.dob.strftime('%m/%d/%Y')}\n"
                    f"[Lobby Debug] Age: {age} dob {dob}")
            await interaction.response.send_message(
                    f'A staff member will contact you soon, please wait patiently.',
                    ephemeral=True)
            return

        # Check if user needs to ID or has previously ID'd
        if await AgeCalculations.id_check_or_id_verified(interaction.user, interaction.guild, channel):
            await modlobby.send(f"{interaction.user.mention} gave ages: {age} {dob}, but is on the idlist.")
            await interaction.response.send_message(
                    f'A staff member will contact you soon, please wait patiently.', ephemeral=True)
            return
        # Check the age and send the right command/button based upon that.
        command_prefix = AgeCalculations.prefix(age)
        # Check Chat History
        await AgeCalculations.check_history(interaction.user, channel)
        # Sends the buttons and information to lobby channel
        await channel.send(
                f"\n{interaction.user.mention} has given {age} {dob}. You can let them through with the buttons below"
                f"\n"
                f"[LOBBY DEBUG] `?{command_prefix} {interaction.user.mention} {age} {dob}`",
                view=AgeButtons(age=age, dob=dob, user=interaction.user))
        try:
            await interaction.response.send_message(
                    f'Thank you for submitting your age and dob! We will let you through soon.',
                    ephemeral=True)
        except discord.errors.NotFound:
            await interaction.followup.send(
                    f'Thank you for submitting your age and dob! We will let you through soon.',
                    ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        print(error)
        await interaction.response.send_message('Oops! Something went wrong.\n'
                                                f'{error}')
        raise error
