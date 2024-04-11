import discord


async def send_embed(interaction: discord.Interaction, title: str, body: str, location:str = "followup"):
    embed = discord.Embed(title=title, description=body)
    embed.set_footer(text=interaction.command.name)
    if location.lower() == "followup":
        await interaction.followup.send(embed=embed)
    if location.lower() == "channel":
        await interaction.channel.send(embed=embed)
    if location.lower() == "user":
        await interaction.user.send(embed=embed)
