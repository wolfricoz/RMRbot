"""this module handles the lobby."""
import datetime
import os

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

import classes.permissions as permissions
from classes.AgeCalculations import AgeCalculations
from classes.databaseController import UserTransactions, ConfigData, VerificationTransactions
from classes.encryption import Encryption
from classes.lobbyprocess import LobbyProcess
from views.buttons.agebuttons import AgeButtons
from views.buttons.confirmButtons import confirmAction
from views.buttons.verifybutton import VerifyButton
from views.embeds.SendEmbed import send_embed
from views.modals import inputmodal


class Lobby(commands.GroupCog):
    def __init__(self, bot):
        self.bot = bot
        self.index = 0
        self.bot.add_view(VerifyButton())
        self.bot.add_view(AgeButtons())

    @app_commands.command(name="button")
    @permissions.check_app_roles_admin()
    async def verify_button(self, interaction: discord.Interaction, text: str):
        """Verification button for the lobby; initiates the whole process"""
        await interaction.channel.send(text, view=VerifyButton())

    @app_commands.command()
    @app_commands.choices(operation=[Choice(name=x, value=x) for x in
                                     ['add', 'update', 'delete', 'get']])
    @permissions.check_app_roles()
    async def database(self, interaction: discord.Interaction, operation: Choice['str'], userid: str, dob: str = None):
        """One stop shop to handle all age entry management. when adding or updating, dob field is required."""
        userid = int(userid)
        age_log = ConfigData().get_key_int(interaction.guild.id, "lobbylog")
        age_log_channel = interaction.guild.get_channel(age_log)
        await interaction.response.defer(ephemeral=True)  # type: ignore
        match operation.value.upper():
            case "UPDATE":
                if await AgeCalculations.validatedob(dob, interaction) is False:
                    return
                UserTransactions.update_user_dob(userid, dob, interaction.guild.name)
                await send_embed(interaction, title="Database entry updated",
                                 body=f"<@{userid}>'s database entry has been updated to: {dob}")
                await LobbyProcess.age_log(age_log_channel, userid, dob, interaction, "updated")
            case "DELETE":
                if permissions.check_admin(interaction.user) is False:
                    await interaction.followup.send("You are not an admin")
                    return
                if UserTransactions.user_delete(userid) is False:
                    await send_embed(interaction, title="Database entry not found",
                                     body=f"Can't find entry: <@{userid}>")
                    return
                await send_embed(interaction, title="Database entry deleted", body=f"Deleted entry: <@{userid}>")
            case "ADD":
                if await AgeCalculations.validatedob(dob, interaction) is False:
                    return
                UserTransactions.add_user_full(str(userid), dob, interaction.guild.name)
                await send_embed(interaction, title="Database entry added",
                                 body=f"<@{userid}> added to the database with dob: {dob}")
                await LobbyProcess.age_log(age_log_channel, userid, dob, interaction)
            case "GET":
                user = UserTransactions.get_user(userid)
                await send_embed(interaction, title="Database entry",
                                 body=f"**__USER INFO__**\n"
                                      f"user: <@{user.uid}>\n"
                                      f"dob: {Encryption().decrypt(user.date_of_birth)}")

    @app_commands.command(name="adduser")
    @permissions.check_app_roles()
    async def add_user(self, interaction: discord.Interaction, userid: str, dob: str):
        """Adds user to the database"""
        await interaction.response.defer(ephemeral=True)
        userid = int(userid)
        age_log = ConfigData().get_key_int(interaction.guild.id, "lobbylog")
        age_log_channel = interaction.guild.get_channel(age_log)
        if await AgeCalculations.validatedob(dob, interaction) is False:
            return
        UserTransactions.add_user_full(str(userid), dob)
        await interaction.followup.send(f"<@{userid}> added to the database with dob: {dob}")
        await LobbyProcess.age_log(age_log_channel, userid, dob, interaction)

    @app_commands.command()
    @app_commands.choices(process=[Choice(name=x, value=x) for x in
                                   ["True", "False"]])
    @permissions.check_app_roles_admin()
    async def idverify(self, interaction: discord.Interaction, process: Choice['str'],
                       user: discord.Member, dob: str):
        """ID verifies user. process True will put the user through the lobby."""
        await interaction.response.defer(ephemeral=True)  # type: ignore
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

    @app_commands.command()
    @permissions.check_app_roles()
    async def returnlobby(self, interaction: discord.Interaction, user: discord.Member):
        """returns user to lobby; removes the roles."""
        await interaction.response.defer()  # type: ignore
        original_user = ConfigData().get_key(interaction.guild.id, "add")
        add_to_user = list(original_user)
        rem_from_user: list = ConfigData().get_key(interaction.guild.id, "rem")
        returns: list = ConfigData().get_key(interaction.guild.id, "return")
        role18 = ConfigData().get_key_int(interaction.guild.id, "18")
        role21 = ConfigData().get_key_int(interaction.guild.id, "21")
        role25 = ConfigData().get_key_int(interaction.guild.id, "25")
        add_to_user.append(role18)
        add_to_user.append(role21)
        add_to_user.append(role25)
        rm = []
        ra = []
        for role in rem_from_user:
            r = interaction.guild.get_role(role)
            ra.append(r)
        for role in add_to_user + returns:
            r = interaction.guild.get_role(role)
            rm.append(r)
        await user.remove_roles(*rm, reason="returning to lobby")
        await user.add_roles(*ra, reason="returning to lobby")
        await send_embed(interaction, title="User returned to lobby", body=f"{user.mention} has been moved back to the lobby by {interaction.user.mention}")

    @app_commands.command()
    @permissions.check_app_roles()
    async def agecheck(self, interaction: discord.Interaction, dob: str):
        """Checks the age of a dob"""
        age = AgeCalculations.dob_to_age(dob)
        await interaction.response.send_message(f"As of today {dob} is {age} years old", ephemeral=True)  # type: ignore

    @commands.command(name="18a")
    @permissions.check_roles()
    async def _18a(self, ctx: commands.Context, user: discord.Member, age: int, dob: str):
        """allows user to enter"""
        dob = AgeCalculations.regex(dob)
        await LobbyProcess.approve_user(ctx.guild, user, dob, age, ctx.author.name)
        await ctx.message.delete()

    @commands.command(name="21a")
    @permissions.check_roles()
    async def _21a(self, ctx: commands.Context, user: discord.Member, age: int, dob: str):
        """allows user to enter"""
        dob = AgeCalculations.regex(dob)
        await LobbyProcess.approve_user(ctx.guild, user, dob, age, ctx.author.name)
        await ctx.message.delete()

    @commands.command(name="25a")
    @permissions.check_roles()
    async def _25a(self, ctx: commands.Context, user: discord.Member, age: int, dob: str):
        """allows user to enter"""
        dob = AgeCalculations.regex(dob)
        await LobbyProcess.approve_user(ctx.guild, user, dob, age, ctx.author.name)
        await ctx.message.delete()

    @app_commands.command()
    @permissions.check_app_roles_admin()
    async def purge(self, interaction: discord.Interaction, days: int = 14):
        """This command will kick all the users that have not been processed through the lobby with the given days."""
        lobby_config = ConfigData().get_key_int(interaction.guild.id, "lobby")
        lobby_channel = interaction.guild.get_channel(lobby_config)
        if days > 14:
            days = 14
            await interaction.channel.send("Max days is 14, setting to 14")

        view = confirmAction()
        await view.send_message(interaction,
                                f"Are you sure you want to purge the lobby of users that have not been processed in "
                                f"the last {days} days?")
        await view.wait()
        if view.confirmed is False:
            await interaction.followup.send("Purge cancelled")
            return
        days_to_datetime = datetime.datetime.now() - datetime.timedelta(days=days)
        kicked = []
        async for x in lobby_channel.history(limit=None, after=days_to_datetime):
            if x.author.bot is False:
                continue
            for a in x.mentions:
                try:
                    await a.kick()
                    kicked.append(f"{a.name}({a.id})")
                except Exception as e:
                    print(f"unable to kick {a} because {e}")
            await x.delete()
        with open("config/kicked.txt", "w") as file:
            str_kicked = "\n".join(kicked)
            file.write(f"these users were removed during the purge:\n")
            file.write(str_kicked)
        await interaction.channel.send(f"{interaction.user.mention} Kicked {len(kicked)}",
                                       file=discord.File(file.name, "kicked.txt"))
        os.remove("config/kicked.txt")

    @app_commands.command()
    @app_commands.choices(operation=[Choice(name=x, value=x) for x in
                                     ['add', 'update', 'get', 'delete']])
    @app_commands.choices(idcheck=[Choice(name=x, value=y) for x, y in
                                   {"Yes": "True", "No": "False"}.items()])
    @permissions.check_app_roles()
    async def idcheck(self, interaction: discord.Interaction, operation: Choice['str'], idcheck: Choice['str'],
                      userid: str):
        """adds user to id check or removes them"""
        userid = int(userid)
        if idcheck.value == "True":
            idcheck = True
        elif idcheck.value == "False":
            idcheck = False
        if operation.value.upper() not in ["ADD", "UPDATE"]:
            await interaction.response.defer(ephemeral=False)
        match operation.value.upper():
            case "UPDATE":
                reason = await inputmodal.send_modal(interaction, "Please enter a reason")
                VerificationTransactions.update_check(userid, reason, idcheck)
                await send_embed(interaction, title="User id check updated", body=f"<@{userid}>'s id check has been updated to: {idcheck} with reason: `{reason}`")

            case "ADD":
                reason = await inputmodal.send_modal(interaction, "Please enter a reason")
                VerificationTransactions.add_idcheck(userid, reason, idcheck)
                await send_embed(interaction, title="User id check added", body=f"<@{userid}>'s id check has been added with idcheck: {idcheck} and reason: `{reason}`")
            case "GET":
                user = VerificationTransactions.get_id_info(userid)
                if user is None:
                    await interaction.followup.send("Not found")
                    return
                await send_embed(interaction, title="User id check info", body="**__USER INFO__**\n"
                                                                               f"user: <@{user.uid}>\n"
                                                                               f"Reason: {user.reason}\n"
                                                                               f"idcheck: {user.idcheck}\n"
                                                                               f"idverifier: {user.idverified}\n"
                                                                               f"verifieddob: {user.verifieddob}\n")

            case "DELETE":
                if permissions.check_admin(interaction.user) is False:
                    await interaction.followup.send("You are not an admin")
                    return
                if VerificationTransactions.set_idcheck_to_false(userid) is False:
                    await interaction.followup.send(f"Can't find entry: <@{userid}>")
                    return
                await send_embed(interaction, title="User id check deleted", body=f"Deleted entry: <@{userid}>", location="channel")

    # Event

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """posts the button for the user to verify with."""
        try:
            lobby = ConfigData().get_key_int(member.guild.id, "lobby")
            lobbywelcome = ConfigData().get_key(member.guild.id, "lobbywelcome")
        except Exception as e:
            await member.guild.owner.send(f"config error in {member.guild.name}: {e}")
            return
        channel = member.guild.get_channel(lobby)

        await channel.send(f"Welcome {member.mention}! {lobbywelcome}", view=VerifyButton())


async def setup(bot):
    """Adds the cog to the bot."""
    await bot.add_cog(Lobby(bot))
