import typing

import discord
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands

import classes.permissions as permissions
from classes.databaseController import ConfigData
from classes.moduser import ModUser


# noinspection PyUnresolvedReferences
class moderation(commands.Cog, name="Moderation"):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="watchlist")
    @permissions.check_app_roles()
    async def watchlist(self, interaction: discord.Interaction, user: discord.Member, *, reason: str):
        await interaction.response.send_message(f"adding {user} to watchlist", ephemeral=True)
        bot = self.bot
        # warnchannel = bot.get_channel(537365631675400192)
        watchlist = bot.get_channel(661375573649522708)
        await watchlist.send(f"""Name: {user.mention}
UID: {user.id}
username: {user}
reason {reason}""")

    async def ban_autocompletion(self, interaction: discord.Interaction, current: str) -> typing.List[app_commands.Choice[str]]:
        data = []
        search_commands = ConfigData().get_key(interaction.guild.id, "BAN")
        data.append(app_commands.Choice(name="custom", value="custom"))
        for x in search_commands:
            if current.lower() in x.lower():
                data.append(app_commands.Choice(name=x.lower(), value=x.lower()))
        return data

    @app_commands.command(name="ban")
    @app_commands.choices(
            appeal=[
                Choice(name="Yes", value="To appeal this ban, you can send an email to roleplaymeetsappeals@gmail.com"),
                Choice(name="No", value="This ban is permanent and can not be appealed.")
            ],
            idlist=[
                Choice(name="Yes", value="yes"),
                Choice(name="No", value="no")
            ]
    )
    @app_commands.autocomplete(type=ban_autocompletion)
    @permissions.check_app_roles_admin()
    async def banc(self, interaction: discord.Interaction, type: str, member: discord.User = None,
                   memberid: str = None, *, reason: str = "You have been banned by an admin",
                   appeal: Choice[str], idlist: Choice[str]) -> None:
        """Bans user from ALL Roleplay Meets servers. Use memberid if user is not in server."""
        await interaction.response.defer(ephemeral=True)
        bans: dict = ConfigData().get_key(interaction.guild.id, "BAN")
        print(bans)
        reason = bans.get(type.upper(), reason)
        print(reason)
        bot = self.bot
        if memberid is None and member is None:
            await interaction.followup.send("Please fill in the member or memberid field.")
        try:
            await ModUser.ban_user(interaction, member, bot, reason, appeal, idlist)
        except Exception as e:
            print(e)
            if memberid is None:
                await interaction.followup.send("User is not in the server, please use Memberid")
                return
            member = await self.bot.fetch_user(int(memberid))
            await ModUser.ban_user(interaction, member, bot, reason, appeal, idlist)

    @app_commands.command(name="kick")
    @permissions.check_app_roles()
    async def kick(self, interaction: discord.Interaction, user: discord.Member, *, reason: str = None):
        await interaction.response.send_message(f"Kicking {user}", ephemeral=True)
        try:
            await user.send(
                    f"you've been kicked from {interaction.guild.name} for {reason} \n \n You may rejoin once your behavior improves.")
        except discord.Forbidden:
            await interaction.channel.send("Error: user could not be dmed.")
        await user.kick(reason=reason)
        await ModUser.log(interaction, user, reason, interaction.guild, typeofaction="kicked")

    @app_commands.command(name="notify")
    @permissions.check_app_roles()
    async def notify(self, interaction: discord.Interaction, user: discord.Member, *, reason: str):
        await interaction.response.defer()
        await user.send(f"{interaction.guild.name} **__Notification__**: {reason} ")
        await interaction.followup.send(f"{user.mention} has been notified about {reason}")

    # @app_commands.command(name="searchban", description="ADMIN adcommand: search bans the users")
    # @app_commands.choices(time=[
    #     Choice(name="one week", value="for **1 Week**"),
    #     Choice(name="two weeks", value="for **2 Weeks**"),
    #     Choice(name="1 month", value="for **1 Month**"),
    #     Choice(name="permanent", value="**permanently**"),
    #     Choice(name="custom", value=f"custom"),
    # ])
    # @adefs.check_slash_admin_roles()
    # async def searchban(self, interaction: discord.Interaction, member: discord.Member, time: Choice[str],
    #                     custom: str = None) -> None:
    #     await interaction.response.defer(ephemeral=True)
    #     tz = pytz.timezone("US/Eastern")
    #     bot = self.bot
    #     searchbanrole = discord.utils.get(interaction.guild.roles, id=538809717808693248)
    #     await member.add_roles(searchbanrole)
    #     current = datetime.now(tz)
    #     cooldown = None
    #     if time.name == "one week":
    #         cooldown = current + timedelta(weeks=1)
    #     elif time.name == "two weeks":
    #         cooldown = current + timedelta(weeks=2)
    #     elif time.name == "1 month":
    #         cooldown = current + timedelta(days=30)
    #     else:
    #         pass
    #     reason = f"{interaction.guild.name} **__SEARCH BAN__**: Hello, I'm a staff member from RMR. Due to your frequent refusal to follow our search rules concerning ads, your ad posting privileges have been revoked and you've been given a search ban {time.value}. Please use this time to thoroughly review RMR's rules. Continued refusal to follow the server's search rules can result in a permanent search ban. This search ban expires on {cooldown.strftime('%m/%d/%Y %I:%M:%S %p')} EST."
    #     customr = f"{interaction.guild.name} **__SEARCH BAN__**: Hello, I'm a staff member from RMR. Due to your frequent refusal to follow our search rules concerning ads, your ad posting privileges have been revoked and you've been given a search ban for {custom}. Please use this time to thoroughly review RMR's rules. Continued refusal to follow the server's search rules can result in a permanent search ban."
    #     if time.value == "custom":
    #         await member.send(customr)
    #         await jsonmaker.Configer.addwarning(self, member, interaction, customr)
    #         await ModUser.searchban(interaction, member, customr, interaction.guild, custom)
    #         await interaction.followup.send(
    #             f"{member.mention} has been search banned for {custom}\n(Note: the bot currently does not auto remove the role.)")
    #     else:
    #         await member.send(reason)
    #         await jsonmaker.Configer.addwarning(self, member, interaction, reason)
    #         await ModUser.searchban(interaction, member, customr, interaction.guild, time.value)
    #         await interaction.followup.send(
    #             f"{member.mention} has been search banned {time.value} ({cooldown.strftime('%m/%d/%Y %I:%M:%S %p')})\n(Note: the bot currently does not auto remove the role.)")


async def setup(bot: commands.Bot):
    await bot.add_cog(moderation(bot))
