import json
import os
from typing import List, Optional

import discord
from discord import app_commands
from discord.ext import commands


class MightDistribution(commands.Cog):

  def __init__(self, client: commands.Bot):
    self.client = client

  async def load_player_data(self, guild_id: int) -> List[dict]:
    file_path = f'playerlist_{guild_id}.json'
    try:
      with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    except FileNotFoundError:
      data = []  # If the file does not exist, start with an empty list
    return sorted(data, key=lambda x: x.get('might', 0), reverse=True)

  async def save_player_data(self, players: List[dict], guild_id: int) -> None:
    file_path = f'playerlist_{guild_id}.json'
    with open(file_path, 'w', encoding='utf-8') as file:
      json.dump(players, file, indent=4)

  async def prepare_embed(self, guild_id: int) -> discord.Embed:
    players = await self.load_player_data(guild_id)
    # Allocate players to lanes to achieve a balanced might distribution
    lane1, lane2 = [], []
    lane3 = players[40:]  # Remaining players go here
    top_40_players = players[:40]

    lane1_might, lane2_might = 0, 0

    for player in top_40_players:
      # Place the player in the lane with the lesser total might
      if lane1_might <= lane2_might:
        lane1.append(player)
        lane1_might += player['might']
      else:
        lane2.append(player)
        lane2_might += player['might']
    lane3_might = sum(player['might'] for player in lane3)

    embed = discord.Embed(
        title="Flag Capture Lane Setup",
        description=
        "Players are divided into three lanes based on balanced might distribution.",
        color=0x00ff00)

    for index, (lane, total_might) in enumerate(zip(
        [lane1, lane2, lane3], [lane1_might, lane2_might, lane3_might]),
                                                start=1):
      lane_description = '\n'.join([
          f"{idx + 1}. {player['name']}: {player['might']:,}"
          for idx, player in enumerate(lane)
      ])
      lane_description += f"\n**Total Might**: {total_might:,}"
      embed.add_field(name=f"Lane {index}",
                      value=lane_description,
                      inline=False)

    return embed

  @commands.Cog.listener()
  async def on_guild_join(self, guild: discord.Guild):
    file_path = f'playerlist_{guild.id}.json'
    if not os.path.exists(file_path):
      with open(file_path, 'w', encoding='utf-8') as file:
        json.dump([], file, indent=4)  # Initialize with an empty list

  @app_commands.command(name="flag_capture_lineup",
                        description="Distributes the might of the players")
  async def might_distribution(self, interaction: discord.Interaction):
    if interaction.guild is not None:
      embed = await self.prepare_embed(interaction.guild.id)
      await interaction.response.send_message(embed=embed)
    else:
      await interaction.response.send_message(
          "This command cannot be used in DMs.", ephemeral=True)

  # Replacing original commands with the consolidated player_upkeep command
  @app_commands.command(
      name="player_upkeep",
      description="Manage player information for flag capture lineup")
  @app_commands.choices(action=[
      app_commands.Choice(name="add_player", value="add"),
      app_commands.Choice(name="remove_player", value="remove"),
      app_commands.Choice(name="adjust_might", value="adjust"),
      app_commands.Choice(name="display_players", value="display"),
      app_commands.Choice(
          name="might_distribution", value="distribute"
      )  # Including might_distribution as a subcommand action
  ])
  async def player_upkeep(self,
                          interaction: discord.Interaction,
                          action: app_commands.Choice[str],
                          name: Optional[str] = None,
                          might: Optional[int] = None):
    if action.value == "add":
      if not name or might is None:
        await interaction.response.send_message(
            "Please provide both a name and a might value.", ephemeral=True)
        return
      if interaction.guild is not None:
        players = await self.load_player_data(interaction.guild.id)
        players.append({"name": name, "might": might})
        await self.save_player_data(players, interaction.guild.id
                                    )  # Updated with guild_id
        await interaction.response.send_message(
            f"Added player {name} with might {might}.")
      else:
        await interaction.response.send_message(
            "This command cannot be used in DMs.", ephemeral=True)

    elif action.value == "remove":
      if not name:
        await interaction.response.send_message(
            "Please provide a player name.", ephemeral=True)
        return
      if interaction.guild is not None:
        players = await self.load_player_data(interaction.guild.id)
        players = [player for player in players if player['name'] != name]
        await self.save_player_data(players, interaction.guild.id
                                    )  # Updated with guild_id
        await interaction.response.send_message(f"Removed player {name}.")
      else:
        await interaction.response.send_message(
            "This command cannot be used in DMs.", ephemeral=True)

    elif action.value == "adjust":
      if not name or might is None:
        await interaction.response.send_message(
            "Please provide both a name and a new might value.",
            ephemeral=True)
        return

      if interaction.guild is not None:
        players = await self.load_player_data(interaction.guild.id)
        for player in players:
          if player['name'] == name:
            player['might'] = might
            await self.save_player_data(players, interaction.guild.id
                                        )  # Updated with guild_id
            await interaction.response.send_message(
                f"Updated {name}'s might to {might}.")
            return
        await interaction.response.send_message(f"Player {name} not found.")
      else:
        await interaction.response.send_message(
            "This command cannot be used in DMs.", ephemeral=True)

    elif action.value == "display":
      await self.display_players(interaction)
    elif action.value == "distribute":
      # Code to call might_distribution directly
      embed = await self.prepare_embed(interaction.guild.id)
      await interaction.response.send_message(embed=embed)

  # Display players command retained for use within player_upkeep
  async def display_players(self, interaction: discord.Interaction):
    if interaction.guild is not None:
      players = await self.load_player_data(interaction.guild.id)
      embed = discord.Embed(title="Players List", color=0x00ff00)
      display_text = '\n'.join(f"{player['name']}: {player['might']}"
                               for player in players)
      embed.description = display_text
      await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
      await interaction.response.send_message(
          "This command cannot be used in DMs.", ephemeral=True)

  # Autocomplete callback function for player names
  async def player_name_autocomplete(
      self, interaction: discord.Interaction,
      current: str) -> List[app_commands.Choice[str]]:
    if interaction.guild is not None:
      players = await self.load_player_data(interaction.guild.id)
      return [
          app_commands.Choice(name=player['name'], value=player['name'])
          for player in players if current.lower() in player['name'].lower()
      ][:25]  # Limit to 25 entries
    else:
      return []  # Return an empty list if the condition is not met

  @player_upkeep.autocomplete('name')
  async def name_autocomplete(self, interaction: discord.Interaction,
                              current: str) -> List[app_commands.Choice[str]]:
    return await self.player_name_autocomplete(interaction, current)


async def setup(client: commands.Bot) -> None:
  await client.add_cog(MightDistribution(client))
