@bot.command()
async def poke(ctx, user: discord.Member = None):
    if user is None:
        await ctx.send("Incorrect Syntax:\nUsage: `r?poke [user]`")

    await user.send("boop")
    channel = bot.get_channel(987679198560796713)
    await channel.send('User {} has been dmed'.format(user))





@bot.command()
async def getmsg(ctx, msgID: int):
    msg = None
    for channel in ctx.guild.text_channels:
        try:
            msg = await channel.fetch_message(msgID)
            await ctx.send(msg.content)
        except discord.errors.NotFound:
            continue
        else:
            return
    if not msg:
        await ctx.send("ID invalid")
    # means that the given messageId is invalid


#future code
    @commands.command(aliases=[])
    @adefs.check_db_roles()
    async def ban(ctx, user : discord.User, type,*, reason=None):
        cembed = discord.Embed(title="User Banned", description=f"{ctx.message.author.mention} has banned {user.mention} for {reason}")
        bembed = discord.Embed(title="User Banned", description=f"Hi, I am a bot of Roleplay Meets Reborn. {user.mention} you've been banned for {reason}")
        if user == None or user == ctx.message.author:
            ctx.send("Invalid user")
        else:
            match type.lower:
                case "id":
                    reason = ""
                case "pedo":
                case "":
                case "custom":
                case default:
                    await ctx.send("""Syntax: ?ban @user type reason
Types: id, Pedo, """)

        @commands.command(aliases=[])
        @adefs.check_db_roles()
        async def warn(ctx, user : discord.User, type, reason=None):
            match type.lower():
                case "":
                case "":
                case "":
                case "custom":
                case default:
                    await ctx.send("")
        @commands.command(aliases=[])
        @adefs.check_db_roles()
        async def notify(ctx, user : discord.User, type, reason=None):
            match type.lower():
                case "":
                case "":
                case "":
                case "custom":
                case default:
                    await ctx.send("")