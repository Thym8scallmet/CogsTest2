import discord
from discord import app_commands
from discord.ext import commands
import gspread
import json

class GetFlagData(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.gc = gspread.service_account(filename="flagcapturedata-319e906a9631.json")  # Client
        self.sheet = self.gc.open("FlagData").sheet1  # Spreadsheet

    @app_commands.command(name='get_flag_data')
    async def get_flag_data(self, interaction: discord.Interaction):
        # Fetch all data from the spreadsheet
        data = self.sheet.get_all_records()
        # Convert data to player list format
        player_list = [{'name': row['Name'], 'might': int(row['Might'])} for row in data if row['Name'] and row['Might']]
        # Write to playerlist.json
        with open('playerlist.json', 'w', encoding='utf-8') as f:
            json.dump(player_list, f, ensure_ascii=False, indent=4)
        await interaction.response.send_message("Data imported and saved successfully into playerlist.json")

async def setup(client: commands.Bot) -> None:
    await client.add_cog(GetFlagData(client))