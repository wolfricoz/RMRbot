"""Allowing and denying users based on age."""
import discord

from classes.databaseController import ConfigData, VerificationTransactions
from classes.lobbyprocess import LobbyProcess


class AgeButtons(discord.ui.View):
    def __init__(self, age: int = None, dob: str = None, user: discord.Member = None):
        self.age = age
        self.dob = dob
        self.user = user
        super().__init__(timeout=None)

    @discord.ui.button(label="Allow", style=discord.ButtonStyle.green, custom_id="allow")
    async def allow(self, interaction: discord.Interaction, button: discord.ui.Button):
        """starts approving process"""
        if self.age is None or self.dob is None or self.user is None:
            await interaction.response.send_message('The bot has restarted and the data of this button is missing. Please use the command.', ephemeral=True)
            return
        await interaction.response.send_message('User approved.', ephemeral=True)
        button.disabled = True
        # Share this with the age commands
        await LobbyProcess.approve_user(interaction.guild, self.user, self.dob, self.age, interaction.user.name)

    @discord.ui.button(label="Manual ID Check", style=discord.ButtonStyle.red, custom_id="ID")
    async def manual_id(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Flags user for manual id."""
        if self.user is None:
            await interaction.response.send_message('The bot has restarted and the data of this button is missing. Please manually report user to admins',
                                                    ephemeral=True)
        await interaction.response.send_message('User flagged for manual ID.', ephemeral=True)
        idcheck = ConfigData().get_key_int(interaction.guild.id, "idlog")
        admin = ConfigData().get_key(interaction.guild.id, "admin")
        idlog = interaction.guild.get_channel(idcheck)
        VerificationTransactions.set_idcheck_to_true(self.user.id, f"manually flagged by {interaction.user.name}")
        await idlog.send(
                f"<@&{admin[0]}> {interaction.user.mention} has flagged {self.user.mention} for manual ID.")
        return

    @discord.ui.button(label="add to db", style=discord.ButtonStyle.primary, custom_id="add")
    async def add_to_db(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Adds user to db"""
        age_log = ConfigData().get_key_int(interaction.guild.id, "lobbylog")
        age_log_channel = interaction.guild.get_channel(age_log)
        if self.user is None:
            await interaction.response.send_message('The bot has restarted and the data of this button is missing. Please add the user manually.',
                                                    ephemeral=True)
        await LobbyProcess.age_log(age_log_channel, self.user.id, self.dob, interaction)
        self.disable_buttons()
        await interaction.message.add_reaction("✅")
        await interaction.response.send_message('User added to database.', ephemeral=True)
        return

    def disable_buttons(self):
        """disables buttons"""
        self.manual_id.disabled = True
        self.manual_id.style = discord.ButtonStyle.grey

        self.allow.disabled = True
        self.allow.style = discord.ButtonStyle.grey

        self.add_to_db.disabled = True
        self.add_to_db.style = discord.ButtonStyle.grey
