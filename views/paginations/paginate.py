from abc import ABC, abstractmethod

import discord

import classes.permissions as permissions
from classes.databaseController import UserTransactions, ConfigData, DatabaseTransactions


# noinspection PyUnresolvedReferences
class PaginationView(discord.ui.View):
    current_page: int = 1
    sep: int = 1
    data: list = []
    warndict: dict = {}
    username = None

    def __init__(self):
        super().__init__(timeout=300)

    async def send(self, interaction):
        self.message = await interaction.channel.send(view=self)
        await self.update_message(self.data[:self.sep])
        await interaction.response.send_message("Gettng user data", ephemeral=True)

    def create_embed(self, data):
        embed = discord.Embed(title=f"User {self.warningtype} warnings")
        for item in data:
            embed.add_field(name=f"{self.warningtype} id: {item}", value=self.warndict.get(item, "Warning not found"), inline=False)
        return embed

    def get_current_page_data(self):
        until_item = self.current_page * self.sep
        from_item = until_item - self.sep
        return self.data[from_item:until_item]

    async def update_message(self, data):
        if len(self.data) == 0:
            await self.message.channel.send(f"No {self.warningtype} entries to display for {self.username}")
            await self.message.delete()
            return
        self.update_buttons()
        await self.message.edit(embed=self.create_embed(data), view=self)

    def update_buttons(self):
        if self.current_page == 1:
            self.first_page_button.disabled = True
            self.prev_button.disabled = True
            self.first_page_button.style = discord.ButtonStyle.gray
            self.prev_button.style = discord.ButtonStyle.gray
        else:
            self.first_page_button.disabled = False
            self.prev_button.disabled = False
            self.first_page_button.style = discord.ButtonStyle.green
            self.prev_button.style = discord.ButtonStyle.primary

        if self.current_page == int(len(self.data) / self.sep):
            self.last_page_button.disabled = True
            self.next_button.disabled = True
            self.last_page_button.style = discord.ButtonStyle.gray
            self.next_button.style = discord.ButtonStyle.gray
        else:
            self.last_page_button.disabled = False
            self.next_button.disabled = False
            self.last_page_button.style = discord.ButtonStyle.green
            self.next_button.style = discord.ButtonStyle.primary

    @discord.ui.button(label="First", style=discord.ButtonStyle.green)
    @permissions.check_app_roles()
    async def first_page_button(self, interaction: discord.Interaction, button: discord.ui.button()):
        await interaction.response.defer()
        self.current_page = 1
        await self.update_message(self.get_current_page_data())

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.button()):
        await interaction.response.defer()
        self.current_page -= 1
        await self.update_message(self.get_current_page_data())

    @discord.ui.button(label="🗑️", style=discord.ButtonStyle.primary)
    async def delete_item_button(self, interaction: discord.Interaction, button: discord.ui.button()):
        await interaction.response.defer(ephemeral=True)
        user_roles = [x.id for x in interaction.user.roles]
        admin_roles = ConfigData().get_key(interaction.guild.id, "ADMIN")

        if not any(x in admin_roles for x in user_roles):
            await interaction.followup.send(f"{interaction.user.mention}: No permission to remove warnings.")
            return
        pgdata = self.get_current_page_data()

        UserTransactions.user_remove_warning(int(pgdata[0]))
        self.data.pop(self.current_page - 1)
        self.current_page = 1
        await self.update_message(self.get_current_page_data())

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.button()):
        await interaction.response.defer()
        self.current_page += 1
        await self.update_message(self.get_current_page_data())

    @discord.ui.button(label="Last", style=discord.ButtonStyle.green)
    async def last_page_button(self, interaction: discord.Interaction, button: discord.ui.button()):
        await interaction.response.defer()
        self.current_page = int(len(self.data) / self.sep)
        await self.update_message(self.get_current_page_data())


class paginate(ABC):
    @staticmethod
    @abstractmethod
    async def create_pagination_user(interaction, user, wtype, warningtype="official"):
        data, warndict = UserTransactions.user_get_warnings(user.id, wtype)
        pagination_view = PaginationView()
        pagination_view.data = data
        pagination_view.warndict = warndict
        pagination_view.username = user.name
        pagination_view.warningtype = warningtype
        await pagination_view.send(interaction)

    @staticmethod
    @abstractmethod
    async def create_pagination_table(interaction, table_name, warningtype="official"):
        data, warndict = DatabaseTransactions.get_all_timers(table_name)
        pagination_view = PaginationView()
        pagination_view.data = data
        pagination_view.warndict = warndict
        pagination_view.username = "search bans"
        pagination_view.warningtype = warningtype
        await pagination_view.send(interaction)
