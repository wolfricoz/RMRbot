from abc import ABC, abstractmethod


class ConfirmDialogue(ABC):
    @abstractmethod
    @staticmethod
    async def confirm(bot, discord, interaction, desc, title):
        def check(m):
            return m.content is not None and m.channel == interaction.channel

        confirm = True
        msg = None
        embed = discord.Embed(title=title, description=desc)
        conf = await interaction.channel.send(embed=embed)
        while confirm is True:
            msg = await bot.wait_for('message', check=check, timeout=600)
            if "confirm" in msg.content.lower():
                embed = discord.Embed(title=title, description=desc)
                confirm = False
                await conf.edit(embed=embed)
                await msg.delete()
            elif "cancel" in msg.content.lower():
                desc = "Cancelled!"
                embed = discord.Embed(title=f"Roleplay Roulette", description=desc)
                await conf.edit(embed=embed)
                return
        return msg

    @abstractmethod
    async def input(bot, discord, interaction, desc, title):
        def check(m):
            return m.content is not None and m.channel == interaction.channel and m.author == interaction.user

        embed = discord.Embed(title=title, description=desc)
        conf = await interaction.channel.send(embed=embed)
        msg = await bot.wait_for('message', check=check, timeout=600)
        return msg.content
