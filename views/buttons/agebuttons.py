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
        await self.disable_buttons(interaction, button)
        if self.age is None or self.dob is None or self.user is None:
            await interaction.followup.send('The bot has restarted and the data of this button is missing. Please use '
                                            'the command.', ephemeral=True)
            return

        await interaction.followup.send("User approved.", ephemeral=True)
        # Share this with the age commands
        await LobbyProcess.approve_user(interaction.guild, self.user, self.dob, self.age, interaction.user.name)

    @discord.ui.button(label="Manual ID Check", style=discord.ButtonStyle.red, custom_id="ID")
    async def manual_id(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Flags user for manual id."""
        await self.disable_buttons(interaction, button)
        if self.user is None:
            await interaction.followup.send('The bot has restarted and the data of this button is missing. Please manually report user to admins',
                                            ephemeral=True)
        await interaction.followup.send('User flagged for manual ID.', ephemeral=True)
        idcheck = ConfigData().get_key_int(interaction.guild.id, "idlog")
        admin = ConfigData().get_key(interaction.guild.id, "admin")
        idlog = interaction.guild.get_channel(idcheck)
        VerificationTransactions.set_idcheck_to_true(self.user.id, f"manually flagged by {interaction.user.name}")
        await idlog.send(
                f"<@&{admin[0]}> {interaction.user.mention} has flagged {self.user.mention} for manual ID.")
        return

    @discord.ui.button(label="NSFW Warning", style=discord.ButtonStyle.danger, custom_id="NSFW")
    async def nsfw_warning(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Flags user for nsfw warning."""
        await self.disable_buttons(interaction, button)
        if self.user is None:
            await interaction.followup.send('The bot has restarted and the data of this button is missing. Please manually report user to admins',
                                            ephemeral=True)
        await interaction.followup.send('User flagged for NSFW Warning.', ephemeral=True)
        warning = """**NSFW Warning**\n
Hello, this is the moderation team for Roleplay Meets: Reborn and Roleplay Meets: Network. As Discord TOS prohibits NSFW content anywhere that can be accessed without an age gate, we will have to ask that you inspect your profile and remove any NSFW content. This includes but is not limited to: 
* NSFW profile pictures 
* NSFW display names
* NSFW Biographies
* NSFW status messages
* and NSFW game activity. 

Once you've made these changes you may resubmit your age and date of birth. Thank you for your cooperation."""
        await self.user.send(warning)

        return

    @discord.ui.button(label="add to db", style=discord.ButtonStyle.primary, custom_id="add")
    async def add_to_db(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Adds user to db"""
        age_log = ConfigData().get_key_int(interaction.guild.id, "lobbylog")
        age_log_channel = interaction.guild.get_channel(age_log)
        await self.disable_buttons(interaction, button)
        if self.user is None:
            await interaction.followup.send('The bot has restarted and the data of this button is missing. Please add the user manually.',
                                            ephemeral=True)
        await LobbyProcess.age_log(age_log_channel, self.user.id, self.dob, interaction)
        await interaction.message.add_reaction("✅")
        await interaction.followup.send('User added to database.', ephemeral=True)
        return

    async def disable_buttons(self, interaction, button: discord.ui.Button = None):
        """disables buttons"""
        self.manual_id.disabled = True
        self.manual_id.style = discord.ButtonStyle.grey

        self.allow.disabled = True
        self.allow.style = discord.ButtonStyle.grey

        self.add_to_db.disabled = True
        self.add_to_db.style = discord.ButtonStyle.grey

        self.nsfw_warning.disabled = True
        self.nsfw_warning.style = discord.ButtonStyle.grey

        button.style = discord.ButtonStyle.green
        await interaction.response.edit_message(view=self)
