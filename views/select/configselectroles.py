import discord

from discord.ui import UserSelect
from discord.ui import ChannelSelect
# Only roles?
from discord.ui import RoleSelect
# Members and roles in one?
from discord.ui import MentionableSelect

# import for the decorator and callback...
from discord import ui, Interaction

# using...
# this example uses the UserSelect
class ConfigSelectChannels(ui.View):
    # @ui.select(cls=type_we_want, **other_things)
    @ui.select(cls=ChannelSelect, placeholder="Select a channel please!")
    async def my_user_select(self, interaction: Interaction, select: UserSelect):
        # handle the selected users here
        # select.values is a list of User or Member objects here
        # it will be a list of Role if you used RoleSelect
        # it will be a list of both Role and Member/User if you used MentionableSelect

        self.value = [user.id for user in select.values]
        await interaction.response.edit_message()
        self.stop()

    @ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = None
        self.stop()

class ConfigSelectRoles(ui.View):
    # @ui.select(cls=type_we_want, **other_things)
    @ui.select(cls=RoleSelect, placeholder="Select a channel please!")
    async def my_user_select(self, interaction: Interaction, select: UserSelect):
        # handle the selected users here
        # select.values is a list of User or Member objects here
        # it will be a list of Role if you used RoleSelect
        # it will be a list of both Role and Member/User if you used MentionableSelect

        self.value = [user.id for user in select.values]
        await interaction.response.edit_message()
        self.stop()

    @ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = None
        self.stop()


# class ConfigSelectRoles(discord.ui.RoleSelect):
#     def __init__(self):
#         super().__init__(placeholder="Select a role")
#
#
#     async def callback(self, interaction: discord.Interaction):
#         await interaction.response.send_message(content=f"Your choice is {self.values[0]}!", ephemeral=True)
#
#     async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
#         print(error)
#         await interaction.response.send_message('Oops! Something went wrong.\n'
#                                                 f'{error}')
#         raise error
#
# class MyView(discord.ui.View):
#   def __init__(self, ctx):
#         super().__init__(timeout = 300)
#         self.ctx = ctx
#   @discord.ui.select(cls = discord.ui.RoleSelect, custom_id="menu_dump_RoleSelect" , placeholder="Select another role here...")
#   async def menu_dump_RoleSelect_callback(self, interaction: discord.Interaction, select: discord.ui.RoleSelect):
#

# class SelectView(discord.ui.View):
#     def __init__(self, *, timeout=180):
#         super().__init__(timeout=timeout)
#         self.add_item(Select())
