import json
import os
import sys

import discord

sys.path.append('/home/usename/.local/lib/python2.7/site-packages/')
import gspread
from discord import app_commands
from discord.ext import commands


class GetSendGather(commands.Cog):

  def __init__(self, client: commands.Bot):
    self.client = client
    self.gc = gspread.service_account(
        filename="flagcapturedata-319e906a9631.json")
    self.flag_data_workbook = self.gc.open("FlagData")
    self.allowed_guilds = [383365467894710272, 1045479020940234783]  # gui

  async def guild_is_allowed(self, interaction: discord.Interaction):
    return interaction.guild and interaction.guild.id in self.allowed_guilds

  async def user_is_admin(self, interaction: discord.Interaction):
    if interaction.guild is None:
        return False 
    member = interaction.guild.get_member(interaction.user.id)
    return any(role.name.lower() == 'admin' for role in member.roles)

  def get_guild_specific_filename(self, guild_id: int, base_filename: str = "RssDepletion.json"):
    """Generates a guild-specific filename for storing data."""
    return f"cogs/cogfiles/RssDepletion_{guild_id}.json"

  def ensure_file_exists(self, filepath):
    """Ensure the JSON file for the guild exists. If not, creates an empty JSON list file."""
    if not os.path.exists(filepath):
      os.makedirs(os.path.dirname(filepath), exist_ok=True)
      with open(filepath, 'w', encoding='utf-8') as file:
        json.dump([], file)

  @app_commands.command(name='retrieve_gathering_history')
  async def retrieve_gathering_history(self, interaction):
      if not await self.guild_is_allowed(interaction):
        await interaction.response.send_message("Your server does not have access to this feature.", ephemeral=True)
        return
      if not await self.user_is_admin(interaction):
        await interaction.response.send_message("You must be an admin to use this command.", ephemeral=True)
        return

      guild_id = interaction.guild.id
      guild_specific_filename = self.get_guild_specific_filename(guild_id)
      self.ensure_file_exists(guild_specific_filename)  # Ensure file exists before attempting to write
      sheet = self.flag_data_workbook.worksheet("GatheringHistory")
      data = sheet.get_all_records()

      with open(guild_specific_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
      await interaction.response.send_message(
          "Gathering history data retrieved successfully.")

  @app_commands.command(name='send_gathering_history')
  async def send_gathering_history(self, interaction):
    if not await self.guild_is_allowed(interaction):
      await interaction.response.send_message("Your server does not have access to this feature.", ephemeral=True)
      return
    if not await self.user_is_admin(interaction):
      await interaction.response.send_message("You must be an admin to use this command.", ephemeral=True)
      return

    guild_id = interaction.guild.id
    guild_specific_filename = self.get_guild_specific_filename(guild_id)
    self.ensure_file_exists(guild_specific_filename)  # Ensure file exists before attempting to read
    with open(guild_specific_filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    sheet = self.flag_data_workbook.worksheet("GatheringHistory")
    values = [['Date', 'Resource Type', 'Occupants', 'Gathering Rate', 'Ran By']]
    values += [[item['date_run'], item['resource_type'], item['number_of_gathers'],
                item['gathering_rate'], item['ran_by']] for item in data]

    sheet.clear()
    sheet.update('A1', values)

    await interaction.response.send_message(
        "Gathering history sent to Google Sheet successfully.")


async def setup(client: commands.Bot) -> None:
  await client.add_cog(GetSendGather(client))