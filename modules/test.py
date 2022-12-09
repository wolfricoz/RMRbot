import logging
import traceback
from time import sleep

from discord import app_commands
import discord
from discord import Button, ButtonStyle
from discord.ext import commands
from abc import ABC, abstractmethod
import db
import adefs
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, column
from datetime import datetime, timedelta
import re
import typing
import logging

Session = sessionmaker(bind=db.engine)
session = Session()

q_list = [
    'What is your Discord username? (eg: Rico Stryker#6666)',
    'What is your age and dob?',
    "Please list a minimum of 5 kinks and/or extremes you incorporate into your roleplay and a maximum of 10 for us. "
    "(Note: Your application will be denied with less than 5 listed. Don't worry, everyone has to do this!)",
    "By joining After Dark, you agree to keep everything that happens within the channels. "
    "No blackmail or outing people outside of After Dark will be tolerated. Please type 'Agree' if you agree.",
    "If you have an F-List link or kinklist, please link that here!",
    "What makes you a good candidate for After Dark?",
    "What made you interested in After Dark?"""
]

a_list = []

class Buttons(discord.ui.View,):
    def __init__(self, *, timeout=None):
        super().__init__(timeout=timeout)
    @discord.ui.button(label="Accept",style=discord.ButtonStyle.green,emoji="✅")
    async def blurple_button(self,button:discord.ui.Button,interaction:discord.Interaction):
        await interaction.user.send("Accepted!")
        await interaction.response.edit_message(view=self)
    @discord.ui.button(label="Decline",style=discord.ButtonStyle.red,emoji="❌")
    async def red_button(self,button:discord.ui.Button,interaction:discord.Interaction):
        await interaction.user.send("Declined!")
        await interaction.response.edit_message(view=self)


class Test(commands.Cog, name="test"):

    def __init__(self, bot: commands.Bot):
        self.bot = bot


    #code found online
    @commands.command(aliases=['adapply'])
    async def staff_application(self, ctx):
        a_list = []
        submit_channel = self.bot.get_channel(478965604225908756)
        channel = await ctx.author.create_dm()

        def check(m):
            return m.content is not None and m.channel == channel

        for question in q_list:
            await channel.send(question)
            msg = await self.bot.wait_for('message', check=check)
            a_list.append(msg.content)

        # submission to channel
        submit_wait = True
        while submit_wait:
            await channel.send('End of questions - "submit" to finish')
            msg = await self.bot.wait_for('message', check=check)
            if "submit" in msg.content.lower():
                submit_wait = False
                await channel.send("Thank you for applying, please wait while we manually process your application. "
                             "\nThis may take 1-3 days.")
                embed = discord.Embed(title=f"{msg.author}'s Application")
                embed.set_footer(text=msg.author.id)
                # Answer
                for i, (q, a) in enumerate(zip(q_list , a_list), 1):
                    embed.add_field(name=f"{i}. {q}", value=a, inline=False)
                #buttons
                button = Button(label="Approve", style=discord.ButtonStyle.green, emoji="✅")
                async def button_callback(interaction, msg):
                    await msg.author.send("Your post was approved")
                button.callback = button_callback(msg=msg)
                view = Buttons()
                view.add_item(button)
                await submit_channel.send(embed=embed, view=view)
                print(f'{a}. {b}' for a, b in enumerate(a_list, 1))
                #TODO: Buttons to accept or deny


async def setup(bot: commands.Bot):
    await bot.add_cog(Test(bot))
