# Standard library imports
import datetime
import json
import os

# Third-party imports
import discord
from discord import Embed, File, app_commands
from discord.ext import commands

class RssDepletion(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client

    async def store_depletion_info(self, guild_id: int, date_run: str, resource_type: str,
                                   number_of_gathers: int, gathering_rate: float,
                                   ran_by: str):
        data = {
            "Date": date_run,
            "Resource Type": resource_type,
            "Occupants": number_of_gathers,
            "Gathering Rate": gathering_rate,
            "Ran By": ran_by
        }

        file_path = f'cogs/cogfiles/RssDepletion_{guild_id}.json'
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump([], file, indent=4)  # Create a new file with an empty list if it does not exist

        with open(file_path, 'r+', encoding='utf-8') as file:
            file_data = json.load(file)
            file_data.append(data)
            file.seek(0)
            file.truncate()
            json.dump(file_data, file, indent=4)

    class RssModal(discord.ui.Modal):

        def __init__(self, title: str, mill_type: str, client: commands.Bot, guild_id: int):
            super().__init__(title=title)
            self.mill_type = mill_type
            self.client = client
            self.guild_id = guild_id

        starting_amount = discord.ui.TextInput(
            label="Starting Amount",
            style=discord.TextStyle.short,
            placeholder="Enter the starting amount here")
        amount_after_one_minute = discord.ui.TextInput(
            label="Amount After One Minute",
            style=discord.TextStyle.short,
            placeholder="Enter the amount after one minute here")
        number_of_gathers = discord.ui.TextInput(
            label="Number of Gathers",
            style=discord.TextStyle.short,
            placeholder="Enter the number of gathers here")

        async def on_submit(self, interaction: discord.Interaction):
            await interaction.response.defer()
            try:
                num1 = float(self.starting_amount.value)
                num2 = float(self.amount_after_one_minute.value)
                gathers = int(self.number_of_gathers.value)
            except ValueError:
                await interaction.response.send_message("Please enter valid numbers.")
                return

            rate = num1 - num2
            if rate <= 0:
                await interaction.response.send_message(
                    "Invalid input. The first number must be greater than the second.")
                return

            minutes = num2 / rate
            hours = minutes / 60
            days = hours / 24
            depletion_time_utc = datetime.datetime.utcnow() + datetime.timedelta(minutes=minutes)

            date_run = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            resource_type = self.mill_type
            number_of_gathers = int(self.number_of_gathers.value)
            gathering_rate = rate  # Assuming 'rate' is the gathering rate calculated above
            ran_by = interaction.user.name  # or interaction.user.display_name for the nickname
            await self.client.get_cog('RssDepletion').store_depletion_info(
                self.guild_id, date_run, resource_type, number_of_gathers, gathering_rate, ran_by)

            file_path = 'files/GasfieldSnip.PNG'
            file = File(file_path, filename="GasfieldSnip.PNG")
            embed = discord.Embed(
                title=f"{self.mill_type} Rss Depletion Info",
                description=(
                    f"The starting resource amount is {num1:.0f}\n"
                    f"The amount after 1 minute is {num2:.0f}\n"
                    f"Number of gathers: {gathers}\n"
                    f"Resource Type: {self.mill_type}\n\n"  # Displaying the Resource Type
                    f"Resources are being gathered at: **{rate:.0f}** per minute"),
                colour=discord.Colour.blue(),
                timestamp=discord.utils.utcnow())
            embed.set_thumbnail(url="attachment://GasfieldSnip.PNG")
            embed.add_field(
                name="At the current gathering rate, the mill will be depleted in:",
                value=f"{minutes:.0f} minutes\n{hours:.1f} hours\n{days:.1f} days",
                inline=False)
            embed.add_field(
                name="The mill will be depleted by:",
                value=f"{depletion_time_utc.strftime('%a, %B %#d, %Y, %I:%M %p UTC')}",
                inline=False)
            embed.add_field(name="Local Time for mill depletion:",
                            value=f"<t:{int(depletion_time_utc.timestamp())}:F>",
                            inline=False)
            embed.set_footer(
                text=f"\nThis command was run by {interaction.user.display_name}")

            await interaction.followup.send(file=file, embed=embed)

    @app_commands.command(
        name='rss_depletion',
        description='Calculate resource depletion time and rate')
    @app_commands.choices(mill_type=[
        app_commands.Choice(name="Food", value="Food"),
        app_commands.Choice(name="Wood", value="Wood"),
        app_commands.Choice(name="Steel", value="Steel"),
        app_commands.Choice(name="Gas", value="Gas")
    ])
    async def rss_depletion(self, interaction: discord.Interaction,
                            mill_type: app_commands.Choice[str]):
        if interaction.guild is None:
            await interaction.response.send_message("This command cannot be used in DMs.", ephemeral=True)
            return
        modal = self.RssModal(title="Resource Depletion Information",
                              mill_type=mill_type.value,
                              client=self.client,
                              guild_id=interaction.guild.id)
        await interaction.response.send_modal(modal)

    @app_commands.command(
        name='gathering_history',
        description='Displays the history of gathering activities')
    async def gathering_history(self, interaction: discord.Interaction):
        file_path = f'cogs/cogfiles/RssDepletion_{interaction.guild.id}.json'
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except FileNotFoundError:
            await interaction.response.send_message('No gathering history found.', ephemeral=True)
            return

        header_text = "Below is the history of all resource gathering activities:"
        embed = Embed(title='Gathering History', description=header_text, colour=discord.Colour.blue())

        for entry in data:
            date_obj = datetime.datetime.strptime(entry['Date'], '%Y-%m-%d %H:%M:%S')
            formatted_date = date_obj.strftime('%b %d, %H:%M')  # e.g., Apr 02 00:19
            # Format the entry as a field
            entry_description = f"Type: **{entry['Resource Type']}**\xa0\xa0\xa0\xa0Gathering Rate: **{entry['Gathering Rate']}**\xa0\xa0\xa0\xa0Occupants: **{entry['Occupants']}**"

            embed.add_field(name=f"Date: {formatted_date} UTC",
                            value=entry_description,
                            inline=False)

        if not embed.fields:
            # If no data was added to the embed
            embed.description = 'No history data available.'
        await interaction.response.send_message(embed=embed)

async def setup(client: commands.Bot) -> None:
    await client.add_cog(RssDepletion(client))