import discord


async def send_embed(interaction: discord.Interaction, title: str, body: str):
    embed = discord.Embed(title=title, description=body)
    embed.set_footer(text=interaction.command.name)
    await interaction.followup.send(embed=embed)
