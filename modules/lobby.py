import datetime
import os

import discord
from discord import app_commands
from discord.ext import commands

import databases.current
from classes.AgeCalculations import AgeCalculations
from classes.databaseController import UserTransactions

prefix = os.getenv('PREFIX')


class Lobby(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.index = 0
        self.bot.add_view(self.VerifyButton())
        self.bot.add_view(self.AgeButtons())

    class VerifyModal(discord.ui.Modal):
        # Our modal classes MUST subclass `discord.ui.Modal`,
        # but the title can be whatever you want.
        title = "Verify your age"
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
            channel = interaction.guild.get_channel(1155647622896439377)
            age = self.age.value
            # validates inputs with regex
            if await AgeCalculations.infocheck(interaction, age, self.dateofbirth.value, channel) is False:
                return
            dob = self.dateofbirth.value.replace("-", "/").replace(".", "/")

            print(dob)
            # Checks if date of birth and age match
            if int(age) < 18:
                await channel.send(
                        f"User {interaction.user.mention}\'s gave an age below 18 and was added to the ID list.\n"
                        f"[Debug] Age: {age} dob {dob}")
                await interaction.response.send_message(
                        f'Unfortunately you are too young for our server. If you are 17 you may wait in the lobby.',
                        ephemeral=True)
                UserTransactions.set_idcheck_to_true(interaction.user.id, f"{datetime.datetime.now(datetime.timezone.utc).strftime('%m/%d/%Y')}: User is under the age of 18")
                return
            # Checks if age matches with the date of birth
            agechecked, years = AgeCalculations.agechecker(age, dob)
            if agechecked != 0:
                await channel.send(
                        f"User {interaction.user.mention}\'s age does not match and has been timed out. User gave {age} but dob indicates {years}\n"
                        f"[Debug] Age: {age} dob {dob}")
                await interaction.response.send_message(
                        f'A staff member will contact you within 24 hours, please wait patiently.',
                        ephemeral=True)
                return
            # Checks if user has a date of birth in the database, and if the date of births match.
            if AgeCalculations.check_date_of_birth(userdata, dob) is False:
                await channel.send(
                        f"User {interaction.user.mention}\'s date of birth does not match. Given: {dob} Recorded: {userdata.dob.strftime('%m/%d/%Y')}\n"
                        f"[Debug] Age: {age} dob {dob}")
                await interaction.response.send_message(
                        f'A staff member will contact you within 24 hours, please wait patiently.',
                        ephemeral=True)
                return
            # Check Chat History
            await AgeCalculations.check_history(interaction.user, channel)
            # Check if user needs to ID or has previously ID'd
            if await AgeCalculations.id_check_or_id_verified(interaction.user, channel):
                return
            # Check the age and send the right command/button based upon that.
            command_prefix = ""
            for n, y in {18: 21, 21: 25, 25: 1000}.items():
                if n <= int(age) < y:
                    command_prefix = f"{n}+"
                    break

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
            await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)

            # Make sure we know what the error actually is
            traceback.print_exception(type(error), error, error.__traceback__)

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
            # updates user's age if it exists, otherwise makes a new entry
            UserTransactions.update_user_dob(self.user.id, self.dob)

        @discord.ui.button(label="Manual ID Check", style=discord.ButtonStyle.red, custom_id="ID")
        async def manual_id(self, interaction: discord.Interaction, button: discord.ui.Button):
            pass

    @app_commands.command(name="btest")
    async def button_test(self, interaction: discord.Interaction):
        print("received")
        await interaction.channel.send("verify here", view=self.VerifyButton())

    # @commands.Cog.listener()
    # async def on_message(self, message):
    #     # Enforces lobby format
    #     bot = self.bot
    #     dobreg = re.compile(r"([0-9][0-9]) (1[0-2]|0?[0-9]|1)/([0-3]?[0-9])/([0-2][0-9][0-9][0-9])")
    #     match = dobreg.search(message.content)
    #     if message.guild is None:
    #         return
    #     if message.author.bot:
    #         return
    #     # Searches the config for the lobby for a specific guild
    #     p = session.query(db.permissions).filter_by(guild=message.guild.id).first()
    #     c = session.query(db.config).filter_by(guild=message.guild.id).first()
    #     # Checks if user is a staff member.
    #     if message.author.get_role(p.mod) is None and message.author.get_role(
    #             p.admin) is None and message.author.get_role(p.trial) is None:
    #         # Checks if channel is the lobby
    #         if message.channel.id == c.lobby:
    #             # Checks if message matches the regex
    #             if match:
    #                 waitmessage = f"{message.author.mention} Thank you for submitting your age! " \
    #                               f"One of our staff members will let you through into the main server once they are available. " \
    #                               f"Please be patient, as our lobby is handled manually."
    #                 channel = bot.get_channel(c.modlobby)
    #                 lobby = bot.get_channel(c.lobby)
    #                 await message.add_reaction("🤖")
    #                 # Checks the ages in the message, and acts based upon it.
    #                 if int(match.group(1)) < 18:
    #                     await channel.send(
    #                         f"<@&{p.lobbystaff}> {message.author.mention} has given an age under the age of 18: {message.content} (User has been added to ID list)")
    #                     idchecker = session.query(db.idcheck).filter_by(uid=message.author.id).first()
    #                     if idchecker is not None:
    #                         idchecker.check = True
    #                         session.commit()
    #                     else:
    #                         try:
    #                             idcheck = db.idcheck(message.author.id, True)
    #                             session.add(idcheck)
    #                             session.commit()
    #                         except:
    #                             session.rollback()
    #                             session.close()
    #                             logging.exception("failed to  log to database")
    #                 if int(match.group(1)) >= 18 and not int(match.group(1)) > 20:
    #                     await channel.send(
    #                         f"<@&{p.lobbystaff}> {message.author.mention} has given age. You can let them through with `?18a {message.author.mention} {message.content}`")
    #                     await lobby.send(waitmessage)
    #                     await Lobby.check(message.author, channel)
    #                     await Lobby.idcheck(message.author, channel)
    #                 elif int(match.group(1)) >= 21 and not int(match.group(1)) > 24:
    #                     await channel.send(
    #                         f"<@&{p.lobbystaff}> {message.author.mention} has given age. You can let them through with `?21a {message.author.mention} {message.content}`")
    #                     await lobby.send(waitmessage)
    #                     await Lobby.check(message.author, channel)
    #                     await Lobby.idcheck(message.author, channel)
    #                 elif int(match.group(1)) >= 25:
    #                     await channel.send(
    #                         f"<@&{p.lobbystaff}> {message.author.mention} has given age. You can let them through with `?25a {message.author.mention} {message.content}`")
    #                     await lobby.send(waitmessage)
    #                     await Lobby.check(message.author, channel)
    #                     await Lobby.idcheck(message.author, channel)
    #                 return
    #             else:
    #                 channel = bot.get_channel(c.modlobby)
    #                 await channel.send(f"{message.author.mention} failed to follow the format: {message.content}")
    #                 await message.channel.send(
    #                     f"{message.author.mention} Please use format age mm/dd/yyyy "
    #                     f"\n Example: `122 01/01/1900` "
    #                     f"\n __**Do not round up your age**__ "
    #                     f"\nhttps://cdn.discordapp.com/attachments/523343470362886154/1118851484197605396/image.png")
    #                 await message.delete()
    #                 return
    #     else:
    #         pass


async def setup(bot):
    await bot.add_cog(Lobby(bot))
