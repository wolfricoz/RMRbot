from discord.ext import commands
from discord import app_commands
import discord
import adefs
from datetime import datetime
from abc import ABC, abstractmethod
from discord.app_commands import Choice
class moduser(ABC):
    @abstractmethod
    async def userbanned(self, ctx, member, bot, reason):
        rguilds = []
        if member == ctx.user:
            await ctx.followup.send(f"Error: user ID belongs to {member.mention}.")
        else:
            for guild in bot.guilds:
                user = guild.get_member(member.id)
                if user is not None:
                    await member.send(
                        f"You've been banned from {guild} with reason: \n {reason} \n\n To appeal this ban, you can send an email to roleplaymeetsappeals@gmail.com")
                    await user.ban(reason=reason, delete_message_days=0)
                    await moduser.banlog(ctx, member, reason, guild)
                    rguilds.append(guild.name)
                else:
                    await ctx.followup.send(f"User was not in {guild}, could not ban. Please do this manually.")
            print(rguilds)
            guilds = ", ".join(rguilds)
            embed = discord.Embed(title=f"{member.name} banned", description=reason)
            embed.set_footer(text=f"User removed from: {guilds}")
            await ctx.channel.send(embed=embed)

    async def banlog(ctx, member, reason, guild):
        embed = discord.Embed(title=f"{member.name} Banned", description=f"**Mention:** {member.mention} \n**UID:** {member.id}\n **Reason:** \n{reason}")
        embed.set_footer(text=datetime.now().strftime('%m/%d/%Y, %H:%M:%S'))
        if guild.id == 395614061393477632:
            log = ctx.bot.get_channel(695112426642997279)
            await log.send(embed=embed)
        if guild.id == 780622396297183252:
            log = ctx.bot.get_channel(851651921823268874)
            await log.send(embed=embed)
    async def kicklog(ctx, member, reason, guild):
        embed = discord.Embed(title=f"{member.name} kicked", description=f"**Mention:** {member.mention} \n**UID:** {member.id}\n **Reason:** \n{reason}")
        embed.set_footer(text=datetime.now().strftime('%m/%d/%Y, %H:%M:%S'))
        if guild.id == 395614061393477632:
            log = ctx.bot.get_channel(695112426642997279)
            await log.send(embed=embed)
        if guild.id == 780622396297183252:
            log = ctx.bot.get_channel(851651921823268874)
            await log.send(embed=embed)
    async def warnlog(ctx, member, reason, guild):
        embed = discord.Embed(title=f"{member.name} warned", description=f"**Mention:** {member.mention} \n**UID:** {member.id}\n **Reason:** \n{reason}")
        embed.set_footer(text=datetime.now().strftime('%m/%d/%Y, %H:%M:%S'))
        await ctx.send(embed=embed)
        if guild.id == 395614061393477632:
            log = ctx.bot.get_channel(537365631675400192)
            await log.send(embed=embed)
        if guild.id == 780622396297183252:
            log = ctx.bot.get_channel(780622396595372039)
            await log.send(embed=embed)

class moderation(commands.Cog, name="Moderation"):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(aliases=["wl"])
    @adefs.check_db_roles()
    async def watchlist(self, ctx, user: discord.Member, *, reason):
        bot = self.bot
        #warnchannel = bot.get_channel(537365631675400192)
        watchlist = bot.get_channel(661375573649522708)
        await ctx.message.delete()
        await watchlist.send(f"""Name: {user.mention}
UID: {user.id}
username: {user}
reason {reason}""")

    @commands.command(aliases=["al","age"])
    @adefs.check_db_roles()
    async def agelist(self, ctx, user: discord.Member,*, age):
        bot = self.bot
        #warnchannel = bot.get_channel(537365631675400192)
        watchlist = bot.get_channel(661375573649522708)
        await ctx.message.delete()
        await watchlist.send(f"""Name: {user.mention}
UID: {user.id}
username: {user}
age: {age}""")

    @app_commands.command(name="ban", description="Bans user from all roleplay meets servers")
    @app_commands.choices(type=[
        Choice(name="Id", value="id"),
        Choice(name="Pedophilia", value="underage"),
        Choice(name="Community", value="community"),
        Choice(name="Custom", value="custom"),
    ])
    @adefs.check_admin_roles()
    async def ban(self, interaction: discord.Interaction, type: Choice[str], member : discord.Member, *, reason:str= "You have been banned by an admin"):
        await interaction.response.defer(ephemeral=True)
        bot = self.bot
        match type.value:
            case "id":
                preason = f"{member.name} you've failed to ID after lying about your age, we'll be banning you from our server, as per our rules: **RMR is restricted to users 18 or older. Lying about your age may put our users (your partners) at risk and may result in an immediate ban. If you refuse to give staff your age in the lobby, you will be refused access to the server and removed.**"
                await moduser.userbanned(self, interaction, member, bot, preason)
            case "underage":
                preason = f"Your roleplay profile/F-list/advert indicate a willingness to write with underaged people and write underaged characters. As we have a strict ban on pedophilia, we have made the decision to ban you from our server. There is no appealing this ban."
                await moduser.userbanned(self, interaction, member, bot, preason)
            case "community":
                preason = f"After discussion amongst the staff and a majority vote, we have decided that you are not fit to remain within RMR. There is no appealing this ban."
                await moduser.userbanned(self, interaction, member, bot, preason)
            case "custom":
                await moduser.userbanned(self, interaction, member, bot, reason)
            case default:
                await interaction.followup.send("Options:\n- ID @user \n- underage @user \n- community @user  \n- Custom @user reason")

    @commands.command(aliases=["k"])
    @adefs.check_db_roles()
    async def kick(self, ctx, user: discord.Member,*, reason=None):
        try:
            await user.send(f"you've been kicked from {ctx.guild.name} for {reason} \n \n You may rejoin once your behavior improves.")
        except:
            await ctx.send("Error: user could not be dmed.")
        await user.kick(reason=reason)
        await moduser.kicklog(ctx, user, reason, ctx.guild)
        await ctx.message.delete()

    @commands.command(aliases=["w"])
    @adefs.check_db_roles()
    async def warn(self, ctx, user: discord.Member,*, reason=None):
        await user.send(f"{ctx.guild.name} **__WARNING__**: You've been warned for: {reason} ")
        await ctx.send(f"{user.mention} has been warned about {reason}")
        await moduser.warnlog(ctx, user, reason, ctx.guild)
        await ctx.message.delete()
    @commands.command(aliases=["n"])
    @adefs.check_db_roles()
    async def notify(self, ctx, user: discord.Member,*, reason=None):
        await user.send(f"{ctx.guild.name} **__Notification__**: {reason} ")
        await ctx.send(f"{user.mention} has been notified about {reason}")
        await ctx.message.delete()






async def setup(bot: commands.Bot):
    await bot.add_cog(moderation(bot))
